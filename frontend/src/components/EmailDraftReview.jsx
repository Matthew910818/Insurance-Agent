import { useState } from 'react'

const EmailDraftReview = ({ email, draft, onSend, onEdit, onCancel }) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedDraft, setEditedDraft] = useState(draft)
  
  const handleEditClick = () => {
    setIsEditing(true)
  }
  
  const handleSaveEdit = () => {
    onEdit(editedDraft)
    setIsEditing(false)
  }
  
  const handleCancelEdit = () => {
    setEditedDraft(draft)
    setIsEditing(false)
  }
  
  return (
    <div className="bg-white rounded-lg border border-gray-200">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-lg font-semibold text-gray-800">Review Draft Response</h3>
      </div>
      
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="mb-3">
          <span className="font-medium text-gray-700">To:</span> {email.sender}
        </div>
        <div className="mb-3">
          <span className="font-medium text-gray-700">Subject:</span> Re: {email.subject}
        </div>
      </div>
      
      <div className="p-4">
        <div className="mb-4">
          <h4 className="font-medium text-gray-700 mb-2">Original Email:</h4>
          <div className="bg-gray-50 p-3 rounded-md text-gray-600 text-sm max-h-40 overflow-y-auto">
            {email.body || email.snippet}
          </div>
        </div>
        
        <div>
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-medium text-gray-700">Draft Response:</h4>
            {!isEditing && (
              <button 
                onClick={handleEditClick}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Edit Draft
              </button>
            )}
          </div>
          
          {isEditing ? (
            <>
              <textarea
                value={editedDraft}
                onChange={(e) => setEditedDraft(e.target.value)}
                className="w-full p-3 border border-gray-300 rounded-md h-64 text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
              />
              
              <div className="flex justify-end space-x-3 mt-3">
                <button
                  onClick={handleCancelEdit}
                  className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-50"
                >
                  Cancel
                </button>
                <button
                  onClick={handleSaveEdit}
                  className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700"
                >
                  Save Changes
                </button>
              </div>
            </>
          ) : (
            <div className="bg-white border border-gray-200 p-3 rounded-md text-gray-700 whitespace-pre-wrap min-h-64">
              {draft}
            </div>
          )}
        </div>
      </div>
      
      <div className="p-4 bg-gray-50 border-t border-gray-200 flex justify-between">
        <button
          onClick={onCancel}
          className="px-4 py-2 border border-gray-300 rounded-md text-gray-700 hover:bg-gray-100"
        >
          Back to Emails
        </button>
        
        <button
          onClick={onSend}
          className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          Send Response
        </button>
      </div>
    </div>
  )
}

export default EmailDraftReview 