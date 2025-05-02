import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const SuccessMessage = ({ user }) => {
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState(null)
  const navigate = useNavigate()
  
  const handleConnectGmail = async () => {
    setIsConnecting(true)
    setError(null)
    
    try {
      // Get the auth URL from the backend
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000'
      const response = await axios.get(`${apiUrl}/api/auth/gmail/url`, {
        params: { 
          user_id: user?.id,
          redirect_uri: window.location.origin + '/auth/callback'
        }
      })
      
      // Redirect to Google's OAuth consent screen
      if (response.data && response.data.authUrl) {
        window.location.href = response.data.authUrl
      } else {
        throw new Error('Authentication URL not provided')
      }
    } catch (err) {
      console.error('Error initiating Gmail auth:', err)
      setError('Failed to connect to Gmail. Please try again.')
      setIsConnecting(false)
    }
  }
  
  const handleViewEmails = () => {
    navigate('/insurance-emails')
  }
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md text-center">
      <div className="flex justify-center mb-4">
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
      </div>
      
      <h2 className="text-xl font-semibold text-gray-800 mb-2">
        Registration Successful!
      </h2>
      
      <p className="text-gray-600 mb-6">
        Your information has been successfully saved in our system.
      </p>
      
      {user && (
        <div className="bg-gray-50 p-4 rounded-md mb-6 text-left">
          <p className="text-sm text-gray-700 mb-1">
            <span className="font-medium">Name:</span> {user.Name}
          </p>
          <p className="text-sm text-gray-700 mb-1">
            <span className="font-medium">Email:</span> {user['Gmail Account']}
          </p>
          <p className="text-sm text-gray-700">
            <span className="font-medium">Phone:</span> {user['Phone Number']}
          </p>
        </div>
      )}
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md text-sm">
          {error}
        </div>
      )}
      
      <div className="space-y-3">
        {!user?.is_gmail_connected ? (
          <button 
            onClick={handleConnectGmail}
            disabled={isConnecting}
            className={`w-full py-2 px-4 rounded-md text-white font-medium ${
              isConnecting ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'
            }`}
          >
            {isConnecting ? 'Connecting...' : 'Connect Gmail Account'}
          </button>
        ) : (
          <button 
            onClick={handleViewEmails}
            className="w-full py-2 px-4 rounded-md text-white font-medium bg-blue-600 hover:bg-blue-700"
          >
            View Insurance Emails
          </button>
        )}
      </div>
      
      <div className="border-t border-gray-200 pt-4 mt-4">
        <p className="text-sm text-gray-500">
          If you need to make changes or have questions, please contact our support team.
        </p>
      </div>
    </div>
  )
}

export default SuccessMessage 