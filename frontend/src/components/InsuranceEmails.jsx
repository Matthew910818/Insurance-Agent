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

  const fetchInsuranceEmails = async (userId) => {
    setLoading(true)
    setError(null)
    
    try {
      const response = await axios.get(`${API_URL}/emails/insurance`, {
        params: { user_id: userId }
      })
      
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
      // Request draft response for the selected email
      const response = await axios.post(`${API_URL}/emails/draft-response`, {
        email_id: email.id,
        user_id: user.id
      })
      
      setDraftResponse(response.data.draft || null)
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
    <div className="bg-white rounded-lg shadow-md overflow-hidden">
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
              <div className="divide-y divide-gray-200">
                {emails.map((email) => (
                  <div 
                    key={email.id} 
                    className="py-4 cursor-pointer hover:bg-gray-50"
                    onClick={() => handleEmailSelect(email)}
                  >
                    <div className="flex justify-between">
                      <p className="font-medium text-gray-800">{email.sender}</p>
                      <p className="text-sm text-gray-500">{new Date(email.date).toLocaleString()}</p>
                    </div>
                    <p className="text-gray-700 font-medium mt-1">{email.subject}</p>
                    <p className="text-gray-600 mt-1 text-sm line-clamp-2">{email.snippet}</p>
                  </div>
                ))}
              </div>
            )}
            
            <div className="mt-6 flex justify-center">
              <button
                onClick={() => user && fetchInsuranceEmails(user.id)}
                className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                Refresh Emails
              </button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default InsuranceEmails 