from fastapi import APIRouter
from utils.ai_agent import query_nim

router = APIRouter()

@router.get("/test", tags=["AI"])
async def ai_test():
    """
    Simple endpoint to verify the AI agent is working.
    """
    prompt = "Say 'Hello from CulinAIry AI!' in a fun way."
    response = query_nim(prompt)
    return {
        "status": "ok",
        "prompt": prompt,
        "ai_response": response
    }
