import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from main import ManagerAgent
import json
import asyncio
import uuid
app = FastAPI()

# Store active connections. Acts as connection pooling
class ConnectionManager:
    def __init__(self):
        self.session_states: Dict[str, (WebSocket, ManagerAgent)] = {}

    async def connect(self, session_id: str, websocket: WebSocket):
        await websocket.accept()
        # Initialize session state if it doesn't exist
        if session_id not in self.session_states.keys():
            self.session_states[session_id] = (websocket, ManagerAgent(
                websocket_send_message=self.send_message,
                session_id=session_id
            ))
        
    def disconnect(self, session_id: str):
        del self.session_states[session_id]

    async def send_message(self, session_id: str, message: json):
        print(f"Sending message to session {session_id}: {message}")
        websocket = self.session_states[session_id][0]
        if isinstance(websocket, WebSocket):
            await websocket.send_json(message)
        else:
            raise ValueError("Websocket is not a valid WebSocket object")

manager = ConnectionManager()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    session_id = None
    while True:
        session_id = str(uuid.uuid4())
        if session_id not in manager.session_states:
            break

    await manager.connect(session_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                print(f"Received message from session {session_id}: {message_data}")
                if "query" in message_data:
                    # Update the session state with the new query
                    
                    
                    # Send the result back to the client
                    # await manager.send_message(session_id, json.dumps({
                    #     "agent": "manager",
                    #     "type": "text",
                    #     "message": "Running..."
                    # })) 
                    
                    # Use asyncio to run the blocking function in a thread pool. 
                    # Offloads the blocking function to a thread.
                    manager_agent = manager.session_states[session_id][1]
                    if isinstance(manager_agent, ManagerAgent):
                        await manager_agent.chat(message_data["query"])
                    else:
                        raise ValueError("Manager agent is not a valid ManagerAgent object")
                    
                else:
                    await manager.send_message(session_id, json.dumps({
                        "status": "error",
                        "message": "Invalid message format. Expected 'query' field."
                    }))
            except json.JSONDecodeError:
                await manager.send_message(session_id, json.dumps({
                    "status": "error",
                    "message": "Invalid JSON format."
                }))
    except WebSocketDisconnect:
        manager.disconnect(session_id)

@app.get("/")
def read_root():
    return {"message": "ML Trainer Agent API is running. Connect via WebSocket."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
