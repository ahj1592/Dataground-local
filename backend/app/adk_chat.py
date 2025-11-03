"""
ADK Chat Integration - FastAPI
"""

import os
import time
from typing import List, Dict, Any, Optional
from fastapi import HTTPException, Depends
from sqlalchemy.orm import Session

from .database import get_db
from .models import User, Message, Chat
from .adk_geospatial_agents.main_agent.agent import process_user_message
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents.invocation_context import InvocationContext
from collections import defaultdict

# Global user state management (should be stored in Redis or DB in practice)
user_states = defaultdict[Any, dict[str, str | dict[Any, Any] | list[Any] | None]](lambda: {
    "status": "idle",
    "analysis_type": None,
    "collected_params": {},
    "conversation_context": []
})

# ADK agents are called directly through the process_user_message function

def create_adk_context(user_id: int, chat_id: int):
    """Create CallbackContext according to ADK standards"""
    try:
        # Create InvocationContext according to ADK standards
        from google.adk.sessions import Session
        from google.adk.agents import Agent
        from google.adk.sessions import InMemorySessionService
        
        # Create Session
        session = Session(
            id=f"session_{user_id}_{chat_id}",
            app_name="dataground",
            user_id=str(user_id),
            state={},
            events=[],
            last_update_time=time.time()
        )
        
        # Create SessionService
        session_service = InMemorySessionService()
        
        # Create Agent
        agent = Agent(name="main_agent")
        
        # Create InvocationContext
        invocation_context = InvocationContext(
            session_service=session_service,
            invocation_id=f"inv_{user_id}_{chat_id}_{int(time.time())}",
            agent=agent,
            session=session
        )
        
        # Create CallbackContext
        callback_context = CallbackContext(invocation_context)
        
        # Initialize state
        if "user_states" not in callback_context.state:
            callback_context.state["user_states"] = user_states
        if "current_user_id" not in callback_context.state:
            callback_context.state["current_user_id"] = user_id
        if "chat_id" not in callback_context.state:
            callback_context.state["chat_id"] = chat_id
            
        return callback_context
        
    except ImportError as e:
        print(f"⚠️ [ADK] ADK modules not available, using fallback: {e}")
        # Fallback: Simple MockCallbackContext
        class MockCallbackContext:
            def __init__(self, user_id, chat_id):
                self.state = {
                    "user_states": user_states,
                    "current_user_id": user_id,
                    "chat_id": chat_id
                }
        return MockCallbackContext(user_id, chat_id)
    except Exception as e:
        print(f"❌ [ADK] Error creating ADK context: {e}")
        # Fallback: Simple MockCallbackContext
        class MockCallbackContext:
            def __init__(self, user_id, chat_id):
                self.state = {
                    "user_states": user_states,
                    "current_user_id": user_id,
                    "chat_id": chat_id
                }
        return MockCallbackContext(user_id, chat_id)

