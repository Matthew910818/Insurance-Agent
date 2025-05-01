'use client';

import { useState, useEffect } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import { LoginForm } from '@/components/LoginForm';

export default function LoginPage() {
  const { user, signInWithGoogle, signInWithEmail, signUpWithEmail, isLoading: authLoading } = useAuth();
  const router = useRouter();
  const [error, setError] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (user) {
      router.replace('/profile');
    } else {
      setIsLoading(false);
    }
  }, [user, router]);

  if (authLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-foreground">Loading auth...</div>
      </div>
    );
  }

  const handleGoogleSignIn = async () => {
    try {
      setError('');
      setIsLoading(true);
      await signInWithGoogle();
    } catch (error) {
      console.error('Error in handleGoogleSignIn:', error);
      setError(error instanceof Error ? error.message : 'Google authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleSubmit = async (email: string, password: string, isSignUp: boolean) => {
    setError('');
    setIsLoading(true);

    try {
      if (isSignUp) {
        const { data, error } = await signUpWithEmail(email, password);
        if (error) throw error;
        
        // Check if the user needs to verify their email
        if (data?.user && !data.user.email_confirmed_at) {
          router.replace(`/verify-email?email=${encodeURIComponent(email)}`);
          return;
        }
        
        router.replace('/profile');
      } else {
        await signInWithEmail(email, password);
        router.replace('/profile');
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Authentication failed');
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="text-foreground">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex mt-20 justify-center bg-background px-4">
      <div className="w-full max-w-md">
        <h1 className="text-4xl font-bold text-center mb-8 text-primary dark:text-white flex items-center justify-center">
          <span className="mr-2">🐰</span>
          Find My Bun
        </h1>
        <LoginForm
          onSubmit={handleSubmit}
          onGoogleSignIn={handleGoogleSignIn}
          isLoading={isLoading}
          error={error}
        />
      </div>
    </div>
  );
} 