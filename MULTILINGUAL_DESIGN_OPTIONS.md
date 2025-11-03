# 다국어 지원을 위한 디자인 패턴 옵션

## 현재 상황 분석

현재 시스템은 영어로만 응답하며, 다음과 같은 특징이 있습니다:
- Google ADK 기반의 에이전트 시스템
- 프롬프트에 "Always respond in English" 명시적 지시
- Intent detection에는 한국어 키워드 포함 (해수면, 도시 등)
- 사용자 입력은 한국어/영어 모두 받지만 응답은 항상 영어

## 다국어 지원을 위한 디자인 패턴 옵션

### 옵션 1: Strategy Pattern + Language Detection Layer (추천)

**개요**: 언어별 처리 전략을 분리하고, 언어 감지 레이어를 추가하는 방식

**구조**:
```
User Message
    ↓
Language Detection Layer (자동 언어 감지)
    ↓
Language Strategy Selector (Factory Pattern)
    ↓
Language-Specific Prompt Strategy
    ↓
Agent (동일한 Agent, 다른 프롬프트)
```

**장점**:
- 언어별 로직이 명확히 분리됨
- 새로운 언어 추가 시 Strategy만 추가하면 됨
- 기존 Agent 로직은 변경 없음
- Language Matcher와 유사한 패턴으로 일관성 유지

**구현 포인트**:
1. `LanguageDetectionStrategy`: 사용자 메시지 언어 감지 (Google Cloud Translation API, 또는 LLM 기반)
2. `PromptLocalizationStrategy`: 언어별 프롬프트 생성
3. `ResponseLocalizationStrategy`: 에이전트 응답 번역/로컬라이제이션

**예시 구조**:
```
adk_geospatial_agents/
└── shared/
    └── i18n/
        ├── __init__.py
        ├── language_detector.py      # 언어 감지
        ├── prompt_localizer.py       # 프롬프트 로컬라이제이션
        ├── response_localizer.py     # 응답 로컬라이제이션
        └── strategies/
            ├── english_strategy.py
            ├── korean_strategy.py
            └── base_strategy.py
```

**적용 위치**:
- `main_agent/agent.py`의 `process_user_message()` 시작 부분에 언어 감지 추가
- `main_agent/prompts.py`에 언어별 프롬프트 전략 적용
- 각 에이전트의 `prompts.py`에도 동일 패턴 적용

---

### 옵션 2: Decorator Pattern (Agent Wrapper)

**개요**: 기존 에이전트를 다국어 지원 데코레이터로 감싸는 방식

**구조**:
```
MultilingualAgentDecorator
    ↓ (언어 감지 및 프롬프트 변환)
Base Agent (기존 Agent)
    ↓
Response Localizer (응답 번역)
    ↓
Localized Response
```

**장점**:
- 기존 Agent 코드 변경 최소화
- 데코레이터로 동적으로 기능 추가
- 테스트 및 디버깅 용이

**구현 포인트**:
1. `MultilingualDecorator` 클래스가 Agent를 감싸서:
   - 입력 메시지 언어 감지
   - 프롬프트에 언어 지시 추가
   - 응답 번역/로컬라이제이션

**예시 구조**:
```
adk_geospatial_agents/
└── shared/
    └── decorators/
        ├── __init__.py
        ├── multilingual_decorator.py
        └── language_aware_agent.py
```

**적용 위치**:
- `main_agent/agent.py`에서 Agent 생성 시 데코레이터 적용
- `adk_chat.py`에서 에이전트 호출 전 래핑

---

### 옵션 3: Factory Pattern + Resource Bundle Pattern

**개요**: 언어별 프롬프트를 리소스 번들로 관리하고 팩토리로 생성

**구조**:
```
User Message
    ↓
Language Detector
    ↓
Prompt Factory (선택된 언어의 리소스 번들 사용)
    ↓
Agent (동일)
```

**장점**:
- 프롬프트 관리가 체계적
- 번역 작업이 명확함
- 확장성 좋음

