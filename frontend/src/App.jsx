import { useState, useEffect } from 'react'
import UserForm from './components/UserForm'
import SuccessMessage from './components/SuccessMessage'

function App() {
  const [formSubmitted, setFormSubmitted] = useState(false)
  const [userData, setUserData] = useState(null)
  
  const handleFormSuccess = (user) => {
    setUserData(user)
    setFormSubmitted(true)
  }
  
  return (
    <div className="min-h-screen bg-gray-100 flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-gray-800">User Registration</h1>
          <p className="text-gray-600 mt-2">Register your information with our service</p>
        </header>
        
        {formSubmitted ? (
          <SuccessMessage user={userData} />
        ) : (
          <UserForm onSuccess={handleFormSuccess} />
        )}
      </div>
    </div>
  )
}

export default App 