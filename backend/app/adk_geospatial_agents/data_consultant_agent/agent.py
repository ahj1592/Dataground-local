"""
DataConsultantAgent - Provides data analysis advice and guidance
"""

import os
from typing import Dict, Any
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

from .prompts import get_data_consultant_agent_instruction, get_web_search_prompt, get_follow_up_suggestions_prompt
from .tools import detect_data_analysis_question, search_data_analysis_info, generate_follow_up_suggestions

# ADK Agent 생성
data_consultant_agent = LlmAgent(
    model=LiteLlm(model="openai/gpt-4o"),  # LLMRegistry를 통한 OpenAI GPT-4-turbo 사용
    name="data_consultant_agent",
    instruction=get_data_consultant_agent_instruction(),
    tools=[
        detect_data_analysis_question,
        search_data_analysis_info,
        generate_follow_up_suggestions
    ],
    generate_content_config=types.GenerateContentConfig(temperature=0.3)
)