**구현 포인트**:
1. 언어별 리소스 파일 (YAML/JSON):
   ```
   resources/
   ├── en/
   │   ├── prompts.yaml
   │   └── messages.yaml
   └── ko/
       ├── prompts.yaml
       └── messages.yaml
   ```

2. `PromptFactory` 클래스:
   - 언어 코드에 따라 적절한 리소스 로드
   - 프롬프트 템플릿에 변수 삽입

**예시 구조**:
```
backend/
└── app/
    └── resources/
        ├── en/
        │   ├── prompts.yaml
        │   └── messages.yaml
        └── ko/
            ├── prompts.yaml
            └── messages.yaml
adk_geospatial_agents/
└── shared/
    └── i18n/
        ├── prompt_factory.py
        └── resource_loader.py
```

**리소스 파일 예시**:
```yaml
# resources/ko/prompts.yaml
main_agent_instruction: |
  당신은 DataGround 지리공간 분석 시스템의 메인 코디네이터입니다.
  
  주요 역할:
  1. 사용자 요청을 분석하고 의도를 식별합니다
  2. 적절한 전문 에이전트에게 작업을 위임합니다
  ...
  
welcome_message: |
  안녕하세요! DataGround 지리공간 분석 시스템입니다.
  어떤 분석을 도와드릴까요?
  
supported_analyses:
  - 해수면 상승 위험 분석
  - 도시 지역 분석
  ...
```

---

### 옵션 4: Context-Based Language Preference (가장 실용적)

**개요**: 사용자 컨텍스트에 언어 선호도 저장하고, 세션 전체에서 일관되게 사용

**구조**:
```
User Context (DB/Session)
    ↓ (언어 선호도 저장)
Language Context Manager
    ↓
Language-Aware Prompt Generator
    ↓
Agent (프롬프트에 언어 지시 포함)
```

**장점**:
- 사용자별 언어 설정 유지
- 세션 간 일관성 보장
- 구현이 비교적 단순

**구현 포인트**:
1. 사용자 모델에 `preferred_language` 필드 추가
2. 첫 메시지에서 언어 감지 후 저장
3. 이후 세션에서는 저장된 언어 사용
4. 프롬프트 생성 시 언어 코드 포함

**프롬프트 예시**:
```python
def get_main_agent_instruction(language: str = "en") -> str:
    if language == "ko":
        return """
        당신은 DataGround 지리공간 분석 시스템의 메인 코디네이터입니다.
        항상 한국어로 응답해주세요.
        ...
        """
    else:
        return """
        You are the main coordinator of the DataGround geospatial analysis system.
        Always respond in English.
        ...
        """
```

**적용 위치**:
- `models.py`에 User 모델에 `preferred_language` 필드 추가
- `adk_chat.py`에서 첫 메시지 언어 감지 및 저장
- `main_agent/agent.py`에서 `callback_context`에서 언어 정보 읽기
- 모든 `prompts.py`에 언어 파라미터 추가

---

### 옵션 5: LLM Native Multilingual Support (간단하지만 제한적)

**개요**: Gemini 모델의 내장 다국어 능력을 활용, 프롬프트만 수정

**구조**:
```
User Message (언어 자동 감지)
    ↓
Enhanced Prompt (언어 자동 감지 지시 포함)
    ↓
Agent (LLM이 자동으로 언어 매칭)
```

**장점**:
- 구현이 가장 간단
- 추가 코드 최소화
- LLM의 자연스러운 언어 처리 활용

**단점**:
- 언어 일관성 보장 어려움
- 특정 용어 번역 정확도 제어 어려움

**프롬프트 수정 예시**:
```python
def get_main_agent_instruction() -> str:
    return """
    You are the main coordinator of the DataGround geospatial analysis system.
    
    IMPORTANT: Detect the user's language from their messages and always respond 
    in the same language. If the user writes in Korean, respond in Korean. 
    If the user writes in English, respond in English.
    
    Key roles:
    1. Analyze user requests and identify intent
    ...
    """
```

---

