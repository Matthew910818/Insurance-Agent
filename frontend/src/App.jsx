import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import UserForm from './components/UserForm'
import SuccessMessage from './components/SuccessMessage'
import InsuranceEmails from './components/InsuranceEmails'
import AuthCallback from './components/AuthCallback'
import Navigation from './components/Navigation'

function App() {
  const [formSubmitted, setFormSubmitted] = useState(false)
  const [userData, setUserData] = useState(null)
  
  const handleFormSuccess = (user) => {
    setUserData(user)
    setFormSubmitted(true)
  }
  
  return (
    <Router>
      <div className="min-h-screen bg-gray-100">
        <Navigation />
        
        <div className="flex items-center justify-center p-4">
          <div className="w-full max-w-md">
            <Routes>
              <Route path="/" element={
                <>
                  <header className="text-center mb-8">
                    <h1 className="text-3xl font-bold text-gray-800">User Registration</h1>
                    <p className="text-gray-600 mt-2">Register your information with our service</p>
                  </header>
                  
                  {formSubmitted ? (
                    <SuccessMessage user={userData} />
                  ) : (
                    <UserForm onSuccess={handleFormSuccess} />
                  )}
                </>
              } />
              
              <Route path="/insurance-emails" element={<InsuranceEmails />} />
              <Route path="/auth/callback" element={<AuthCallback />} />
            </Routes>
          </div>
        </div>
      </div>
    </Router>
  )
}

export default App 