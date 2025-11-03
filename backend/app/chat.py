from fastapi import APIRouter, Depends, HTTPException, status, Header, Body, BackgroundTasks
from sqlalchemy.orm import Session
from . import schemas, models, database, utils
from .adk_chat import send_message, generate_ai_response, get_chat_history
import openai
import os
from typing import List, Optional, Dict
from datetime import datetime
from .schemas import ChatOut, MessageOut
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

router = APIRouter()

# Dependency to get DB session
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Dependency to get current user from JWT token
def get_current_user(Authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = Authorization.split(" ")[1]
    payload = utils.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.get('/chats', response_model=List[schemas.ChatOut])
def list_chats(current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chats = db.query(models.Chat).filter(models.Chat.user_id == current_user.id).all()
    return chats

@router.post('/chats', response_model=schemas.ChatOut)
def create_chat(title: str, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    print(f"🚀 [Create Chat] Creating chat with title: '{title}' for user {current_user.id}")
    chat = models.Chat(user_id=current_user.id, title=title)
    db.add(chat)
    db.commit()
    db.refresh(chat)
    print(f"✅ [Create Chat] Chat created successfully: {chat.id}")
    return chat

@router.get('/chats/{chat_id}/messages', response_model=List[schemas.MessageOut])
def get_messages(chat_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    return chat.messages

@router.post('/chats/{chat_id}/messages', response_model=schemas.MessageOut)
async def send_message_endpoint(
    chat_id: int, 
    content: str, 
    background_tasks: BackgroundTasks,
    current_user: models.User = Depends(get_current_user), 
    db: Session = Depends(get_db)
):
    import time
    request_id = f"{int(time.time() * 1000)}_{chat_id}_{content[:10]}"
    print(f"🔍 [ENDPOINT] {request_id} - Starting send_message_endpoint")
    print(f"🔍 [ENDPOINT] {request_id} - Chat ID: {chat_id}, Content: {content[:20]}")
    print(f"🔍 [ENDPOINT] {request_id} - User ID: {current_user.id}")
    
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
    if not chat:
        print(f"❌ [ENDPOINT] {request_id} - Chat not found")
        raise HTTPException(status_code=404, detail="Chat not found")
    
    print(f"✅ [ENDPOINT] {request_id} - Chat found, storing user message")
    # Store user message
    user_msg = models.Message(chat_id=chat_id, sender="user", content=content)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    print(f"✅ [ENDPOINT] {request_id} - User message stored with ID: {user_msg.id}")
    
    # Create loading message immediately to show user that processing has started
    # Use "..." as content to indicate loading state (frontend can check content === "...")
    loading_msg = models.Message(
        chat_id=chat_id,
        sender="assistant",
        content="..."  # Loading indicator - frontend will recognize this
    )
    db.add(loading_msg)
    db.commit()
    db.refresh(loading_msg)
    print(f"✅ [ENDPOINT] {request_id} - Loading message created with ID: {loading_msg.id}")
    
    # Return loading message immediately
    loading_msg_dict = {
        "id": loading_msg.id,
        "sender": loading_msg.sender,
        "content": loading_msg.content,
        "created_at": loading_msg.created_at.isoformat()
    }
    
    # Process message in background and update the loading message
    print(f"🚀 [ADK] Chat API received message from user {current_user.id}: '{content[:50]}...'")
    print(f"🔍 [ENDPOINT] {request_id} - Starting background processing")
    
    # Start background task to process message and update loading message
    from app.adk_chat import process_message_in_background_task
    background_tasks.add_task(
        process_message_in_background_task,
        message=content,
        user_id=current_user.id,
        chat_id=chat_id,
        loading_message_id=loading_msg.id
    )
    
    return loading_msg_dict

@router.patch('/chats/{chat_id}/title', response_model=schemas.ChatOut)
def update_chat_title(chat_id: int, title: str = Body(...), current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    chat.title = title
    db.commit()
    db.refresh(chat)
    return chat

@router.post('/chats/first', response_model=dict)
async def create_chat_with_first_message(
    title: str = Body(...),
    content: str = Body(...),
    current_user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    chat = models.Chat(user_id=current_user.id, title=title, created_at=datetime.utcnow())
    db.add(chat)
    db.commit()
    db.refresh(chat)
    user_msg = models.Message(chat_id=chat.id, sender="user", content=content, created_at=chat.created_at)
    db.add(user_msg)
    db.commit()
    db.refresh(user_msg)
    return {
        "chat": ChatOut.model_validate(chat),
        "message": MessageOut.model_validate(user_msg)
    }

@router.post('/chats/{chat_id}/ai_response', response_model=schemas.MessageOut)
async def generate_ai_response_endpoint(chat_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    # Get the last user message to process
    last_user_message = None
    for message in reversed(chat.messages):
        if message.sender == "user":
            last_user_message = message
            break
    
    if not last_user_message:
        ai_content = "I don't see any user messages to respond to."
    else:
        # Use ADK chat integration for AI response
        print(f"🚀 [ADK] Chat API generating AI response for user {current_user.id}...")
        try:
            response = await generate_ai_response(
                user_id=current_user.id,
                db=db
            )
            ai_content = response.get("message", "Sorry, I cannot generate a response.")
            print(f"✅ [ADK] AI response generated: {ai_content[:100]}...")
            
        except Exception as e:
            print(f"❌ [ADK] Error generating AI response: {str(e)}")
            import traceback
            traceback.print_exc()
            ai_content = f"Sorry, an error occurred: {str(e)}"
    
    # Store AI message
    ai_msg = models.Message(chat_id=chat_id, sender="assistant", content=ai_content)
    db.add(ai_msg)
    db.commit()
    db.refresh(ai_msg)
    return ai_msg

@router.get('/chats/{chat_id}/history', response_model=List[Dict])
def get_chat_history_endpoint(chat_id: int, current_user: models.User = Depends(get_current_user), db: Session = Depends(get_db)):
    chat = db.query(models.Chat).filter(models.Chat.id == chat_id, models.Chat.user_id == current_user.id).first()
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    
    return get_chat_history(current_user.id, db)