"""
Main Coordinator Agent - ADK Standard
"""

import os
import asyncio
from datetime import date
from typing import Dict, Any, Optional
from collections import defaultdict

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.tools import load_artifacts
from google.genai import types

from .prompts import get_main_agent_instruction, get_global_instruction
from .tools import (
    call_sea_level_agent,
    call_urban_agent, 
    call_infrastructure_agent,
    call_topic_modeling_agent,
    collect_parameters,
    detect_analysis_intent
)
from ..shared.utils.parameter_collector import parameter_collector
from ..shared.utils.bbox_utils import calculate_bbox, get_standard_buffer

date_today = date.today()

def setup_before_agent_call(callback_context: CallbackContext):
    """Setup before agent call"""
    # Initialize user-specific state
    if "user_states" not in callback_context.state:
        callback_context.state["user_states"] = defaultdict(lambda: {
            "status": "idle",  # idle, collecting_parameters, awaiting_confirmation, analysis_in_progress
            "analysis_type": None,
            "collected_params": {},
            "conversation_context": []
        })
    
    # Set current user ID (should be retrieved from request in practice)
    if "current_user_id" not in callback_context.state:
        callback_context.state["current_user_id"] = 1  # Default value

async def process_user_message(message: str, user_id: int, callback_context: CallbackContext) -> Dict[str, Any]:
    """Main logic for processing user messages"""
    # Setup before ADK agent call
    setup_before_agent_call(callback_context)
    
    user_states = callback_context.state["user_states"]
    user_state = user_states[user_id]
    
    print(f"🚀 [Main Agent] Processing message from user {user_id}: '{message[:50]}...'")
    
    # Check if new chat and initialize state
    is_new_chat = callback_context.state.get("is_new_chat", False)
    if is_new_chat:
        print(f"🔄 [Main Agent] New chat detected, resetting user state")
        user_state["status"] = "idle"
        user_state["analysis_type"] = None
        user_state["collected_params"] = {}
        user_state["conversation_context"] = []
    
    # Add user message to conversation context
    if "conversation_context" not in user_state:
        user_state["conversation_context"] = []
    
    user_state["conversation_context"].append({
        "role": "user",
        "content": message,
        "timestamp": "now"
    })
    
    # Process by status
    if user_state["status"] == "collecting_parameters":
        return await handle_parameter_collection(message, user_id, user_state, callback_context)
    elif user_state["status"] == "awaiting_confirmation":
        return await handle_confirmation(message, user_id, user_state, callback_context)
    else:
        return await handle_new_request(message, user_id, user_state, callback_context)

