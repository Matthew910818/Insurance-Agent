import { useState, useEffect } from 'react'
import axios from 'axios'
import EmailDraftReview from './EmailDraftReview'
import { useNavigate } from 'react-router-dom'

// Get API URL from environment variables or use default for local development
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`;

const InsuranceEmails = () => {
  const [loading, setLoading] = useState(true)
  const [emails, setEmails] = useState([])
  const [error, setError] = useState(null)
  const [selectedEmail, setSelectedEmail] = useState(null)
  const [draftResponse, setDraftResponse] = useState(null)
  const [showDraftReview, setShowDraftReview] = useState(false)
  const [user, setUser] = useState(null)
  const navigate = useNavigate()

  useEffect(() => {
    // Get user data from localStorage if available
    const storedUser = localStorage.getItem('userData')
    if (storedUser) {
      try {
        const userData = JSON.parse(storedUser)
        setUser(userData)
        fetchInsuranceEmails(userData.id)
      } catch (err) {
        console.error('Error parsing user data:', err)
        setError('Unable to retrieve user information. Please sign in again.')
      }
    } else {
      setError('Please sign in to view your emails')
      setLoading(false)
    }
  }, [])

  // Add a debug function to check user data
  const debugUserData = () => {
    console.log('Current user state:', user);
    console.log('LocalStorage userData:', localStorage.getItem('userData'));
    try {
      const userData = JSON.parse(localStorage.getItem('userData'));
      console.log('Parsed user data:', userData);
      if (userData && userData.id) {
        fetchInsuranceEmails(userData.id);
      }
    } catch (err) {
      console.error('Error parsing stored user data:', err);
    }
  }

  const fetchInsuranceEmails = async (userId) => {
    setLoading(true)
    setError(null)
    
    try {
      console.log('Fetching emails for user ID:', userId);
      const response = await axios.get(`${API_URL}/emails/insurance`, {
        params: { user_id: userId }
      })
      
      console.log('Email response:', response.data);
      setEmails(response.data.emails || [])
    } catch (err) {
      console.error('Error fetching insurance emails:', err)
      
      // Handle specific error cases
      if (err.response && err.response.data.needsConnection) {
        setError('Your Gmail account is not connected. Please go back and connect your account.')
      } else {
        setError('Failed to load insurance emails. Please try again later.')
      }
    } finally {
      setLoading(false)
    }
  }

  const handleEmailSelect = async (email) => {
    if (!user || !user.id) {
      setError('User information not available. Please sign in again.')
      return
    }
    
    setSelectedEmail(email)
    setDraftResponse(null)
    
    try {
      console.log('Requesting draft response for email:', email.id);
      // Request draft response for the selected email
      const response = await axios.post(`${API_URL}/emails/draft-response`, {
        email_id: email.id,
        user_id: user.id
      })
      
      console.log('Draft response received:', response.data);
      
      // Check different possible formats the draft might be returned in
      let draft = null;
      if (typeof response.data.draft === 'string') {
        draft = response.data.draft;
      } else if (response.data.draft && response.data.draft.body) {
        draft = response.data.draft.body;
      } else if (response.data.draft && response.data.draft.draft) {
        draft = response.data.draft.draft;
      } else {
        console.warn('Could not extract draft from response:', response.data);
        draft = 'Unable to generate a response. Please try again later.';
      }
      
      setDraftResponse(draft)
      setShowDraftReview(true)
    } catch (err) {
      console.error('Error generating draft response:', err)
      setError('Failed to generate a response. Please try again.')
    }
  }

  const handleSendResponse = async () => {
    if (!selectedEmail || !draftResponse || !user || !user.id) return
    
    try {
      await axios.post(`${API_URL}/emails/send-response`, {
        email_id: selectedEmail.id,
        thread_id: selectedEmail.threadId,
        response: draftResponse,
        user_id: user.id
      })
      
      // Reset state after sending
      setShowDraftReview(false)
      setSelectedEmail(null)
      setDraftResponse(null)
      
      // Refresh emails list
      fetchInsuranceEmails(user.id)
    } catch (err) {
      console.error('Error sending email response:', err)
      setError('Failed to send the response. Please try again.')
    }
  }

  const handleEditDraft = (updatedDraft) => {
    setDraftResponse(updatedDraft)
  }

  const handleConnectGmail = () => {
    navigate('/')
  }

  if (loading) {
    return (
      <div className="text-center py-10">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-blue-600 mx-auto"></div>
        <p className="mt-4 text-gray-600">Loading insurance emails...</p>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden w-full">
      <div className="p-6">
        <h2 className="text-2xl font-semibold text-gray-800 mb-4">Insurance Emails</h2>
        
        {error && (
          <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
            {error}
            {error.includes('not connected') && (
              <button
                onClick={handleConnectGmail}
                className="ml-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700"
              >
                Connect Gmail
              </button>
            )}
          </div>
        )}
        
        {showDraftReview && selectedEmail && draftResponse ? (
          <EmailDraftReview 
            email={selectedEmail}
            draft={draftResponse}
            onSend={handleSendResponse}
            onEdit={handleEditDraft}
            onCancel={() => setShowDraftReview(false)}
          />
        ) : (
          <>
            {emails.length === 0 ? (
              <div className="text-center py-8">
                <p className="text-gray-500">No insurance emails found.</p>
              </div>
            ) : (
              <div className="divide-y divide-gray-200 border border-gray-200 rounded-lg overflow-hidden">
                {emails.map((email) => (
                  <div 
                    key={email.id} 
                    className="p-4 cursor-pointer hover:bg-gray-50 transition-colors"
                    onClick={() => handleEmailSelect(email)}
                  >
                    <div className="flex flex-wrap justify-between items-center mb-2">
                      <p className="font-medium text-gray-800 mr-4">{email.sender}</p>
                      <p className="text-sm text-gray-500">{new Date(email.date).toLocaleString()}</p>
                    </div>
                    <p className="text-gray-800 font-medium mb-2">{email.subject}</p>
                    <p className="text-gray-600 text-sm line-clamp-2">{email.snippet}</p>
                  </div>
                ))}
              </div>
            )}
            
            <div className="mt-6 flex justify-center space-x-4">
              <button
                onClick={() => user && fetchInsuranceEmails(user.id)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Refresh Emails
              </button>
              <button
                onClick={debugUserData}
                className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-gray-500"
              >
                Debug User Data
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default InsuranceEmails 