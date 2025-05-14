import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import Dict
from main import ManagerAgent
import json
import asyncio
import uuid
import uvicorn

app = FastAPI()

# Store active connections. Acts as connection pooling
class ConnectionManager:
    ''' Stores the connections into the server into pool of WebSockets with unique IDs.'''
    def __init__(self):
        self.session_states: Dict[str, (WebSocket, ManagerAgent)] = {}
        self.max_connections = 1000 # arbitrarily set

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
    '''
    Initiate websocket connection with a client from server. 
    Then offload waiting for request to another thread
    '''
    session_id = None
    while True:
        session_id = str(uuid.uuid4())
        if session_id not in manager.session_states:
            break

    await manager.connect(session_id, websocket)
    async def inner_loop(): 
        '''
        Helper function. Divides the part of the websocket that can be offloaded away from primary server functions.
        Runs as a seperate task in another thread, thus not blocking the server from handling multiple users.
        '''
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    message_data = json.loads(data)
                    print(f"Received message from session {session_id}: {message_data}")
                    if "query" in message_data:
                        # Offloads the blocking function to a thread using asyncio
                        manager_agent = manager.session_states[session_id][1]
                        if isinstance(manager_agent, ManagerAgent):
                            manager_agent.user_query = message_data["query"]
                            await manager_agent.main()
                        
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
    tmp = asyncio.create_task(inner_loop())
    

@app.get("/")
def read_root():
    '''Heartbeat API call'''
    return {"message": "ML Trainer Agent API is running. Connect via WebSocket."}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
