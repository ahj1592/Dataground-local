# GPT를 사용한 다국어 지원 가이드

## 답변: 네, 가능합니다! ✅

**GPT 모델은 다국어 지원이 뛰어나며, ChatGPT처럼 사용자가 어떤 언어로 대화하면 그 언어로 자동 응답합니다.**

## 현재 상황

- **Data Consultant Agent**: 이미 `openai/gpt-4o` 사용 중
- **다른 에이전트들**: `gemini-2.0-flash-exp` 사용 중
- **프롬프트**: Data Consultant Agent에만 "Always respond in English" 명시

## 구현 방법

### 1단계: 모든 에이전트를 GPT로 변경

#### 1.1 Main Agent 변경

**파일**: `backend/app/adk_geospatial_agents/main_agent/agent.py`

**변경 전**:
```python
from google.adk.agents import Agent
from google.genai import types

main_agent = Agent(
    model=os.getenv("MAIN_AGENT_MODEL", "gemini-2.0-flash-exp"),
    ...
)
```

**변경 후**:
```python
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

main_agent = LlmAgent(
    model=LiteLlm(model=os.getenv("MAIN_AGENT_MODEL", "openai/gpt-4o")),
    ...
)
```

#### 1.2 전문 에이전트들 변경

**파일들**:
- `backend/app/adk_geospatial_agents/sea_level_agent/agent.py`
- `backend/app/adk_geospatial_agents/urban_agent/agent.py`
- `backend/app/adk_geospatial_agents/infrastructure_agent/agent.py`
- `backend/app/adk_geospatial_agents/topic_modeling_agent/agent.py`

**모두 동일하게 변경**:
```python
# 변경 전
from google.adk.agents import Agent
from google.genai import types

sea_level_agent = Agent(
    model=os.getenv("SEA_LEVEL_AGENT_MODEL", "gemini-2.0-flash-exp"),
    ...
)

# 변경 후
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from google.genai import types

sea_level_agent = LlmAgent(
    model=LiteLlm(model=os.getenv("SEA_LEVEL_AGENT_MODEL", "openai/gpt-4o")),
    ...
)
```

### 2단계: 프롬프트에 자동 언어 매칭 지시 추가

#### 2.1 Main Agent 프롬프트 수정

**파일**: `backend/app/adk_geospatial_agents/main_agent/prompts.py`

**변경 전**:
```python
def get_main_agent_instruction() -> str:
    return """
    You are the main coordinator of the DataGround geospatial analysis system.
    ...
    Always respond to users in a friendly and clear manner.
    """
```

**변경 후**:
```python
def get_main_agent_instruction() -> str:
    return """
    You are the main coordinator of the DataGround geospatial analysis system.
    
    IMPORTANT LANGUAGE INSTRUCTION:
    - Detect the language of the user's message automatically
    - Always respond in the SAME LANGUAGE as the user's message
    - If the user writes in Korean (한국어), respond in Korean
    - If the user writes in English, respond in English
    - If the user switches languages, immediately match their new language
    - Be natural and fluent in the language you're using
    
    Key roles:
    1. Analyze user requests and identify intent
    2. Delegate tasks to appropriate specialized agents
    3. Manage parameter collection status
    4. Integrate analysis results and deliver to users
    
    Supported analysis types:
    - sea_level_rise: Sea level rise risk analysis
    - urban_analysis: Urban area analysis
    - infrastructure_analysis: Infrastructure exposure analysis
    - topic_modeling: Topic modeling analysis
    
    Workflow:
    1. Detect analysis intent from user messages
    2. Collect necessary parameters (year, threshold, city/country)
    3. Request user confirmation when parameters are complete
    4. Delegate analysis to appropriate specialized agent after confirmation
    5. Deliver results to users
    
    Parameter collection rules:
    - Request only one parameter at a time
    - Display collected information with confirmation messages each time
    - Request final confirmation when all parameters are collected
    - Start over from the beginning if user rejects
    
    Always respond to users in a friendly and clear manner, using the same language as their message.
    """
```

#### 2.2 Data Consultant Agent 프롬프트 수정

**파일**: `backend/app/adk_geospatial_agents/data_consultant_agent/prompts.py`

**변경 전**:
```python
def get_data_consultant_agent_instruction() -> str:
    return """You are a DataConsultantAgent, an expert in data analysis...
    
    Guidelines:
    - Always respond in English
    ...
    """
```

**변경 후**:
```python
def get_data_consultant_agent_instruction() -> str:
    return """You are a DataConsultantAgent, an expert in data analysis, data science, machine learning, and related fields.
    
    IMPORTANT LANGUAGE INSTRUCTION:
    - Detect the language of the user's message automatically
    - Always respond in the SAME LANGUAGE as the user's message
    - If the user writes in Korean (한국어), respond in Korean
    - If the user writes in English, respond in English
    - Be natural and fluent in the language you're using
    
    Your role is to:
    1. Provide expert advice and guidance on data analysis topics
    2. Answer questions about data science methodologies, tools, and best practices
    3. Offer practical recommendations and next steps
    4. Always search the web for current information to provide up-to-date answers
    5. Include source links in your responses
    6. Suggest follow-up questions and related topics
    
    Guidelines:
    - Provide comprehensive and accurate information
    - Include practical examples when relevant
    - Suggest next steps or related topics at the end
    - Be helpful and encouraging
    - Focus on actionable advice
    
    ...
    """
```

