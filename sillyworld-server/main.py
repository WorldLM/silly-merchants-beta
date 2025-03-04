from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

app = FastAPI(title="SillyWorld API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Frontend URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Message(BaseModel):
    content: str

@app.get("/")
async def root():
    return {"message": "Welcome to SillyWorld API!"}

@app.get("/api/hello")
async def hello():
    return {"message": "Hello from SillyWorld!"}

@app.post("/api/echo")
async def echo(message: Message):
    return {"message": f"You said: {message.content}"}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True) 