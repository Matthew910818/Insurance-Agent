const SuccessMessage = () => {
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
        Successfully Connected!
      </h2>
      
      <p className="text-gray-600 mb-6">
        Your Gmail account has been connected to our service. You'll receive updates via email and SMS.
      </p>
      
      <div className="border-t border-gray-200 pt-4">
        <p className="text-sm text-gray-500">
          If you need to make changes or have questions, please contact our support team.
        </p>
      </div>
    </div>
  )
}

export default SuccessMessage 