"""
Tools for DataConsultantAgent
"""

import re
import os
import json
import warnings
from typing import Dict, Any, List
from google.adk.tools import ToolContext
from ..shared.tools.web_search_tool import web_search_tool

# Suppress Pydantic serializer warnings from OpenAI SDK
# These warnings occur when ADK tries to serialize OpenAI responses and are harmless
warnings.filterwarnings("ignore", category=UserWarning, module=".*pydantic.*")
warnings.filterwarnings("ignore", message=".*Pydantic.*serializer.*")
warnings.filterwarnings("ignore", message=".*PydanticSerializationUnexpectedValue.*")

# ============================================================================
# KEYWORD-BASED DETECTION (DEPRECATED - 주석 처리됨)
# ============================================================================
# 급하게 사용할 것을 대비해 보관 중
# 사용 시 detect_data_analysis_question_keywords로 이름이 변경되었음

# # Data analysis related keywords
# DATA_ANALYSIS_KEYWORDS = [
#     # Original keywords
#     "data analysis", "data science", "machine learning", "deep learning", "AI", "statistics",
#     # Additional keywords
#     "analytics", "modeling", "prediction", "predict", "classification", "regression",
#     "neural network", "algorithm", "feature engineering",
#     "data visualization", "dashboard", "reporting",
#     "big data", "data mining", "data preprocessing",
#     "supervised learning", "unsupervised learning", "reinforcement learning",
#     "clustering", "dimensionality reduction", "feature selection",
#     "cross validation", "overfitting", "bias variance",
#     "data pipeline", "ETL", "data warehouse", "data lake",
#     "python", "R", "pandas", "numpy", "scikit-learn", "tensorflow", "pytorch",
#     "jupyter", "notebook", "dataframe", "dataset",
#     # Data formats and common terms
#     "csv", "excel", "json", "sql", "database", "table",
#     "start with", "begin", "tutorial", "guide", "how to",
#     "purchase", "sales", "customer", "business", "forecast",
#     "recommendation", "recommend", "suggest", "advice",
#     "analysis", "analyze", "analize",  # 분석 관련 키워드 추가
#     "PCA", "principal component", "dimensionality reduction",  # PCA 관련 키워드
#     "clustering", "k-means", "hierarchical clustering"  # 클러스터링 관련 키워드
# ]

# async def detect_data_analysis_question_keywords(message: str, tool_context: ToolContext) -> Dict[str, Any]:
#     """
#     Detect if the message is asking about data analysis topics (Keyword-based approach)
#     
#     Args:
#         message: User's message
#         tool_context: Tool context
#     
#     Returns:
#         Detection result with confidence score
#     """
#     message_lower = message.lower()
#     
#     # Check for data analysis keywords
#     found_keywords = []
#     for keyword in DATA_ANALYSIS_KEYWORDS:
#         if keyword in message_lower:
#             found_keywords.append(keyword)
#     
#     # Calculate confidence based on keyword matches
#     confidence = 0.0
#     if found_keywords:
#         # Base confidence from keyword matches
#         confidence = min(len(found_keywords) * 0.3, 1.0)
#         
#         # Boost confidence for specific question patterns
#         question_patterns = [
#             r"how to",
#             r"what is",
#             r"how do i",
#             r"best way to",
#             r"recommend",
#             r"tutorial",
#             r"guide",
#             r"learn"
#         ]
#         
#         for pattern in question_patterns:
#             if re.search(pattern, message_lower):
#                 confidence = min(confidence + 0.2, 1.0)
#                 break
#     
#     return {
#         "is_data_analysis_question": confidence > 0.3,
#         "confidence": confidence,
#         "found_keywords": found_keywords,
#         "message": message
#     }

# ============================================================================
# LLM-BASED DETECTION (Current implementation)
# ============================================================================