async def process_message_in_background_task(
    message: str, 
    user_id: int, 
    chat_id: int, 
    loading_message_id: int
):
    """
    Background task to process message and update loading message with actual response.
    This function runs in background so the API can return immediately with loading message.
    """
    from .database import SessionLocal
    db = SessionLocal()
    try:
        print(f"🔄 [BackgroundTask] Processing message for user {user_id}, chat {chat_id}")
        print(f"🔄 [BackgroundTask] Will update loading message ID: {loading_message_id}")
        
        # Create ADK context
        callback_context = create_adk_context(user_id, chat_id)
        
        # Check if new chat
        user_message_count = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.sender == "user",
            Message.content != message
        ).count()
        is_new_chat = user_message_count == 0
        callback_context.state["is_new_chat"] = is_new_chat
        
        # Load chat history from DB to maintain conversation context within this chat_id
        chat_messages = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.content != "...",  # Exclude loading messages
            Message.content != message  # Exclude current message
        ).order_by(Message.created_at).all()
        
        # Load conversation context from DB messages
        conversation_context = []
        for msg in chat_messages:
            if msg.content and msg.content != "...":
                conversation_context.append({
                    "role": msg.sender,  # 'user' or 'assistant'
                    "content": msg.content,
                    "timestamp": msg.created_at.isoformat() if hasattr(msg.created_at, 'isoformat') else str(msg.created_at)
                })
        
        # Store conversation context in callback context for agent to use
        state_key = f"{user_id}_{chat_id}"
        if state_key not in callback_context.state["user_states"]:
            callback_context.state["user_states"][state_key] = {
                "status": "idle",
                "analysis_type": None,
                "collected_params": {},
                "conversation_context": []
            }
        
        # Initialize conversation_context from DB history if new chat or if empty
        if is_new_chat or not callback_context.state["user_states"][state_key].get("conversation_context"):
            callback_context.state["user_states"][state_key]["conversation_context"] = conversation_context
            print(f"📚 [BackgroundTask] Loaded {len(conversation_context)} messages from chat history")
        else:
            # Merge: use existing context (may have in-memory state) but ensure DB messages are included
            existing_context = callback_context.state["user_states"][state_key]["conversation_context"]
            # Only add messages that aren't already in context
            existing_contents = {ctx.get("content") for ctx in existing_context if ctx.get("content")}
            for msg_context in conversation_context:
                if msg_context.get("content") not in existing_contents:
                    existing_context.append(msg_context)
            print(f"📚 [BackgroundTask] Merged chat history, total context: {len(existing_context)} messages")
        
        # Process message with ADK agent
        response = await process_user_message(message, user_id, callback_context)
        
        # Get actual response content
        response_content = response.get("message", "Sorry, I cannot generate a response.")
        dashboard_updates = response.get("dashboard_updates", [])
        
        print(f"✅ [BackgroundTask] Response generated, updating message ID {loading_message_id}")
        
        # Update the loading message with actual response
        loading_msg = db.query(Message).filter(Message.id == loading_message_id).first()
        if loading_msg:
            loading_msg.content = response_content
            db.commit()
            print(f"✅ [BackgroundTask] Message updated successfully")
        else:
            print(f"⚠️ [BackgroundTask] Loading message {loading_message_id} not found, creating new message")
            # Create new message if loading message was deleted
            new_msg = Message(
                chat_id=chat_id,
                sender="assistant",
                content=response_content
            )
            db.add(new_msg)
            db.commit()
            
    except Exception as e:
        print(f"❌ [BackgroundTask] Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Update loading message with error
        try:
            loading_msg = db.query(Message).filter(Message.id == loading_message_id).first()
            if loading_msg:
                loading_msg.content = f"Sorry, an error occurred: {str(e)}"
                db.commit()
        except Exception as update_error:
            print(f"❌ [BackgroundTask] Failed to update error message: {str(update_error)}")
    finally:
        db.close()

async def send_message(message: str, user_id: int, db: Session, chat_id: int = None) -> Dict[str, Any]:
    """Process messages using ADK agents"""
    import time
    request_id = f"{int(time.time() * 1000)}_{user_id}_{message[:10]}"
    print(f"🔍 [ADK_CHAT] {request_id} - Starting send_message function")
    print(f"🔍 [ADK_CHAT] {request_id} - Message: {message[:20]}, User: {user_id}, Chat: {chat_id}")
    
    try:
        print(f"🚀 [ADK Chat] Processing message from user {user_id}: '{message[:50]}...'")
        
        # Simple check to prevent duplicate requests
        import hashlib
        import time
        request_hash = hashlib.md5(f"{user_id}_{chat_id}_{message}_{int(time.time())}".encode()).hexdigest()
        print(f"🔍 [ADK_CHAT] {request_id} - Request hash: {request_hash}")
        print(f"🔍 [ADK_CHAT] {request_id} - Current processing requests: {getattr(send_message, '_processing_requests', set())}")
        
        if hasattr(send_message, '_processing_requests'):
            if request_hash in send_message._processing_requests:
                print(f"⚠️ [ADK Chat] Duplicate request detected, ignoring: {request_hash}")
                return {"message": "요청이 이미 처리 중입니다.", "status": "duplicate"}
            send_message._processing_requests.add(request_hash)
        else:
            send_message._processing_requests = {request_hash}
        print(f"✅ [ADK_CHAT] {request_id} - Request added to processing set")
        
        # Use user's recent chat if chat_id is not provided
        if not chat_id:
            user_chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).limit(1).all()
            if not user_chats:
                raise HTTPException(status_code=404, detail="No chat found for user")
            chat_id = user_chats[0].id
        
        # Check if this is a new chat (excluding current message from count)
        # Count user messages excluding current message (to check if new chat)
        user_message_count = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.sender == "user",
            Message.content != message  # Exclude current message
        ).count()
        
        is_new_chat = user_message_count == 0  # New chat if no user messages excluding current message
        print(f"🔍 [ADK Chat] User message count (excluding current): {user_message_count}")
        print(f"🔍 [ADK Chat] is_new_chat: {is_new_chat}")
        
        # Debug: Check all messages in current chat
        all_messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()
        print(f"🔍 [ADK Chat] All messages in chat {chat_id}:")
        for msg in all_messages:
            print(f"  - {msg.sender}: {msg.content[:20]}...")
        
        # User message is already saved in send_message_endpoint
        # Only need to generate AI response here
        print(f"✅ [ADK Chat] Processing AI response for chat {chat_id}")
        
        # Create ADK standard CallbackContext
        callback_context = create_adk_context(user_id, chat_id)
        
        # Add new chat information to callback_context
        callback_context.state["is_new_chat"] = is_new_chat
        print(f"🔍 [ADK Chat] Set is_new_chat in callback_context: {is_new_chat}")
        
        # Call ADK agent
        response = await process_user_message(message, user_id, callback_context)
        
        # Get response message content (saving is handled in send_message_endpoint)
        response_content = response.get("message", "Sorry, I cannot generate a response.")
        
        print(f"✅ [ADK Chat] Response generated: '{response_content[:50]}...'")
        
        dashboard_updates = response.get("dashboard_updates", [])
        print(f"🔍 [ADK Chat] Dashboard updates in response: {len(dashboard_updates)} items")
        print(f"🔍 [ADK Chat] Dashboard updates content: {dashboard_updates}")
        
        # Debug ADK response
        print(f"🔍 [ADK Chat] Full ADK response keys: {list(response.keys())}")
        print(f"🔍 [ADK Chat] redirect_to_manual: {response.get('redirect_to_manual', 'NOT_FOUND')}")
        print(f"🔍 [ADK Chat] manual_analysis_params: {response.get('manual_analysis_params', 'NOT_FOUND')}")
        print(f"🔍 [ADK Chat] analysis_type: {response.get('analysis_type', 'NOT_FOUND')}")
        
        # Remove request hash
        if hasattr(send_message, '_processing_requests') and request_hash in send_message._processing_requests:
            send_message._processing_requests.remove(request_hash)
        
        return {
            "message": response_content,
            "status": response.get("status", "completed"),
            "dashboard_updated": response.get("dashboard_updated", False),
            "dashboard_updates": dashboard_updates,
            "redirect_to_manual": response.get("redirect_to_manual", False),
            "manual_analysis_params": response.get("manual_analysis_params", None),
            "analysis_type": response.get("analysis_type", None)
        }
        
    except Exception as e:
        print(f"❌ [ADK Chat] Error processing message: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Save error message
        error_message = f"Sorry, an error occurred: {str(e)}"
        db_error = Message(
            chat_id=chat_id or 0,
            sender="assistant",
            content=error_message
        )
        db.add(db_error)
        db.commit()
        
        raise HTTPException(status_code=500, detail=error_message)

async def generate_ai_response(user_id: int, db: Session) -> Dict[str, Any]:
    """Generate AI response (maintain existing compatibility)"""
    try:
        # Get user's recent chat
        user_chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).limit(1).all()
        
        if not user_chats:
            return {
                "message": "Hello! I'm the DataGround geospatial analysis system. How can I help you with your analysis?",
                "status": "greeting"
            }
        
        # Get messages from the most recent chat
        latest_chat = user_chats[0]
        chat_history = db.query(Message).filter(
            Message.chat_id == latest_chat.id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        if not chat_history:
            return {
                "message": "Hello! I'm the DataGround geospatial analysis system. How can I help you with your analysis?",
                "status": "greeting"
            }
        
        # Find latest user message
        latest_user_message = None
        for msg in reversed(chat_history):
            if msg.sender == "user":
                latest_user_message = msg
                break
        
        if not latest_user_message:
            return {
                "message": "Hello! I'm the DataGround geospatial analysis system. How can I help you with your analysis?",
                "status": "greeting"
            }
        
        # Create ADK standard CallbackContext
        callback_context = create_adk_context(user_id, latest_chat.id)
        
        # Call ADK agent
        response = await process_user_message(latest_user_message.content, user_id, callback_context)
        
        # Save AI message
        ai_message = Message(
            chat_id=latest_chat.id,
            sender="assistant",
            content=response["message"]
        )
        db.add(ai_message)
        db.commit()
        db.refresh(ai_message)
        
        return {
            "message": response["message"],
            "message_id": ai_message.id,
            "timestamp": ai_message.created_at.isoformat(),
            "status": response.get("status", "completed"),
            "dashboard_updated": response.get("dashboard_updated", False),
            "dashboard_updates": response.get("dashboard_updates", [])
        }
        
    except Exception as e:
        print(f"❌ [ADK Chat] Error generating AI response: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return {
            "message": f"Sorry, an error occurred: {str(e)}",
            "status": "error"
        }

def get_chat_history(user_id: int, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """Get chat history"""
    try:
        # Get messages from all user chats
        user_chats = db.query(Chat).filter(Chat.user_id == user_id).all()
        chat_ids = [chat.id for chat in user_chats]
        
        messages = db.query(Message).filter(
            Message.chat_id.in_(chat_ids)
        ).order_by(Message.created_at.desc()).limit(limit).all()
        
        return [
            {
                "id": msg.id,
                "content": msg.content,
                "is_user": msg.sender == "user",
                "timestamp": msg.created_at.isoformat()
            }
            for msg in reversed(messages)
        ]
        
    except Exception as e:
        print(f"❌ [ADK Chat] Error getting chat history: {str(e)}")
        return []