#### 2.3 전문 에이전트 프롬프트 수정

**각 전문 에이전트의 프롬프트 파일들도 동일하게 수정**:
- `sea_level_agent/prompts.py`
- `urban_agent/prompts.py`
- `infrastructure_agent/prompts.py`
- `topic_modeling_agent/prompts.py`

**각 프롬프트 시작 부분에 추가**:
```python
def get_sea_level_agent_instruction() -> str:
    return """
    IMPORTANT LANGUAGE INSTRUCTION:
    - Detect the language of the user's message automatically
    - Always respond in the SAME LANGUAGE as the user's message
    - If the user writes in Korean (한국어), respond in Korean
    - If the user writes in English, respond in English
    - Be natural and fluent in the language you're using
    
    You are a specialized sea level rise risk analysis agent.
    ...
    """
```

### 3단계: 전역 프롬프트도 수정

**파일**: `backend/app/adk_geospatial_agents/main_agent/prompts.py`

**변경 후**:
```python
def get_global_instruction() -> str:
    return """
    You are the DataGround geospatial analysis AI assistant.
    You provide advanced geospatial analysis using Google Earth Engine.
    
    IMPORTANT: Always match the user's language. If they write in Korean, respond in Korean. 
    If they write in English, respond in English.
    
    Supported features:
    - Sea level rise risk analysis
    - Urban area change analysis
    - Infrastructure exposure analysis
    - Topic modeling analysis
    
    You collect necessary information through conversations with users
    and collaborate with specialized agents to provide accurate analysis.
    """
```

## 환경 변수 설정 (선택사항)

각 에이전트의 모델을 환경 변수로 제어할 수 있습니다:

```bash
# .env 파일 또는 환경 변수
MAIN_AGENT_MODEL=openai/gpt-4o
SEA_LEVEL_AGENT_MODEL=openai/gpt-4o
URBAN_AGENT_MODEL=openai/gpt-4o
INFRASTRUCTURE_AGENT_MODEL=openai/gpt-4o
TOPIC_MODELING_AGENT_MODEL=openai/gpt-4o
```

**모델 옵션**:
- `openai/gpt-4o` - 최신 GPT-4o (권장)
- `openai/gpt-4-turbo` - GPT-4 Turbo
- `openai/gpt-3.5-turbo` - 더 빠르고 저렴하지만 성능 낮음

## 작동 원리

1. **사용자가 한국어로 메시지 입력**: "해수면 상승 분석을 해주세요"
2. **GPT가 자동으로 언어 감지**: 한국어로 인식
3. **프롬프트에 언어 매칭 지시 포함**: "Always respond in the SAME LANGUAGE"
4. **GPT가 한국어로 응답**: "네, 해수면 상승 분석을 도와드리겠습니다. 어떤 연도를 분석하시겠어요?"
5. **사용자가 영어로 전환**: "Let me check 2020"
6. **GPT가 자동으로 영어로 전환**: "Sure! I'll analyze sea level rise for 2020. Which city would you like to analyze?"

## 장점

✅ **자동 언어 감지**: 별도의 언어 감지 라이브러리 불필요  
✅ **자연스러운 대화**: ChatGPT처럼 자연스러운 언어 전환  
✅ **구현 간단**: 프롬프트만 수정하면 됨  
✅ **확장 용이**: 새로운 언어 자동 지원  

## 주의사항

⚠️ **비용**: GPT-4o는 Gemini보다 비용이 높을 수 있음  
⚠️ **응답 속도**: GPT-4o는 Gemini Flash보다 다소 느릴 수 있음  
⚠️ **일관성**: 가끔 언어 전환이 늦을 수 있음 (프롬프트 강화로 해결 가능)

## 테스트 방법

1. 한국어로 메시지 보내기: "안녕하세요, 해수면 상승 분석을 원합니다"
   → 한국어로 응답해야 함

2. 영어로 메시지 보내기: "Hello, I want sea level rise analysis"
   → 영어로 응답해야 함

3. 언어 전환 테스트:
   - 한국어로 시작 → 영어로 전환 → 한국어로 다시 전환
   - 각 단계에서 언어가 일치해야 함

## 최종 체크리스트

- [ ] 모든 에이전트를 `LlmAgent`와 `LiteLlm`으로 변경
- [ ] 모든 프롬프트에 자동 언어 매칭 지시 추가
- [ ] "Always respond in English" 제거
- [ ] 환경 변수 설정 (선택사항)
- [ ] 테스트: 한국어/영어 각각 테스트
- [ ] 테스트: 언어 전환 테스트

## 결론

**GPT를 사용하면 ChatGPT처럼 자동 언어 매칭이 가능합니다!**  
프롬프트만 적절히 수정하면 별도의 언어 감지 시스템 없이도 다국어 지원이 가능합니다.