async def handle_new_request(message: str, user_id: int, user_state: Dict[str, Any], callback_context: CallbackContext) -> Dict[str, Any]:
    """Handle new request"""
    print(f"🔍 [Main Agent] Analyzing new request...")
    
    # Detect analysis intent
    try:
        intent_result = await detect_analysis_intent(message, callback_context)
        print(f"🔍 [Main Agent] Intent detection result: {intent_result}")
        analysis_type = intent_result.get("intent")
        
        print(f"🔍 [Main Agent] analysis_type value: '{analysis_type}' (type: {type(analysis_type)})")
        print(f"🔍 [Main Agent] analysis_type is truthy: {bool(analysis_type)}")
        
        if analysis_type:
            print(f"📊 [Main Agent] Detected analysis type: {analysis_type}")
            print(f"📊 [Main Agent] Entering analysis setup block...")
        else:
            print(f"❌ [Main Agent] No analysis intent detected")
    except Exception as e:
        print(f"❌ [Main Agent] Intent detection error: {str(e)}")
        import traceback
        traceback.print_exc()
        analysis_type = None
    
    # Only proceed with parameter collection if analysis_type exists
    if analysis_type:
        print(f"🔧 [Main Agent] Setting up parameter collection for {analysis_type}...")
        
        # Start parameter collection
        user_state["status"] = "collecting_parameters"
        user_state["analysis_type"] = analysis_type
        user_state["collected_params"] = {}
        
        print(f"🔧 [Main Agent] User state updated: {user_state}")
        
        # Collect parameters
        try:
            print(f"🔧 [Main Agent] Starting parameter collection...")
            param_result = await parameter_collector.collect_parameters(
                message, analysis_type, user_state["collected_params"]
            )
            print(f"🔧 [Main Agent] Parameter collection result: {param_result}")
        except Exception as e:
            print(f"❌ [Main Agent] Parameter collection error: {str(e)}")
            import traceback
            traceback.print_exc()
            return {
                "message": "An error occurred during parameter collection. Please try again.",
                "status": "error"
            }
        
        if param_result["needs_more_info"]:
            print(f"🔧 [Main Agent] More information needed, generating question...")
            missing_params = param_result["validation"]["missing"]
            print(f"🔧 [Main Agent] Missing params: {missing_params}")
            
            # Change order to ask Country first, then City
            if "country_name" in missing_params:
                question = "Which country would you like to analyze? (e.g., South Korea, United States)"
            elif "city_name" in missing_params:
                question = "Which city would you like to analyze? (e.g., Seoul, Busan, New York)"
            else:
                # Ask only the first missing parameter
                first_missing = missing_params[0]
                question = parameter_collector.generate_questions([first_missing], analysis_type)
            
            response_message = f"Yes, I'll help you with {analysis_type.replace('_', ' ')} analysis! {question}"
            print(f"🔧 [Main Agent] Generated response: {response_message}")
            
            # Add AI response to conversation context
            user_state["conversation_context"].append({
                "role": "assistant",
                "content": response_message,
                "timestamp": "now"
            })
            
            return {
                "message": response_message,
                "analysis_type": analysis_type,
                "status": "collecting_parameters",
                "needs_clarification": True
            }
        else:
            print(f"🔧 [Main Agent] All parameters collected, executing analysis...")
            # All parameters collected - execute analysis
            return await execute_analysis(analysis_type, param_result["params"], user_id, user_state, callback_context)
    else:
        # General conversation - show welcome message only for new chats
        is_new_chat = callback_context.state.get("is_new_chat", False)
        print(f"🔍 [Main Agent] is_new_chat: {is_new_chat}")
        
        if is_new_chat:
            print(f"🔍 [Main Agent] Showing welcome message for new chat")
            return {
                "message": "Hello! I'm the DataGround geospatial analysis system. How can I help you with your analysis?\n\nSupported analyses:\n- Sea level rise risk analysis\n- Urban area analysis\n- Infrastructure exposure analysis\n- Topic modeling analysis",
                "status": "general_chat"
            }
        else:
            print(f"🔍 [Main Agent] Showing generic response for existing chat")
            # Friendly response for general conversation
            return {
                "message": "Hello! How can I help you today? I can assist you with:\n\n• Sea level rise risk analysis\n• Urban area analysis\n• Infrastructure exposure analysis\n• Topic modeling analysis\n\nJust let me know what you'd like to analyze!",
                "status": "general_chat"
            }

