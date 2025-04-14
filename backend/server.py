import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage, HumanMessage, SystemMessage, AIMessage
from main import ManagerAgent
import json
import asyncio

app = FastAPI()

# Store active connections. Acts as connection pooling
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.session_states: Dict[str, (WebSocket,ManagerAgent)] = {}

    async def connect(self, websocket: WebSocket, session_id: str):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Initialize session state if it doesn't exist
        if session_id not in self.session_states:
            self.session_states[session_id] = (websocket, ManagerAgent(
                websocket_send_message=self.send_message
            ))
        
    def disconnect(self, websocket: WebSocket, session_id: str):
        self.active_connections.remove(websocket)
        del self.session_states[session_id]

    async def send_message(self, session_id: str, message: str):
        websocket = self.session_states[session_id][0]
        if isinstance(websocket, WebSocket):
            await websocket.send_json(message)
        else:
            raise ValueError("Websocket is not a valid WebSocket object")

manager = ConnectionManager()

@app.websocket("/ws/{session_id}/init")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await manager.connect(websocket, session_id)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                message_data = json.loads(data)
                if "query" in message_data:
                    # Update the session state with the new query
                    manager.session_states[session_id]['user_query'] = message_data["query"]
                    
                    # Run the main function in a separate thread to avoid blocking
                    def run_main():
                        if isinstance(manager.session_states[session_id][1], ManagerAgent):
                            result = manager.session_states[session_id][1].chat(message_data["query"])
                        else:
                            raise ValueError("Manager agent is not a valid ManagerAgent object")
                        return result
                    
                    # Send the result back to the client
                    await manager.send_message(websocket, json.dumps({
                        "agent": "manager",
                        "type": "text",
                        "message": "Running..."
                    })) 
                    
                    # Use asyncio to run the blocking function in a thread pool. 
                    # Offloads the blocking function to a thread.
                    result = await asyncio.to_thread(run_main)
                    
                    # Send the result back to the client
                    await manager.send_message(websocket, json.dumps({
                        "status": "complete",
                        "result": result
                    })) 
                else:
                    await manager.send_message(websocket, json.dumps({
                        "status": "error",
                        "message": "Invalid message format. Expected 'query' field."
                    }))
            except json.JSONDecodeError:
                await manager.send_message(websocket, json.dumps({
                    "status": "error",
                    "message": "Invalid JSON format."
                }))
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/")
def read_root():
    return {"message": "ML Trainer Agent API is running. Connect via WebSocket."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
