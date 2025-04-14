import { useState, useEffect, useRef } from 'react'
import BaseAgentColumn from './comps/BaseAgentColumn'

function App() {
  // state to manage the chat history for each agent
  const [managerChat, setManagerChat] = useState([])
  const [kaggleChat, setKaggleChat] = useState([])
  const [pythonChat, setPythonChat] = useState([])
  const [curUserMessage, setCurUserMessage] = useState('')
  const [loadingScreen, setLoadingScreen] = useState(true)
  const [wsConnected, setWsConnected] = useState(false)
  
  // Create a ref to store the WebSocket instance
  const ws = useRef(null)

  useEffect(() => {
    // Initialize WebSocket connection
    ws.current = new WebSocket('ws://localhost:8000/ws')

    // WebSocket event handlers
    ws.current.onopen = () => {
      console.log('WebSocket Connected')
      setWsConnected(true)
    }

    ws.current.onmessage = (event) => {
      let data = JSON.parse(event.data)
      console.log(typeof data)
      // Handle different types of messages based on the agent
      switch(data["agent"]) {
        case 'manager_agent':
          setManagerChat(prev => [...prev, { role: 'manager_agent', type: data["type"], content: data["message"] }])
          break
        case 'kaggle_agent':
          setKaggleChat(prev => [...prev, { role: 'kaggle_agent', type: data["type"], content: data["message"] }])
          break
        case 'python_agent':
          setPythonChat(prev => [...prev, { role: 'python_agent', type: data["type"], content: data["message"] }])
          break
        default:
          console.log('Unknown agent type:', data)
      }
    }

    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error)
      setWsConnected(false)
    }

    ws.current.onclose = () => {
      console.log('WebSocket Disconnected')
      setWsConnected(false)
    }

    // Cleanup on component unmount
    return () => {
      if (ws.current) {
        ws.current.close()
      }
    }
  }, [])

  
  const InitialScreen = () => {
    const handleChangingLoadingScreen = () => {
      setLoadingScreen(false)
      // wait 2 seconds before appending manager init message
      setTimeout(() => {
        setManagerChat([...managerChat, { role: 'manager_agent', type: 'text', content: 'Hello! I am the Manager Agent. How can I help you today?' }])
      }, 1500)
    }
    return (
      <div className="flex flex-col h-screen w-screen">
        <div className="flex flex-row w-full h-[90%]">
          <div className="flex flex-col w-full h-full justify-center space-y-10 items-center">
            <h1 className="text-4xl font-bold">Welcome to the Multi Agent ML Checking</h1>
            <p className="text-lg">We can quickly grab data from kaggle check feasibility of an ML project</p>
            <button 
              className="bg-blue-400 text-white px-6 py-2 rounded-lg hover:bg-blue-800 animate-bounce" 
              onClick={handleChangingLoadingScreen}
            >Start</button>
          </div>
        </div>
      </div>
    )
  }

  const NavBar = () => {
    // have the navbar display whether the connection is stable or not
    return (
      <div className="flex flex-row w-full h-10 bg-blue-600">
        <div className="flex flex-row w-full h-full justify-start items-center px-4">
          <p className="text-sm text-white">Connection: {wsConnected ? 'Connected' : 'Disconnected'}</p>
        </div>
      </div>
    )
  }

  const handleUserMessageSubmit = (e) => {
    e.preventDefault();
    const message = curUserMessage
    if (message.trim() === '') {
      return;
    }
    
    // Send message to WebSocket server
    if (ws.current && wsConnected) {
      ws.current.send(JSON.stringify({
        agent: 'manager',
        query: message
      }))
    }
    
    setManagerChat([...managerChat, { role: 'user', content: message, type: 'text' }]);
    setCurUserMessage("")
  }

  return (
    <>
    {!loadingScreen ? <div className="flex flex-col h-screen w-screen">
      <NavBar />
      <div className="flex flex-row w-full h-[90%]">
        <BaseAgentColumn title="Manager Agent" messages={managerChat} />
        <BaseAgentColumn title="Kaggle Agent" messages={kaggleChat} />
        <BaseAgentColumn title="Python Agent" messages={pythonChat} />
      </div>
      
      {/* Unified input box at the bottom */}
      <div className="flex flex-col justify-end h-20 w-full p-4 bg-gray-100">
        <form className="flex flex-row align-center justify-center w-full h-full space-x-2" onSubmit={handleUserMessageSubmit}>
          <input
            type="text"
            placeholder="Type your message here..."
            className="w-1/2 px-4 py-2 rounded-lg border-2 border-blue-200 focus:outline-none focus:border-blue-500"
            value={curUserMessage}
            onChange={(e) => setCurUserMessage(e.target.value)}
          />
          <button 
            className="bg-blue-500 text-white px-6 py-2 rounded-lg hover:bg-blue-600 transition-colors" 
            type="submit"
          >
            Send
          </button>
        </form>
      </div>
    </div> : <InitialScreen />}
    </>
  )
}

export default App
