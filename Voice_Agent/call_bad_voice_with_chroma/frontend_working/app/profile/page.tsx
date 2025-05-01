'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import { useSubscription } from '@/hooks/useSubscription';
import Link from 'next/link';
import { AccountManagement } from '@/components/AccountManagement';
import { ErrorBoundary } from 'react-error-boundary';
import { Suspense } from 'react';
import LoadingSpinner from '@/components/LoadingSpinner';
import { StripeBuyButton } from '@/components/StripeBuyButton';
import { useTrialStatus } from '@/hooks/useTrialStatus';
import { CreditCard, User, Settings, Bell } from 'lucide-react';
import { ThemeToggle } from '@/components/ui/theme-toggle';

function ProfileContent() {
  const { user, signOut } = useAuth();
  const { subscription, isLoading: isLoadingSubscription, syncWithStripe, fetchSubscription } = useSubscription();
  const router = useRouter();
  const searchParams = useSearchParams();
  const paymentStatus = searchParams.get('payment');
  const [isCancelModalOpen, setIsCancelModalOpen] = useState(false);
  const [isCancelling, setIsCancelling] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const { isInTrial, trialEndTime } = useTrialStatus();
  const [activeTab, setActiveTab] = useState('subscription');

  // Show payment success message if redirected from successful payment
  useEffect(() => {
    if (paymentStatus === 'success') {
      // Could add a toast notification here
      console.log('Payment successful!');
    }
  }, [paymentStatus]);

  // Add error handling for subscription sync
  useEffect(() => {
    if (subscription?.stripe_subscription_id) {
      try {
        syncWithStripe(subscription.stripe_subscription_id);
      } catch (err: unknown) {
        console.error('Error syncing with Stripe:', err);
        setError('Unable to load subscription details');
      }
    }
  }, [syncWithStripe, subscription?.stripe_subscription_id]);

  // Add loading timeout with auto-refresh
  useEffect(() => {
    let timeoutId: NodeJS.Timeout;
    let refreshAttempts = 0;
    const MAX_REFRESH_ATTEMPTS = 3;
    const REFRESH_INTERVAL = 3000; // 3 seconds
    
    const attemptRefresh = async () => {
      if (refreshAttempts < MAX_REFRESH_ATTEMPTS) {
        refreshAttempts++;
        await fetchSubscription();
        
        // If still loading, schedule next attempt
        if (isLoadingSubscription) {
          timeoutId = setTimeout(attemptRefresh, REFRESH_INTERVAL);
        }
      } else {
        setError('Loading subscription is taking longer than expected. Please refresh the page.');
      }
    };

    if (isLoadingSubscription) {
      timeoutId = setTimeout(attemptRefresh, REFRESH_INTERVAL);
    }

    return () => {
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isLoadingSubscription, fetchSubscription]);

  // Add useEffect for auth check
  useEffect(() => {
    if (!user) {
      router.push('/login');
    }
  }, [user, router]);

  // Add refresh effect
  useEffect(() => {
    if (user?.id) {
      fetchSubscription();
    }
  }, [user?.id, fetchSubscription]);

  const handleCancelSubscription = async () => {
    if (!subscription?.stripe_subscription_id) return;
    
    setIsCancelling(true);
    try {
      const response = await fetch('/api/stripe/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          subscriptionId: subscription.stripe_subscription_id 
        }),
      });
      
      if (!response.ok) throw new Error('Failed to cancel subscription');
      
      setIsCancelModalOpen(false);
      router.refresh();
    } catch (error) {
      console.error('Error canceling subscription:', error);
    } finally {
      setIsCancelling(false);
    }
  };

  const handleReactivateSubscription = async () => {
    if (!subscription?.stripe_subscription_id) return;
    
    try {
      const response = await fetch('/api/stripe/reactivate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          subscriptionId: subscription.stripe_subscription_id 
        }),
      });
      
      if (!response.ok) throw new Error('Failed to reactivate subscription');
      
      router.refresh();
    } catch (error) {
      console.error('Error reactivating subscription:', error);
    }
  };

  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mb-4 mx-auto"></div>
          <p>Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return (
    <ErrorBoundary
      fallback={
        <div className="p-4 text-red-500">
          Failed to load subscription details. Please try refreshing.
        </div>
      }
    >
      <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-0">
        {/* Header */}
        <header className="bg-white dark:bg-[#0B1120] border-b border-slate-200 dark:border-slate-700 p-6">
          <div className="max-w-7xl mx-auto flex items-center justify-between">
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white flex items-center">
              <span className="mr-2">🐰</span>
              Find My Bun
            </h1>
            <div className="flex items-center space-x-4">
              <ThemeToggle />
              <Link 
                href="/" 
                className="px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-md mr-4 flex items-center"
              >
                <span className="mr-1">👈</span> Go to Main Page
              </Link>
              <span className="text-sm text-slate-600 dark:text-slate-300">
                {user.email}
              </span>
            </div>
          </div>
        </header>

        {/* Main Content */}
        <div className="max-w-7xl mx-auto p-6">
          {paymentStatus === 'success' && (
            <div className="mb-8 p-4 bg-green-50 dark:bg-green-900/30 rounded-lg border border-green-200 dark:border-green-800">
              <p className="text-green-600 dark:text-green-400 flex items-center">
                <span className="mr-2">🎉</span>
                Thank you for your subscription! Your payment was successful.
              </p>
            </div>
          )}
          
          {/* Navigation Tabs */}
          <div className="mb-8 border-b border-slate-200 dark:border-slate-700">
            <nav className="flex space-x-8">
              <button
                onClick={() => setActiveTab('subscription')}
                className={`py-4 px-1 font-medium text-sm border-b-2 ${
                  activeTab === 'subscription'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center">
                  <CreditCard className="w-4 h-4 mr-2" />
                  Subscription
                </div>
              </button>
              <button
                onClick={() => setActiveTab('account')}
                className={`py-4 px-1 font-medium text-sm border-b-2 ${
                  activeTab === 'account'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center">
                  <User className="w-4 h-4 mr-2" />
                  Account
                </div>
              </button>
              <button
                onClick={() => setActiveTab('preferences')}
                className={`py-4 px-1 font-medium text-sm border-b-2 ${
                  activeTab === 'preferences'
                    ? 'border-primary text-primary'
                    : 'border-transparent text-slate-500 hover:text-slate-700 dark:hover:text-slate-300'
                }`}
              >
                <div className="flex items-center">
                  <Settings className="w-4 h-4 mr-2" />
                  Preferences
                </div>
              </button>
            </nav>
          </div>
          
          {/* Tab Content */}
          <div className="space-y-6">
            {activeTab === 'account' && (
              <div className="bg-white dark:bg-[#0B1120] rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                <h2 className="text-xl font-semibold mb-6 text-slate-900 dark:text-white">
                  Account Management
                </h2>
                <AccountManagement />
              </div>
            )}
            
            {activeTab === 'preferences' && (
              <div className="bg-white dark:bg-[#0B1120] rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                <h2 className="text-xl font-semibold mb-6 text-slate-900 dark:text-white">
                  User Preferences
                </h2>
                <p className="text-slate-600 dark:text-slate-400">
                  Preference management features will be coming soon.
                </p>
              </div>
            )}
            
            {activeTab === 'subscription' && (
              <div className="bg-white dark:bg-[#0B1120] rounded-xl shadow-sm border border-slate-200 dark:border-slate-700 p-6">
                <h2 className="text-xl font-semibold mb-6 flex items-center text-slate-900 dark:text-white">
                  <CreditCard className="w-5 h-5 mr-2 text-primary" />
                  Subscription Status
                </h2>
                
                {error ? (
                  <div className="text-red-500 dark:text-red-400 p-4 bg-red-50 dark:bg-red-900/20 rounded-lg">
                    {error}
                  </div>
                ) : isLoadingSubscription ? (
                  <div className="flex items-center space-x-2 p-4 bg-slate-50 dark:bg-slate-700/30 rounded-lg">
                    <div className="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin" />
                    <span className="text-slate-600 dark:text-slate-300">Loading subscription details...</span>
                  </div>
                ) : subscription ? (
                  <div className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                      <div className="bg-slate-50 dark:bg-slate-700/30 p-4 rounded-lg">
                        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Status</p>
                        <p className={`font-medium text-lg ${
                          subscription.status === 'active' 
                            ? 'text-green-500' 
                            : subscription.status === 'trialing'
                              ? 'text-blue-500'
                              : 'text-yellow-500'
                        }`}>
                          {subscription.status.charAt(0).toUpperCase() + subscription.status.slice(1)}
                        </p>
                      </div>
                      
                      <div className="bg-slate-50 dark:bg-slate-700/30 p-4 rounded-lg">
                        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Renewal Date</p>
                        <p className="font-medium text-lg text-slate-900 dark:text-white">
                          {new Date(subscription.current_period_end).toLocaleDateString()}
                        </p>
                      </div>
                      
                      <div className="bg-slate-50 dark:bg-slate-700/30 p-4 rounded-lg">
                        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Start Date</p>
                        <p className="font-medium text-lg text-slate-900 dark:text-white">
                          {new Date(subscription.created_at).toLocaleDateString()}
                        </p>
                      </div>
                      
                      <div className="bg-slate-50 dark:bg-slate-700/30 p-4 rounded-lg">
                        <p className="text-sm text-slate-500 dark:text-slate-400 mb-1">Auto Renewal</p>
                        <p className="font-medium text-lg text-slate-900 dark:text-white">
                          {subscription.cancel_at_period_end ? 'Off' : 'On'}
                        </p>
                      </div>
                    </div>
                    
                    {subscription.status === 'canceled' ? (
                      <div className="mt-6">
                        <Link
                          href="/pay"
                          className="inline-flex items-center justify-center px-6 py-3 bg-primary hover:bg-primary-dark text-white rounded-lg shadow-sm transition-all"
                        >
                          <CreditCard className="w-5 h-5 mr-2" />
                          Resubscribe
                        </Link>
                      </div>
                    ) : subscription.cancel_at_period_end ? (
                      <div className="mt-6 p-4 bg-yellow-50 dark:bg-yellow-900/30 rounded-lg border border-yellow-200 dark:border-yellow-800">
                        <p className="text-yellow-800 dark:text-yellow-200 mb-3">
                          Your subscription will end on {new Date(subscription.current_period_end).toLocaleDateString()}
                        </p>
                        <button
                          onClick={handleReactivateSubscription}
                          className="inline-flex items-center justify-center px-4 py-2 bg-yellow-500 hover:bg-yellow-600 text-white rounded-lg shadow-sm transition-all"
                        >
                          <Bell className="w-4 h-4 mr-2" />
                          Reactivate Subscription
                        </button>
                      </div>
                    ) : (
                      <div className="mt-6 flex flex-wrap gap-4">
                        <button
                          onClick={async () => {
                            try {
                              const response = await fetch('/api/stripe/portal', {
                                method: 'POST',
                                headers: { 'Content-Type': 'application/json' },
                                body: JSON.stringify({ 
                                  customerId: subscription.stripe_customer_id 
                                }),
                              });
                              
                              if (!response.ok) throw new Error('Failed to create portal session');
                              
                              const { url } = await response.json();
                              window.location.href = url;
                            } catch (error) {
                              console.error('Error accessing customer portal:', error);
                              setError('Failed to access subscription management');
                            }
                          }}
                          className="px-4 py-2 bg-primary hover:bg-primary-dark text-white rounded-lg shadow-sm transition-all flex items-center"
                        >
                          <Settings className="w-4 h-4 mr-2" />
                          Manage Subscription
                        </button>
                        <button
                          onClick={() => setIsCancelModalOpen(true)}
                          className="px-4 py-2 bg-red-500 hover:bg-red-600 text-white rounded-lg shadow-sm transition-all flex items-center"
                        >
                          <CreditCard className="w-4 h-4 mr-2" />
                          Cancel Subscription
                        </button>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="space-y-6">
                    {isInTrial ? (
                      <div className="p-4 bg-blue-50 dark:bg-blue-900/30 rounded-lg border border-blue-200 dark:border-blue-800 mb-6">
                        <p className="text-blue-700 dark:text-blue-300 mb-2">
                          <span className="font-medium">Trial Active:</span> You are currently in your 48-hour trial period.
                        </p>
                        <p className="text-blue-700 dark:text-blue-300">
                          Your trial will end on {' '}
                          {trialEndTime ? new Date(trialEndTime).toLocaleDateString() : 'soon'}. Subscribe now to continue using the app after the trial ends.
                        </p>
                      </div>
                    ) : trialEndTime ? (
                      <div className="p-4 bg-red-50 dark:bg-red-900/30 rounded-lg border border-red-200 dark:border-red-800 mb-6">
                        <p className="text-red-700 dark:text-red-300 mb-2">
                          <span className="font-medium">Trial Ended:</span> Your trial period ended on {new Date(trialEndTime).toLocaleDateString()}.
                        </p>
                        <p className="text-red-700 dark:text-red-300">
                          Subscribe now to regain access to all features.
                        </p>
                      </div>
                    ) : (
                      <div className="p-4 bg-primary/5 dark:bg-primary/10 rounded-lg mb-6">
                        <p className="text-slate-700 dark:text-slate-300">
                          Subscribe to unlock all the amazing features of Find My Bun.
                        </p>
                      </div>
                    )}
                    
                    <div className="bg-white dark:bg-[#0B1120] p-6 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm">
                      <h3 className="text-lg font-medium mb-4 text-slate-900 dark:text-white">
                        Subscribe to Find My Bun
                      </h3>
                      <StripeBuyButton
                        buyButtonId={process.env.NEXT_PUBLIC_STRIPE_BUTTON_ID || ''}
                        publishableKey={process.env.NEXT_PUBLIC_STRIPE_PUBLISHABLE_KEY || ''}
                        className="w-full"
                      />
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

        {/* Cancel Confirmation Modal */}
        {isCancelModalOpen && (
          <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
            <div className="bg-white dark:bg-slate-800 rounded-xl p-6 max-w-md w-full shadow-xl border border-slate-200 dark:border-slate-700">
              <h3 className="text-xl font-semibold mb-4 text-slate-900 dark:text-white">Cancel Subscription?</h3>
              <p className="text-slate-600 dark:text-slate-300 mb-6">
                You&apos;ll continue to have access until the end of your billing period on {new Date(subscription?.current_period_end || '').toLocaleDateString()}. No refunds are provided for cancellations.
              </p>
              <div className="flex gap-4 justify-end">
                <button
                  onClick={() => setIsCancelModalOpen(false)}
                  className="px-4 py-2 text-slate-600 dark:text-slate-300 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                  disabled={isCancelling}
                >
                  Keep Subscription
                </button>
                <button
                  onClick={handleCancelSubscription}
                  className="bg-red-500 hover:bg-red-600 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                  disabled={isCancelling}
                >
                  {isCancelling ? (
                    <>
                      <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                      Canceling...
                    </>
                  ) : (
                    'Yes, Cancel'
                  )}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
};


export default function ProfilePage() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <ProfileContent />
    </Suspense>
  );
}
