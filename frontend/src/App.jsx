import { useState, useEffect } from 'react'
import UserForm from './components/UserForm'
import SuccessMessage from './components/SuccessMessage'
import AuthSuccess from './components/AuthSuccess'

function App() {
  const [formSubmitted, setFormSubmitted] = useState(false)
  const [currentPage, setCurrentPage] = useState('home')
  
  useEffect(() => {
    // Check if we're on the auth success page
    if (window.location.pathname === '/auth-success') {
      setCurrentPage('auth-success')
    }
  }, [])
  
  // Render the appropriate page based on the current path
  const renderPage = () => {
    switch (currentPage) {
      case 'auth-success':
        return <AuthSuccess />
      default:
        return (
          <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
            <div className="w-full max-w-md">
              <header className="text-center mb-8">
                <h1 className="text-3xl font-bold text-gray-800">Gmail Agent</h1>
                <p className="text-gray-600 mt-2">Connect your Gmail account for automated assistance</p>
              </header>
              
              {formSubmitted ? (
                <SuccessMessage />
              ) : (
                <UserForm onSuccess={() => setFormSubmitted(true)} />
              )}
            </div>
          </div>
        )
    }
  }
  
  return renderPage()
}

export default App 