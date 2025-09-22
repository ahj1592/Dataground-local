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

# 전역 사용자 상태 관리 (실제로는 Redis나 DB에 저장해야 함)
user_states = defaultdict(lambda: {
    "status": "idle",
    "analysis_type": None,
    "collected_params": {},
    "conversation_context": []
})

# ADK 에이전트는 process_user_message 함수를 통해 직접 호출됩니다

def create_adk_context(user_id: int, chat_id: int):
    """ADK 표준에 맞는 CallbackContext 생성"""
    try:
        # ADK 표준에 맞는 InvocationContext 생성
        from google.adk.sessions import Session
        from google.adk.agents import Agent
        from google.adk.sessions import InMemorySessionService
        
        # Session 생성
        session = Session(
            id=f"session_{user_id}_{chat_id}",
            app_name="dataground",
            user_id=str(user_id),
            state={},
            events=[],
            last_update_time=time.time()
        )
        
        # SessionService 생성
        session_service = InMemorySessionService()
        
        # Agent 생성
        agent = Agent(name="main_agent")
        
        # InvocationContext 생성
        invocation_context = InvocationContext(
            session_service=session_service,
            invocation_id=f"inv_{user_id}_{chat_id}_{int(time.time())}",
            agent=agent,
            session=session
        )
        
        # CallbackContext 생성
        callback_context = CallbackContext(invocation_context)
        
        # 상태 초기화
        if "user_states" not in callback_context.state:
            callback_context.state["user_states"] = user_states
        if "current_user_id" not in callback_context.state:
            callback_context.state["current_user_id"] = user_id
        if "chat_id" not in callback_context.state:
            callback_context.state["chat_id"] = chat_id
            
        return callback_context
        
    except ImportError as e:
        print(f"⚠️ [ADK] ADK modules not available, using fallback: {e}")
        # Fallback: 간단한 MockCallbackContext
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
        # Fallback: 간단한 MockCallbackContext
        class MockCallbackContext:
            def __init__(self, user_id, chat_id):
                self.state = {
                    "user_states": user_states,
                    "current_user_id": user_id,
                    "chat_id": chat_id
                }
        return MockCallbackContext(user_id, chat_id)

