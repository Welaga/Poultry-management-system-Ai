"""Chatbot endpoints."""
from fastapi import APIRouter, Depends
from app.utils.schemas import ChatMessage, ChatResponse
from app.utils.security import get_current_user
from app.services.chatbot_service import ChatbotService, DEFAULT_SUGGESTIONS

router = APIRouter()


@router.post("/message", response_model=ChatResponse)
def chat(payload: ChatMessage, current=Depends(get_current_user)):
    result = ChatbotService.respond(payload.message)
    return ChatResponse(response=result["response"], suggestions=result["suggestions"])


@router.get("/suggestions")
def suggestions(current=Depends(get_current_user)):
    return {"suggestions": DEFAULT_SUGGESTIONS}
