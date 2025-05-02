import { useEffect, useState } from 'react'
import { useNavigate, useLocation } from 'react-router-dom'
import axios from 'axios'

const AuthCallback = () => {
  const [status, setStatus] = useState('processing')
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  const location = useLocation()
  
  useEffect(() => {
    const handleCallback = async () => {
      try {
        // Get the authorization code from the URL
        const queryParams = new URLSearchParams(location.search)
        const code = queryParams.get('code')
        const state = queryParams.get('state')
        
        if (!code) {
          const errorMsg = queryParams.get('error') || 'Authorization code not provided'
          setError(errorMsg)
          setStatus('error')
          return
        }
        
        // Send the code to the backend to exchange for tokens
        const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
        const response = await axios.post(`${apiUrl}/api/auth/gmail/callback`, {
          code,
          state,
          redirect_uri: window.location.origin + '/auth/callback'
        })
        
        if (response.data.success) {
          setStatus('success')
          
          // Decode state to get user ID
          try {
            const stateData = JSON.parse(Buffer.from(state, 'base64').toString())
            const { user_id } = stateData
            
            if (user_id) {
              // Get user data from supabase
              const userResponse = await axios.get(`${apiUrl}/api/users/${user_id}`)
              if (userResponse.data.user) {
                // Save user data to localStorage
                localStorage.setItem('userData', JSON.stringify(userResponse.data.user))
              }
            }
          } catch (err) {
            console.error('Error parsing state or fetching user data:', err)
            // Continue anyway as the authentication was successful
          }
          
          // Wait a moment then redirect to the insurance emails page
          setTimeout(() => {
            navigate('/insurance-emails')
          }, 2000)
        } else {
          throw new Error(response.data.error || 'Failed to complete authentication')
        }
      } catch (err) {
        console.error('Error in auth callback:', err)
        setError(err.message || 'Authentication failed')
        setStatus('error')
      }
    }
    
    handleCallback()
  }, [location, navigate])
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md text-center">
      <div className="flex justify-center mb-4">
        {status === 'processing' && (
          <div className="h-16 w-16 rounded-full bg-blue-100 flex items-center justify-center">
            <div className="animate-spin rounded-full h-8 w-8 border-t-2 border-b-2 border-blue-600"></div>
          </div>
        )}
        
        {status === 'success' && (
          <div className="h-16 w-16 rounded-full bg-green-100 flex items-center justify-center">
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
        )}
        
        {status === 'error' && (
          <div className="h-16 w-16 rounded-full bg-red-100 flex items-center justify-center">
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
        )}
      </div>
      
      <h2 className="text-xl font-semibold text-gray-800 mb-2">
        {status === 'processing' && 'Connecting Gmail Account...'}
        {status === 'success' && 'Gmail Connected Successfully!'}
        {status === 'error' && 'Connection Failed'}
      </h2>
      
      <p className="text-gray-600 mb-6">
        {status === 'processing' && 'Please wait while we complete the authentication process.'}
        {status === 'success' && 'Your Gmail account has been successfully connected. You will be redirected shortly.'}
        {status === 'error' && (error || 'There was an error connecting your Gmail account. Please try again.')}
      </p>
      
      {status === 'error' && (
        <button 
          onClick={() => navigate('/')}
          className="py-2 px-4 rounded-md text-white font-medium bg-blue-600 hover:bg-blue-700"
        >
          Go Back
        </button>
      )}
    </div>
  )
}

export default AuthCallback 