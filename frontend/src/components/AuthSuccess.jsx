import { useEffect, useState } from 'react';
import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`;

const AuthSuccess = () => {
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState('Finalizing Gmail authentication...');
  const [error, setError] = useState(null);

  useEffect(() => {
    const userId = localStorage.getItem('userId');
    
    if (!userId) {
      setStatus('error');
      setError('User ID not found. Please try again.');
      return;
    }

    // Run the Gmail agent for the user
    const runAgent = async () => {
      try {
        const response = await axios.post(`${API_URL}/run-agent/${userId}`);
        
        if (response.status === 200) {
          setStatus('success');
          setMessage('Your Gmail account has been successfully connected and the agent is now running!');
        } else {
          throw new Error('Unexpected response from server');
        }
      } catch (err) {
        console.error('Error running Gmail agent:', err);
        setStatus('error');
        setError(err.response?.data?.details || 'Failed to run Gmail agent. Please try again.');
      }
    };

    // Wait a moment before running the agent to ensure tokens are saved
    const timeout = setTimeout(() => {
      runAgent();
    }, 2000);

    return () => clearTimeout(timeout);
  }, []);

  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="bg-white p-8 rounded-lg shadow-md max-w-md w-full">
        {status === 'loading' && (
          <div className="text-center">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
            <h2 className="text-xl font-semibold mb-2">Connecting to Gmail</h2>
            <p className="text-gray-600">{message}</p>
          </div>
        )}

        {status === 'success' && (
          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-8 w-8 text-green-600" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M5 13l4 4L19 7" 
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Gmail Connected!</h2>
            <p className="text-gray-600 mb-6">{message}</p>
            <a 
              href="/" 
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors"
            >
              Return to Homepage
            </a>
          </div>
        )}

        {status === 'error' && (
          <div className="text-center">
            <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center mx-auto mb-4">
              <svg 
                xmlns="http://www.w3.org/2000/svg" 
                className="h-8 w-8 text-red-600" 
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path 
                  strokeLinecap="round" 
                  strokeLinejoin="round" 
                  strokeWidth={2} 
                  d="M6 18L18 6M6 6l12 12" 
                />
              </svg>
            </div>
            <h2 className="text-xl font-semibold mb-2">Connection Failed</h2>
            <p className="text-red-600 mb-6">{error}</p>
            <a 
              href="/" 
              className="inline-block bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded transition-colors"
            >
              Try Again
            </a>
          </div>
        )}
      </div>
    </div>
  );
};

export default AuthSuccess; 