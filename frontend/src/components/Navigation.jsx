import { Link } from 'react-router-dom'

const Navigation = () => {
  return (
    <nav className="bg-white shadow-md">
      <div className="max-w-6xl mx-auto px-4">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <span className="font-semibold text-lg text-blue-600">Insurance Assistant</span>
          </div>
          
          <div className="flex items-center space-x-4">
            <Link 
              to="/" 
              className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-100"
            >
              Home
            </Link>
            <Link 
              to="/insurance-emails" 
              className="px-3 py-2 rounded-md text-sm font-medium text-gray-700 hover:text-blue-600 hover:bg-gray-100"
            >
              Insurance Emails
            </Link>
          </div>
        </div>
      </div>
    </nav>
  )
}

export default Navigation 