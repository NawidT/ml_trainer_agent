import { useState } from 'react'
import PythonMessage from './comps/python_message'
import TextMessage from './comps/text_message'
import CLIOutMessage from './comps/cliout_message'



function App() {
  // state to manage the chat history
  const [chatHistory, setChatHistory] = useState([
    {
      role: 'ai',
      type: 'cli',
      content: 'Hello! I am the ML Trainer Agent. How can I help you today?'
    }])
  const [curUserTestm, setCurUserTestm] = useState('')

  const handleUserMessageSubmit = (e) => {
    e.preventDefault();
    const message = curUserTestm
    if (message.trim() === '') {
      return;
    }
    setChatHistory([...chatHistory, { role: 'user', content: message, type: 'text' }]);
    console.log(chatHistory);
    setCurUserTestm("")
  }

  return (
    <>
      <div className="flex flex-col h-screen w-screen">
        <div className="flex-1 overflow-y-auto w-full flex flex-col items-center my-2 space-y-4 px-4">
          <div className="flex flex-col w-full p-4 items-center rounded-lg shadow-lg">
            {chatHistory.length > 0 && chatHistory.map((message, index) => (
              <div key={index} className={`flex w-5/10 min-h-[60px] justify-center align-center rounded-lg border-blue-500 border-2 mb-3 ${message.role === 'ai' ? 'bg-pink-800' : 'bg-purple-500' }`}>
              {
              message.type === 'text' ? 
                <TextMessage message={message.content}/> : 
                message.type === 'cli' ? 
                  <CLIOutMessage output={message.content}/> : 
                  <PythonMessage code={message.content} isRunning={false}/>
              }
              </div>
            ))}
            {chatHistory.length === 0 && (
              <div className="flex flex-col justify-center items-center">
                  No messages yet
              </div>
            )}
          </div>
        </div>
        
        {/* place the form in the bottom of the chat container */}
        <div className="flex flex-col justify-end h-1/20 w-full mb-3">
          <form className="flex flex-row align-center justify-center w-full h-full space-x-2" onSubmit={handleUserMessageSubmit}>
            <input
              type="text"
              placeholder="Type your message here..."
              className="w-1/2 px-2 rounded-lg border-2 border-blue-200"
              value={curUserTestm}
              onChange={(e) => setCurUserTestm(e.target.value)}
            />
            <button className="bg-blue-500 text-white px-4 py-2 rounded-lg" type="submit">
              Send
            </button>
          </form>
        </div>
      </div>
    </>
  )
}

export default App