async def detect_data_analysis_question(message: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Detect if the message is asking about data analysis topics using LLM.
    
    Args:
        message: User's message
        tool_context: Tool context
    
    Returns:
        Detection result with confidence score
    """
    try:
        # Use OpenAI directly instead of Google ADK LiteLlm
        from openai import AsyncOpenAI
        
        # Initialize OpenAI client
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Create prompt for LLM-based detection
        detection_prompt = f"""You are an expert at classifying whether a user's question is related to data analysis, data science, machine learning, or related topics.

User's message: "{message}"

Determine if this message is asking about:
- Data analysis, data science, machine learning, deep learning, AI
- Statistics, analytics, modeling, prediction
- Data visualization, dashboards, reporting
- Data preprocessing, feature engineering, algorithms
- Python/R programming for data analysis
- Data formats (CSV, Excel, databases)
- Tutorial, guide, or advice about data analysis methods

Respond ONLY with a JSON object in this exact format:
{{
    "is_data_analysis_question": true or false,
    "confidence": 0.0 to 1.0,
    "reasoning": "brief explanation of why"
}}

Examples:
- "How to do data analysis?" -> {{"is_data_analysis_question": true, "confidence": 0.95, "reasoning": "direct question about data analysis"}}
- "What is sea level rise?" -> {{"is_data_analysis_question": false, "confidence": 0.1, "reasoning": "about geography/climate, not data analysis"}}
- "Tell me about pandas" -> {{"is_data_analysis_question": true, "confidence": 0.8, "reasoning": "pandas is a data analysis library"}}
- "Hello" -> {{"is_data_analysis_question": false, "confidence": 0.0, "reasoning": "greeting, no data analysis context"}}

JSON response:"""

        # Call OpenAI API directly
        response = await client.chat.completions.create(
            model=os.getenv("DATA_ANALYSIS_DETECTION_MODEL", "gpt-4o"),
            messages=[
                {"role": "user", "content": detection_prompt}
            ],
            temperature=0.1,
            response_format={"type": "json_object"}  # Force JSON response
        )
        
        # Extract response text
        response_text = response.choices[0].message.content.strip()
        
        # Try to parse JSON from response
        # Sometimes LLM adds extra text, so we try to extract JSON
        json_start = response_text.find('{')
        json_end = response_text.rfind('}') + 1
        
        if json_start >= 0 and json_end > json_start:
            json_text = response_text[json_start:json_end]
            result = json.loads(json_text)
            
            return {
                "is_data_analysis_question": result.get("is_data_analysis_question", False),
                "confidence": float(result.get("confidence", 0.0)),
                "reasoning": result.get("reasoning", ""),
                "message": message
            }
        else:
            # Fallback: if JSON parsing fails, try to extract boolean from text
            response_lower = response_text.lower()
            is_data_analysis = any(phrase in response_lower for phrase in [
                "true", "yes", "is a data analysis", "related to data"
            ])
            
            return {
                "is_data_analysis_question": is_data_analysis,
                "confidence": 0.7 if is_data_analysis else 0.3,
                "reasoning": "LLM response parsing fallback",
                "message": message
            }
            
    except Exception as e:
        print(f"❌ [DataAnalysisDetection] LLM detection error: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Fallback: return low confidence
        return {
            "is_data_analysis_question": False,
            "confidence": 0.0,
            "reasoning": f"Error during LLM detection: {str(e)}",
            "message": message
        }

async def search_data_analysis_info(query: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Search for data analysis information using web search
    
    Args:
        query: Search query
        tool_context: Tool context
    
    Returns:
        Search results and formatted information
    """
    print(f"🔍 [DataConsultantAgent] Searching for: {query}")
    
    # Perform web search
    search_results = await web_search_tool.search_data_analysis_topic(query)
    
    # Format results
    formatted_results = web_search_tool.format_search_results(search_results)
    source_links = web_search_tool.get_source_links(search_results)
    
    return {
        "search_results": search_results,
        "formatted_results": formatted_results,
        "source_links": source_links,
        "query": query
    }

async def generate_follow_up_suggestions(topic: str, tool_context: ToolContext) -> Dict[str, Any]:
    """
    Generate follow-up suggestions based on the data analysis topic
    
    Args:
        topic: Data analysis topic
        tool_context: Tool context
    
    Returns:
        Follow-up suggestions
    """
    # Common follow-up suggestions based on topic
    suggestions = []
    
    topic_lower = topic.lower()
    
    if any(keyword in topic_lower for keyword in ["machine learning", "ml", "algorithm"]):
        suggestions.extend([
            "Would you like to explore specific machine learning algorithms like random forest or neural networks?",
            "You might be interested in learning about model evaluation techniques and cross-validation.",
            "Consider learning about feature engineering and data preprocessing for better model performance."
        ])
    
    if any(keyword in topic_lower for keyword in ["data visualization", "visualization", "plot", "chart"]):
        suggestions.extend([
            "Would you like to learn about specific visualization libraries like matplotlib, seaborn, or plotly?",
            "You might be interested in creating interactive dashboards with tools like Streamlit or Dash.",
            "Consider exploring advanced visualization techniques for big data."
        ])
    
    if any(keyword in topic_lower for keyword in ["python", "pandas", "numpy"]):
        suggestions.extend([
            "Would you like to dive deeper into specific Python libraries for data analysis?",
            "You might be interested in learning about data manipulation and cleaning techniques.",
            "Consider exploring Jupyter notebooks for interactive data analysis."
        ])
    
    if any(keyword in topic_lower for keyword in ["statistics", "statistical", "hypothesis"]):
        suggestions.extend([
            "Would you like to learn about specific statistical tests and their applications?",
            "You might be interested in understanding probability distributions and sampling methods.",
            "Consider exploring Bayesian statistics and its applications in data science."
        ])
    
    if any(keyword in topic_lower for keyword in ["csv", "data", "dataset"]):
        suggestions.extend([
            "Would you like to learn about data cleaning and preprocessing techniques?",
            "You might be interested in exploring different data formats and their use cases.",
            "Consider learning about data quality assessment and validation methods."
        ])
    
    # Default suggestions if no specific topic matches
    if not suggestions:
        suggestions = [
            "Would you like to explore practical implementation examples?",
            "You might be interested in learning about related tools and technologies.",
            "Consider working on a hands-on project to apply these concepts."
        ]
    
    return {
        "suggestions": suggestions,
        "topic": topic
    }
