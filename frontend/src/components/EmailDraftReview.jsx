import { useState, useEffect } from 'react'

const EmailDraftReview = ({ email, draft, onSend, onEdit, onCancel }) => {
  const [isEditing, setIsEditing] = useState(false)
  const [editedDraft, setEditedDraft] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  
  // Update editedDraft when draft prop changes
  useEffect(() => {
    // Ensure draft is a string
    const draftText = typeof draft === 'string' ? draft : 
                     draft && typeof draft === 'object' && draft.body ? draft.body :
                     JSON.stringify(draft);
    setEditedDraft(draftText || '')
    setIsLoading(false)
  }, [draft])
  
  const handleEditClick = () => {
    setIsEditing(true)
  }
  
  const handleSaveEdit = () => {
    onEdit(editedDraft)
    setIsEditing(false)
  }
  
  const handleCancelEdit = () => {
    // Ensure draft is a string
    const draftText = typeof draft === 'string' ? draft : 
                     draft && typeof draft === 'object' && draft.body ? draft.body :
                     JSON.stringify(draft);
    setEditedDraft(draftText || '')
    setIsEditing(false)
  }
  
  // Function to display the draft appropriately
  const displayDraft = () => {
    if (!draft) {
      return 'Loading draft response...';
    }
    
    if (typeof draft === 'string') {
      return draft;
    }
    
    if (draft && typeof draft === 'object') {
      if (draft.body) return draft.body;
      return JSON.stringify(draft, null, 2);
    }
    
    return 'Unable to display draft response';
  }
  
  return (
    <div className="bg-white rounded-lg border border-gray-200 w-full">
      <div className="p-4 border-b border-gray-200">
        <h3 className="text-xl font-semibold text-gray-800">Review Draft Response</h3>
      </div>
      
      <div className="p-4 bg-gray-50 border-b border-gray-200">
        <div className="mb-3">
          <span className="font-medium text-gray-700">To:</span> {email.sender}
        </div>
        <div className="mb-3">
          <span className="font-medium text-gray-700">Subject:</span> Re: {email.subject}
        </div>
      </div>
      
      <div className="p-6">
        <div className="mb-6">
          <h4 className="font-medium text-gray-700 mb-2">Original Email:</h4>
          <div className="bg-gray-50 p-4 rounded-md text-gray-600 max-h-48 overflow-y-auto border border-gray-200">
            <pre className="whitespace-pre-wrap font-sans text-sm">
              {email.body || email.snippet}
            </pre>
          </div>
        </div>
        
        <div>
          <div className="flex justify-between items-center mb-2">
            <h4 className="font-medium text-gray-700">Draft Response:</h4>
            {!isEditing && !isLoading && (
              <button 
                onClick={handleEditClick}
                className="px-3 py-1 text-sm text-blue-600 hover:text-blue-800 border border-blue-200 rounded-md hover:bg-blue-50"
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
                className="w-full p-4 border border-gray-300 rounded-md h-64 text-gray-700 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 font-sans"
              />
              
              <div className="flex justify-end space-x-3 mt-4">
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
            <div className="bg-white border border-gray-200 p-4 rounded-md text-gray-700 min-h-48">
              <pre className="whitespace-pre-wrap font-sans">
                {displayDraft()}
              </pre>
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
          className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500"
          disabled={isLoading}
        >
          Send Response
        </button>
      </div>
    </div>
  )
}

export default EmailDraftReview 