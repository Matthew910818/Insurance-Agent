import { useState } from 'react'
import { useForm } from 'react-hook-form'
import axios from 'axios'

// Get API URL from environment variables or use default for local development
// Ensure the API_URL always ends with /api
const BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_URL = BASE_URL.endsWith('/api') ? BASE_URL : `${BASE_URL}/api`;

const UserForm = ({ onSuccess }) => {
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)
  
  const { 
    register, 
    handleSubmit, 
    formState: { errors } 
  } = useForm()
  
  const onSubmit = async (data) => {
    setIsLoading(true)
    setError(null)
    
    try {
      // Send data to backend API
      const response = await axios.post(`${API_URL}/users`, {
        Name: data.name,
        Gmail_Account: data.email,
        Phone_Number: data.phone
      })
      
      if (response.status === 201) {
        // User created successfully, call the onSuccess callback
        onSuccess(response.data.user);
      } else {
        throw new Error('Unexpected response from server')
      }
    } catch (err) {
      console.error('Error submitting form:', err)
      if (err.response && err.response.data && err.response.data.errors) {
        // Format validation errors from the server
        const serverErrors = err.response.data.errors.map(e => e.msg).join(', ')
        setError(`Validation error: ${serverErrors}`)
      } else if (err.response && err.response.data && err.response.data.error) {
        // Server error with message
        setError(err.response.data.error)
      } else {
        // Generic error
        setError('There was an error saving your information. Please try again.')
      }
    } finally {
      setIsLoading(false)
    }
  }
  
  return (
    <div className="bg-white p-6 rounded-lg shadow-md">
      <h2 className="text-xl font-semibold mb-4">Your Information</h2>
      
      {error && (
        <div className="mb-4 p-3 bg-red-100 text-red-700 rounded-md">
          {error}
        </div>
      )}
      
      <form onSubmit={handleSubmit(onSubmit)}>
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-1" htmlFor="name">
            Full Name
          </label>
          <input
            id="name"
            type="text"
            className={`w-full p-2 border rounded-md ${errors.name ? 'border-red-500' : 'border-gray-300'}`}
            {...register('name', { required: 'Name is required' })}
          />
          {errors.name && (
            <p className="mt-1 text-sm text-red-600">{errors.name.message}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-1" htmlFor="email">
            Email Address
          </label>
          <input
            id="email"
            type="email"
            className={`w-full p-2 border rounded-md ${errors.email ? 'border-red-500' : 'border-gray-300'}`}
            {...register('email', { 
              required: 'Email is required',
              pattern: {
                value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/,
                message: 'Please enter a valid email address'
              }
            })}
          />
          {errors.email && (
            <p className="mt-1 text-sm text-red-600">{errors.email.message}</p>
          )}
        </div>
        
        <div className="mb-4">
          <label className="block text-gray-700 text-sm font-medium mb-1" htmlFor="phone">
            Phone Number
          </label>
          <input
            id="phone"
            type="tel"
            className={`w-full p-2 border rounded-md ${errors.phone ? 'border-red-500' : 'border-gray-300'}`}
            {...register('phone', { 
              required: 'Phone number is required',
              pattern: {
                value: /^[+]?[(]?[0-9]{3}[)]?[-\s.]?[0-9]{3}[-\s.]?[0-9]{4,6}$/,
                message: 'Please enter a valid phone number'
              }
            })}
          />
          {errors.phone && (
            <p className="mt-1 text-sm text-red-600">{errors.phone.message}</p>
          )}
        </div>
        
        <button
          type="submit"
          disabled={isLoading}
          className={`w-full py-2 px-4 rounded-md text-white font-medium 
            ${isLoading ? 'bg-blue-400' : 'bg-blue-600 hover:bg-blue-700'}`}
        >
          {isLoading ? 'Processing...' : 'Submit'}
        </button>
      </form>
    </div>
  )
}

export default UserForm 