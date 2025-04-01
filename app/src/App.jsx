import { useState } from 'react'
import './App.css'

function App() {
  

  // state to manage the chat history
  const [chatHistory, setChatHistory] = useState([])
  const [curUserTestm, setCurUserTestm] = useState('')

  const handleUserMessageSubmit = (e) => {
    e.preventDefault();
    const message = curUserTestm
    setChatHistory([...chatHistory, { role: 'user', content: message }]);
    console.log(chatHistory);
    setCurUserTestm("")
  }

  return (
    <>
      <div className="flex flex-col h-screen w-screen">
        <div className="flex-grow overflow-y-auto border-2 w-full h-4/5 flex flex-col w-8/10">
            {chatHistory.map((message, index) => (
              <div key={index} className={`p-4 m-4 w-full h-1/10 justify-center align-center rounded-lg shadow-lg ${
                message.role === 'user' 
                  ? 'bg-gradient-to-r from-blue-500 to-purple-500 border-blue-300' 
                  : 'bg-gradient-to-r from-gray-700 to-slate-800 border-gray-500'
              }`}>
                <div className={`text-white break-words text-center justify-center align-center font-medium ${
                  message.role === 'user'
                    ? 'drop-shadow-md'
                    : ''
                }`}>
                  { message.role === 'user' ? "User: " : "AI: "}
                  {message.content}
                </div>
              </div>
            ))}
        </div>
        
        {/* place the form in the bottom of the chat container */}
        <div className="flex flex-col justify-end h-1/10 w-full m-2">
          <form className="flex flex-row align-center justify-center w-full h-full space-x-2" onSubmit={handleUserMessageSubmit}>
            <input
              type="text"
              placeholder="Type your message here..."
              className="w-1/2 rounded-lg"
              value={curUserTestm}
              onChange={(e) => setCurUserTestm(e.target.value)}
            />
            <button type="submit" className="send-button">
              Send
            </button>
          </form>
        </div>
      </div>
    </>
  )
}

export default App