async def handle_parameter_collection(message: str, user_id: int, user_state: Dict[str, Any], callback_context: CallbackContext) -> Dict[str, Any]:
    """Handle parameter collection"""
    print(f"🔧 [Main Agent] Collecting parameters for {user_state['analysis_type']}...")
    
    analysis_type = user_state["analysis_type"]
    existing_params = user_state["collected_params"]
    
    # Collect parameters
    try:
        param_result = await parameter_collector.collect_parameters(
            message, analysis_type, existing_params
        )
        print(f"🔧 [Main Agent] Parameter collection result: {param_result}")
    except Exception as e:
        print(f"❌ [Main Agent] Parameter collection error: {str(e)}")
        import traceback
        traceback.print_exc()
        return {
            "message": "An error occurred during parameter collection. Please try again.",
            "status": "error"
        }
    
    # Update collected parameters
    user_state["collected_params"] = param_result["params"]
    
    # If there's an exact match, ignore suggestion message and continue
    has_exact_match = any(key in param_result["params"] for key in ["city_name", "country_name"])
    
    # Only process if there's a suggestion message and no exact match
    if not has_exact_match and "suggestion_message" in param_result["params"]:
        return {
            "message": param_result["params"]["suggestion_message"],
            "analysis_type": analysis_type,
            "status": "collecting_parameters",
            "needs_clarification": True,
            "suggestion": True
        }
    
    # Generate confirmation message for collected information
    collected = user_state["collected_params"]
    country = collected.get("country_name", "None")
    city = collected.get("city_name", "None") 
    
    confirmation_message = f"Thank you! I've received the following information:\n"
    confirmation_message += f"Country: {country}\n"
    confirmation_message += f"City: {city}\n"
    
    # Display different information by analysis type
    if analysis_type == "urban_analysis":
        start_year = collected.get("start_year", "None")
        end_year = collected.get("end_year", "None")
        threshold = collected.get("threshold", "None")
        confirmation_message += f"Start Year: {start_year}\n"
        confirmation_message += f"End Year: {end_year}\n"
        if threshold != "None":
            threshold = f"{threshold}m"
        confirmation_message += f"Sea-level: {threshold}"
    else:
        year = collected.get("year", "None")
        threshold = collected.get("threshold", "None")
        confirmation_message += f"Year: {year}\n"
        if threshold != "None":
            threshold = f"{threshold}m"
        confirmation_message += f"Sea-level: {threshold}"
    
    # Check if all parameters are collected
    all_collected = parameter_collector.are_all_parameters_collected(
        param_result["params"], analysis_type
    )
    
    print(f"🔍 [Main Agent] Parameter collection check: all_collected={all_collected}")
    print(f"🔍 [Main Agent] Current params: {param_result['params']}")
    print(f"🔍 [Main Agent] Validation result: {param_result['validation']}")
    
    if not all_collected:
        # Still missing parameters
        missing_params = param_result["validation"]["missing"]
        # Change order to ask Country first, then City
        if "country_name" in missing_params:
            question = "Which country would you like to analyze? (e.g., South Korea, United States)"
        elif "city_name" in missing_params:
            question = "Which city would you like to analyze? (e.g., Seoul, Busan, New York)"
        else:
            # Ask only the next missing parameter
            next_missing = missing_params[0]
            question = parameter_collector.generate_questions([next_missing], analysis_type)
        
        return {
            "message": f"{confirmation_message}\n\n{question}",
            "analysis_type": analysis_type,
            "status": "collecting_parameters",
            "needs_clarification": True
        }
    else:
        # All parameters collected - request user confirmation
        print(f"✅ [Main Agent] All parameters collected, requesting user confirmation...")
        user_state["status"] = "awaiting_confirmation"  # Change to confirmation waiting state
        
        return {
            "message": f"{confirmation_message}\n\nIs this information correct? (yes/no)",
            "analysis_type": analysis_type,
            "status": "awaiting_confirmation",
            "needs_clarification": True
        }

async def handle_confirmation(message: str, user_id: int, user_state: Dict[str, Any], callback_context: CallbackContext) -> Dict[str, Any]:
    """Handle user confirmation"""
    print(f"❓ [Main Agent] Handling user confirmation...")
    
    message_lower = message.lower().strip()
    
    # Check for positive response
    positive_responses = ['yes', 'y', '응', '그래', '맞아', '맞다', '맞습니다', '네', '좋아', 'ok', 'okay']
    negative_responses = ['no', 'n', '아니', '아니다', '아니요', '아닙니다', '틀렸', '다시', '취소']
    
    if any(response in message_lower for response in positive_responses):
        # User confirmed - execute analysis
        print(f"✅ [Main Agent] User confirmed, executing analysis...")
        user_state["status"] = "idle"  # Reset state
        analysis_type = user_state["analysis_type"]
        collected_params = user_state["collected_params"]
        return await execute_analysis(analysis_type, collected_params, user_id, user_state, callback_context)
    
    elif any(response in message_lower for response in negative_responses):
        # User rejected - start over from beginning
        print(f"🔄 [Main Agent] User rejected, restarting parameter collection...")
        user_state["status"] = "collecting_parameters"
        user_state["collected_params"] = {}  # Reset collected parameters
        
        analysis_type = user_state["analysis_type"]
        return {
            "message": f"Understood! I'll restart the {analysis_type.replace('_', ' ')} analysis. What year would you like to analyze? (2001-2020) (e.g., 2020, 2018)",
            "analysis_type": analysis_type,
            "status": "collecting_parameters",
            "needs_clarification": True
        }
    
    else:
        # Unclear response - request confirmation again
        collected = user_state["collected_params"]
        country = collected.get("country_name", "None")
        city = collected.get("city_name", "None")
        analysis_type = user_state["analysis_type"]
        
        confirmation_message = f"Thank you! I've received the following information:\n"
        confirmation_message += f"Country: {country}\n"
        confirmation_message += f"City: {city}\n"
        
        # Display different information by analysis type
        if analysis_type == "urban_analysis":
            start_year = collected.get("start_year", "None")
            end_year = collected.get("end_year", "None")
            threshold = collected.get("threshold", "None")
            confirmation_message += f"Start Year: {start_year}\n"
            confirmation_message += f"End Year: {end_year}\n"
            if threshold != "None":
                threshold = f"{threshold}m"
            confirmation_message += f"Sea-level: {threshold}"
        else:
            year = collected.get("year", "None")
            threshold = collected.get("threshold", "None")
            confirmation_message += f"Year: {year}\n"
            if threshold != "None":
                threshold = f"{threshold}m"
            confirmation_message += f"Sea-level: {threshold}"
        
        return {
            "message": f"{confirmation_message}\n\nIs this information correct? (yes/no)",
            "analysis_type": user_state["analysis_type"],
            "status": "awaiting_confirmation",
            "needs_clarification": True
        }

