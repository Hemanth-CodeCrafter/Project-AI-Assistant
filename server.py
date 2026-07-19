# server.py

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import uvicorn

# Import your command processor
from services.command_processor import CommandProcessor, ProcessOptions

app = FastAPI(
    title="Jarvis Home Server",
    version="1.0.0"
)

processor = CommandProcessor()


class ChatRequest(BaseModel):
    text: str
    user_id: str = "default"


class ChatResponse(BaseModel):
    response: str


@app.get("/")
async def root():
    return {
        "status": "online",
        "name": "Jarvis Home Server",
        "version": "1.0"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        result = processor.process(
            request.text,
            ProcessOptions()
        )

        # If your processor returns a string
        if isinstance(result, str):
            return ChatResponse(response=result)

        # If it returns a dict
        if isinstance(result, dict):
            return ChatResponse(
                response=result.get("response", "")
            )

        return ChatResponse(response=str(result))

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8000,
        reload=False
    )