async def send_message(message: str, user_id: int, db: Session, chat_id: int = None) -> Dict[str, Any]:
    """ADK 에이전트를 사용하여 메시지 처리"""
    import time
    request_id = f"{int(time.time() * 1000)}_{user_id}_{message[:10]}"
    print(f"🔍 [ADK_CHAT] {request_id} - Starting send_message function")
    print(f"🔍 [ADK_CHAT] {request_id} - Message: {message[:20]}, User: {user_id}, Chat: {chat_id}")
    
    try:
        print(f"🚀 [ADK Chat] Processing message from user {user_id}: '{message[:50]}...'")
        
        # 중복 요청 방지를 위한 간단한 체크
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
        
        # chat_id가 없으면 사용자의 최근 채팅 사용
        if not chat_id:
            user_chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).limit(1).all()
            if not user_chats:
                raise HTTPException(status_code=404, detail="No chat found for user")
            chat_id = user_chats[0].id
        
        # 새로운 채팅인지 확인 (현재 메시지 제외하고 카운트)
        # 현재 메시지를 제외한 사용자 메시지 카운트 (새 채팅 여부 확인용)
        user_message_count = db.query(Message).filter(
            Message.chat_id == chat_id,
            Message.sender == "user",
            Message.content != message  # 현재 메시지 제외
        ).count()
        
        is_new_chat = user_message_count == 0  # 현재 메시지를 제외한 사용자 메시지가 없으면 새로운 채팅
        print(f"🔍 [ADK Chat] User message count (excluding current): {user_message_count}")
        print(f"🔍 [ADK Chat] is_new_chat: {is_new_chat}")
        
        # 디버깅: 현재 채팅의 모든 메시지 확인
        all_messages = db.query(Message).filter(Message.chat_id == chat_id).order_by(Message.created_at).all()
        print(f"🔍 [ADK Chat] All messages in chat {chat_id}:")
        for msg in all_messages:
            print(f"  - {msg.sender}: {msg.content[:20]}...")
        
        # 사용자 메시지는 이미 send_message_endpoint에서 저장되었으므로
        # 여기서는 AI 응답만 생성하면 됨
        print(f"✅ [ADK Chat] Processing AI response for chat {chat_id}")
        
        # ADK 표준 CallbackContext 생성
        callback_context = create_adk_context(user_id, chat_id)
        
        # 새로운 채팅 정보를 callback_context에 추가
        callback_context.state["is_new_chat"] = is_new_chat
        print(f"🔍 [ADK Chat] Set is_new_chat in callback_context: {is_new_chat}")
        
        # ADK 에이전트 호출
        response = await process_user_message(message, user_id, callback_context)
        
        # 응답 메시지 내용 가져오기 (저장은 send_message_endpoint에서 처리)
        response_content = response.get("message", "죄송합니다. 응답을 생성할 수 없습니다.")
        
        print(f"✅ [ADK Chat] Response generated: '{response_content[:50]}...'")
        
        dashboard_updates = response.get("dashboard_updates", [])
        print(f"🔍 [ADK Chat] Dashboard updates in response: {len(dashboard_updates)} items")
        print(f"🔍 [ADK Chat] Dashboard updates content: {dashboard_updates}")
        
        # Debug ADK response
        print(f"🔍 [ADK Chat] Full ADK response keys: {list(response.keys())}")
        print(f"🔍 [ADK Chat] redirect_to_manual: {response.get('redirect_to_manual', 'NOT_FOUND')}")
        print(f"🔍 [ADK Chat] manual_analysis_params: {response.get('manual_analysis_params', 'NOT_FOUND')}")
        print(f"🔍 [ADK Chat] analysis_type: {response.get('analysis_type', 'NOT_FOUND')}")
        
        # 요청 해시 제거
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
        
        # 에러 메시지 저장
        error_message = f"죄송합니다. 오류가 발생했습니다: {str(e)}"
        db_error = Message(
            chat_id=chat_id or 0,
            sender="assistant",
            content=error_message
        )
        db.add(db_error)
        db.commit()
        
        raise HTTPException(status_code=500, detail=error_message)

async def generate_ai_response(user_id: int, db: Session) -> Dict[str, Any]:
    """AI 응답 생성 (기존 호환성 유지)"""
    try:
        # 사용자의 최근 채팅 가져오기
        user_chats = db.query(Chat).filter(Chat.user_id == user_id).order_by(Chat.created_at.desc()).limit(1).all()
        
        if not user_chats:
            return {
                "message": "안녕하세요! DataGround 지리공간 분석 시스템입니다. 어떤 분석을 도와드릴까요?",
                "status": "greeting"
            }
        
        # 가장 최근 채팅의 메시지들 가져오기
        latest_chat = user_chats[0]
        chat_history = db.query(Message).filter(
            Message.chat_id == latest_chat.id
        ).order_by(Message.created_at.desc()).limit(10).all()
        
        if not chat_history:
            return {
                "message": "안녕하세요! DataGround 지리공간 분석 시스템입니다. 어떤 분석을 도와드릴까요?",
                "status": "greeting"
            }
        
        # 최신 사용자 메시지 찾기
        latest_user_message = None
        for msg in reversed(chat_history):
            if msg.sender == "user":
                latest_user_message = msg
                break
        
        if not latest_user_message:
            return {
                "message": "안녕하세요! DataGround 지리공간 분석 시스템입니다. 어떤 분석을 도와드릴까요?",
                "status": "greeting"
            }
        
        # ADK 표준 CallbackContext 생성
        callback_context = create_adk_context(user_id, latest_chat.id)
        
        # ADK 에이전트 호출
        response = await process_user_message(latest_user_message.content, user_id, callback_context)
        
        # AI 메시지 저장
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
            "message": f"죄송합니다. 오류가 발생했습니다: {str(e)}",
            "status": "error"
        }

def get_chat_history(user_id: int, db: Session, limit: int = 50) -> List[Dict[str, Any]]:
    """채팅 기록 가져오기"""
    try:
        # 사용자의 모든 채팅에서 메시지 가져오기
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