async def execute_analysis(analysis_type: str, params: Dict[str, Any], user_id: int, user_state: Dict[str, Any], callback_context: CallbackContext) -> Dict[str, Any]:
    """Automatically execute analysis after parameter collection is complete"""
    print(f"🚀 [Main Agent] Parameters collected for {analysis_type} analysis with params: {params}")
    
    # Generate URL parameters to pass to manual analysis system
    # Include only necessary parameters for each analysis type
    analysis_params = {
        "task": analysis_type,
        "country": params.get("country_name", ""),
        "city": params.get("city_name", ""),
    }
    
    # 연도 파라미터 설정
    if analysis_type == "urban_analysis":
        analysis_params["year1"] = params.get("start_year", "")
        analysis_params["year2"] = params.get("end_year", "")
    else:
        analysis_params["year1"] = params.get("year", "")
    
    # Add threshold only for analysis types that require it
    if analysis_type in ["sea_level_rise", "infrastructure_analysis", "urban_analysis"]:
        analysis_params["threshold"] = params.get("threshold", "")
    
    # Add special parameters for topic_modeling
    if analysis_type == "topic_modeling":
        analysis_params.update({
            "method": params.get("method", "lda"),
            "nTopics": params.get("n_topics", 10),
            "minDf": params.get("min_df", 2.0),
            "maxDf": params.get("max_df", 0.95),
            "ngramRange": params.get("ngram_range", "1,1"),
            "inputType": params.get("input_type", "text"),
            "textInput": params.get("text_input", ""),
            "files": params.get("files", [])
        })
    
    # Analysis type messages
    analysis_messages = {
        "sea_level_rise": "Sea Level Rise Risk Analysis",
        "urban_analysis": "Urban Area Analysis", 
        "infrastructure_analysis": "Infrastructure Exposure Analysis",
        "topic_modeling": "Topic Modeling Analysis"
    }
    
    analysis_name = analysis_messages.get(analysis_type, analysis_type.replace('_', ' ').title())
    
    # Create dashboard updates for automatic analysis execution
    dashboard_updates = [{
        "type": "analysis_triggered",
        "analysis_type": analysis_type,
        "params": analysis_params,
        "auto_execute": True
    }]
    
    # Analysis completion message
    response_message = f"""✅ **{analysis_name} has been automatically executed!**

📋 **Analysis Information:**
• Country: {params.get("country_name", "N/A")}
• City: {params.get("city_name", "N/A")}
• Year: {params.get("year", "N/A")}
• Threshold: {params.get("threshold", "N/A")}m

🔍 **Analysis results are displayed on the dashboard.**
💡 **Tip:** To modify parameters, you can re-analyze in the "Map" tab."""
    
    # Add AI response to conversation context
    user_state["conversation_context"].append({
        "role": "assistant",
        "content": response_message,
        "timestamp": "now"
    })
    
    # Reset user state after analysis completion to allow new conversations
    user_state["status"] = "idle"
    user_state["analysis_type"] = None
    user_state["collected_params"] = {}
    
    return {
        "message": response_message,
        "status": "analysis_completed",
        "analysis_type": analysis_type,
        "collected_params": params,
        "redirect_to_manual": True,
        "manual_analysis_params": analysis_params,
        "dashboard_updated": True,
        "dashboard_updates": dashboard_updates
    }