## 비교 및 추천

| 옵션 | 구현 복잡도 | 확장성 | 유지보수성 | 성능 | 추천도 |
|------|------------|--------|-----------|------|--------|
| 옵션 1 (Strategy) | 중간 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 옵션 2 (Decorator) | 낮음 | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 옵션 3 (Factory+Bundle) | 높음 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 옵션 4 (Context-Based) | 중간 | ⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| 옵션 5 (LLM Native) | 매우 낮음 | ⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ |

## 단계별 구현 추천 (옵션 1 + 옵션 4 하이브리드)

### Phase 1: 기본 언어 감지 (옵션 5로 시작)
- 프롬프트에 언어 자동 감지 지시 추가
- 빠르게 다국어 지원 시작

### Phase 2: Context 기반 언어 저장 (옵션 4)
- 사용자 언어 선호도 DB 저장
- 세션 간 일관성 확보

### Phase 3: Strategy Pattern 적용 (옵션 1)
- 언어별 전략 분리
- 프롬프트 품질 향상

### Phase 4: Resource Bundle 도입 (옵션 3)
- 리소스 파일로 프롬프트 관리
- 번역 관리 체계화

## 주요 고려사항

### 1. 언어 감지 방법
- **LLM 기반**: 프롬프트에 "Detect language" 지시
- **라이브러리**: `langdetect`, `polyglot` 등
- **API**: Google Cloud Translation API

### 2. 번역 전략
- **실시간 번역**: 각 응답마다 번역 (성능 이슈 가능)
- **프롬프트 번역**: 프롬프트만 번역, 응답은 LLM이 생성 (추천)
- **하이브리드**: 중요 메시지는 사전 번역, 동적 내용은 LLM 생성

### 3. 용어 일관성
- 지리공간 전문 용어 사전 구축
- "sea level rise" → "해수면 상승" 매핑
- 고유명사 보존 전략

### 4. 사용자 경험
- 언어 전환 명령 (`/lang ko`, `/lang en`)
- 언어 자동 감지 옵션
- 언어 설정 UI

## 구현 예시 (옵션 4 기반)

### 1. 모델 확장
```python
# models.py
class User(Base):
    ...
    preferred_language = Column(String, default="en")  # 'en', 'ko', 'auto'
```

### 2. 언어 감지 유틸리티
```python
# shared/utils/language_detector.py
async def detect_language(message: str) -> str:
    """Detect language from message"""
    # 간단한 휴리스틱 또는 LLM 기반
    korean_pattern = re.compile(r'[가-힣]')
    if korean_pattern.search(message):
        return "ko"
    return "en"
```

### 3. 프롬프트 수정
```python
# main_agent/prompts.py
def get_main_agent_instruction(language: str = "en") -> str:
    if language == "ko":
        return """
        당신은 DataGround 지리공간 분석 시스템의 메인 코디네이터입니다.
        항상 한국어로 친절하고 명확하게 응답해주세요.
        ...
        """
    else:
        return """
        You are the main coordinator of the DataGround geospatial analysis system.
        Always respond in English in a friendly and clear manner.
        ...
        """
```

### 4. Agent 호출 시 언어 전달
```python
# main_agent/agent.py
async def process_user_message(message: str, user_id: int, callback_context: CallbackContext) -> Dict[str, Any]:
    # 언어 감지 또는 사용자 설정 가져오기
    user_language = callback_context.state.get("user_language", "en")
    
    # Agent instruction에 언어 포함
    main_agent.instruction = get_main_agent_instruction(user_language)
    ...
```

## 결론

**즉시 적용 가능**: 옵션 5 (LLM Native)로 시작하여 빠르게 다국어 지원 시작

**장기적 권장**: 옵션 1 (Strategy) + 옵션 4 (Context-Based) 하이브리드로 발전

**핵심 포인트**:
1. 사용자 언어 선호도 저장 (DB)
2. 프롬프트에 언어별 버전 생성
3. 언어 감지 로직 중앙화
4. 점진적 확장 (Phase별 구현)

