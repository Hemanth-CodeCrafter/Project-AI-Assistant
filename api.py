from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from core.brain import Brain
from core.router import Router


brain = Brain()
router = Router()

app = FastAPI(title="Jarvis API")
app.mount("/frontend", StaticFiles(directory="frontend"), name="frontend")

@app.get("/")
def home():
    return FileResponse("frontend/index.html")


@app.post("/command")
def command(data: dict):

    text = data.get("text", "")

    if not text:
        return {
            "error": "No command provided"
        }

    result = router.route(text)
    
    print(type(result))
    print(result)

    # Router handled it
    if result:
        return result
    # Fallback to LLM
    reply = brain.think(text)

    return {
        "source": "brain",
        "response": reply
    }