# Mock analysis functions (instead of actual analysis logic) - COMMENTED OUT
# These functions are no longer used as the system now uses real API calls
# async def mock_sea_level_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Mock sea level rise analysis"""
#     await asyncio.sleep(1)  # Analysis simulation
#     return {
#         "analysis_type": "sea_level_rise",
#         "results": {
#             "risk_level": "High",
#             "affected_area": "15.2 km²",
#             "population_at_risk": "45,000"
#         },
#         "dashboard_updates": [
#             {"type": "map", "data": "sea_level_risk_map"},
#             {"type": "chart", "data": "risk_distribution_chart"}
#         ]
#     }

# async def mock_urban_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Mock urban analysis"""
#     await asyncio.sleep(1)  # Analysis simulation
#     return {
#         "analysis_type": "urban_analysis",
#         "results": {
#             "urban_growth_rate": "3.2%",
#             "population_density": "2,450/km²",
#             "built_up_area": "28.5 km²"
#         },
#         "dashboard_updates": [
#             {"type": "map", "data": "urban_expansion_map"},
#             {"type": "chart", "data": "growth_trends_chart"}
#         ]
#     }

# async def mock_infrastructure_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Mock infrastructure analysis"""
#     await asyncio.sleep(1)  # Analysis simulation
#     return {
#         "analysis_type": "infrastructure_analysis",
#         "results": {
#             "exposed_infrastructure": "12 facilities",
#             "risk_score": "7.8/10",
#             "vulnerable_assets": "roads, bridges, power plants"
#         },
#         "dashboard_updates": [
#             {"type": "map", "data": "infrastructure_exposure_map"},
#             {"type": "chart", "data": "vulnerability_assessment_chart"}
#         ]
#     }

# async def mock_topic_modeling_analysis(params: Dict[str, Any]) -> Dict[str, Any]:
#     """Mock topic modeling analysis"""
#     await asyncio.sleep(1)  # Analysis simulation
#     return {
#         "analysis_type": "topic_modeling",
#         "results": {
#             "topics_found": 5,
#             "main_topics": ["climate change", "urban planning", "infrastructure", "risk assessment", "policy"],
#             "coherence_score": 0.85
#         },
#         "dashboard_updates": [
#             {"type": "chart", "data": "topic_distribution_chart"},
#             {"type": "table", "data": "topic_keywords_table"}
#         ]
#     }

# ADK Agent 생성
main_agent = Agent(
    model=os.getenv("MAIN_AGENT_MODEL", "gemini-2.0-flash-exp"),
    name="geospatial_analysis_coordinator",
    instruction=get_main_agent_instruction(),
    global_instruction=get_global_instruction(),
    sub_agents=[],  # 서브 에이전트들은 tools를 통해 호출
    tools=[
        call_sea_level_agent,
        call_urban_agent,
        call_infrastructure_agent,
        call_topic_modeling_agent,
        collect_parameters,
        detect_analysis_intent,
        load_artifacts
    ],
    before_agent_callback=setup_before_agent_call,
    generate_content_config=types.GenerateContentConfig(temperature=0.01)
)

# Actual GEE API call functions
async def call_sea_level_analysis_api(params: Dict[str, Any]) -> Dict[str, Any]:
    """Sea Level Rise analysis API call"""
    try:
        import httpx
        
        # API endpoint URL
        base_url = "http://localhost:8000"  # FastAPI server URL
        endpoint = "/analysis/sea-level-rise"
        
        # Configure request parameters (GET request)
        coordinates = params.get("coordinates", {})
        buffer = get_standard_buffer("sea_level_rise")
        bbox_params = calculate_bbox(coordinates, buffer)
        bbox_params["threshold"] = params.get("threshold", 2.0)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}{endpoint}", params=bbox_params)
            response.raise_for_status()
            result = response.json()
            
            dashboard_updates = [
                {
                    "type": "map_update",
                    "data": result.get("map_data", {}),
                    "center": [params.get("coordinates", {}).get("lng", 0), 
                             params.get("coordinates", {}).get("lat", 0)],
                    "zoom": 10
                },
                {
                    "type": "chart_update", 
                    "data": result.get("chart_data", {}),
                    "chart_type": "sea_level_rise"
                }
            ]
            
            print(f"🔍 [API Call] Sea Level Rise dashboard_updates created: {len(dashboard_updates)} items")
            print(f"🔍 [API Call] Dashboard updates content: {dashboard_updates}")
            
            return {
                "success": True,
                "data": result,
                "dashboard_updates": dashboard_updates
            }
    except Exception as e:
        print(f"❌ [API Call] Sea Level Rise API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "dashboard_updates": []
        }

async def call_urban_analysis_api(params: Dict[str, Any]) -> Dict[str, Any]:
    """Urban Analysis API 호출"""
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        endpoint = "/analysis/urban-area-comprehensive-stats"
        
        # Configure request parameters (GET request)
        coordinates = params.get("coordinates", {})
        buffer = get_standard_buffer("urban_analysis")
        bbox_params = calculate_bbox(coordinates, buffer)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}{endpoint}", params=bbox_params)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "data": result,
                "dashboard_updates": [
                    {
                        "type": "map_update",
                        "data": result.get("map_data", {}),
                        "center": [params.get("coordinates", {}).get("lng", 0), 
                                 params.get("coordinates", {}).get("lat", 0)],
                        "zoom": 10
                    },
                    {
                        "type": "chart_update",
                        "data": result.get("chart_data", {}),
                        "chart_type": "urban_analysis"
                    }
                ]
            }
    except Exception as e:
        print(f"❌ [API Call] Urban Analysis API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "dashboard_updates": []
        }

async def call_infrastructure_analysis_api(params: Dict[str, Any]) -> Dict[str, Any]:
    """Infrastructure Analysis API 호출"""
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        endpoint = "/analysis/infrastructure-exposure"
        
        # Configure request parameters (GET request)
        coordinates = params.get("coordinates", {})
        buffer = get_standard_buffer("infrastructure_analysis")
        bbox_params = calculate_bbox(coordinates, buffer)
        
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{base_url}{endpoint}", params=bbox_params)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "data": result,
                "dashboard_updates": [
                    {
                        "type": "map_update",
                        "data": result.get("map_data", {}),
                        "center": [params.get("coordinates", {}).get("lng", 0), 
                                 params.get("coordinates", {}).get("lat", 0)],
                        "zoom": 10
                    },
                    {
                        "type": "chart_update",
                        "data": result.get("chart_data", {}),
                        "chart_type": "infrastructure_exposure"
                    }
                ]
            }
    except Exception as e:
        print(f"❌ [API Call] Infrastructure Analysis API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "dashboard_updates": []
        }

async def call_topic_modeling_api(params: Dict[str, Any]) -> Dict[str, Any]:
    """Topic Modeling API 호출"""
    try:
        import httpx
        
        base_url = "http://localhost:8000"
        endpoint = "/analysis/topic-modeling"
        
        # 요청 데이터 구성 (POST 요청)
        request_data = {
            "year": params.get("year"),
            "method": params.get("method", "lda"),
            "topics": params.get("topics", 5)
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(f"{base_url}{endpoint}", json=request_data)
            response.raise_for_status()
            result = response.json()
            
            return {
                "success": True,
                "data": result,
                "dashboard_updates": [
                    {
                        "type": "chart_update",
                        "data": result.get("chart_data", {}),
                        "chart_type": "topic_modeling"
                    }
                ]
            }
    except Exception as e:
        print(f"❌ [API Call] Topic Modeling API error: {e}")
        return {
            "success": False,
            "error": str(e),
            "dashboard_updates": []
        }
