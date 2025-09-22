# Enhanced DataGround Agent System

Google ADK와 LangChain을 활용한 고성능 LLM chatbot 시스템으로, 지리 데이터 분석을 위한 4개의 전문 agent로 구성되어 있습니다.

## 🏗️ 아키텍처 개요

### 4개의 전문 Agent

1. **Intent Classification Agent** (`intent_classification_agent.py`)
   - 사용자 메시지의 의도를 분석하고 분석 유형을 분류
   - 자연어 처리로 지리 데이터 분석 요청인지 판단
   - 누락된 정보 식별 및 명확화 질문 생성

2. **Parameter Extraction Agent** (`parameter_extraction_agent.py`)
   - 사용자 메시지에서 분석에 필요한 매개변수 추출
   - 연도, 도시명, 임계값, 좌표 등 자동 추출
   - 매개변수 검증 및 기본값 설정

3. **Analysis Execution Agent** (`analysis_execution_agent.py`)
   - Google Earth Engine API 호출 및 분석 수행
   - 해수면 상승, 도시 분석, 인프라 분석 등 실행
   - 오류 처리 및 재시도 메커니즘

4. **Dashboard Integration Agent** (`dashboard_integration_agent.py`)
   - 분석 결과를 대시보드에 자동 표시
   - 프론트엔드 컴포넌트 업데이트
   - 실시간 시각화 및 알림

### LangChain 통합

- **GeospatialAnalysisTool**: 지리 공간 분석 도구
- **TopicModelingTool**: 토픽 모델링 도구
- **DataValidationTool**: 데이터 검증 도구
- **ConversationBufferMemory**: 대화 메모리 관리

## 🚀 주요 기능

### 1. 지능형 의도 분류
- 사용자 메시지를 분석하여 분석 유형 자동 식별
- 해수면 상승, 도시 분석, 인프라 분석, 인구 노출, 토픽 모델링 지원
- 신뢰도 기반 분류 및 명확화 질문 생성

### 2. 자동 매개변수 추출
- 정규식과 LLM을 결합한 고정밀 매개변수 추출
- 연도, 임계값, 도시명, 좌표 등 자동 인식
- 매개변수 검증 및 기본값 설정

### 3. 실시간 분석 실행
- Google Earth Engine API 자동 호출
- 다중 분석 유형 지원
- 오류 처리 및 재시도 메커니즘

### 4. 대시보드 자동 업데이트
- 분석 결과를 대시보드에 실시간 표시
- 맵, 차트, 테이블 자동 업데이트
- 사용자 인터페이스 동기화

### 5. LangChain 도구 통합
- 고급 자연어 처리 기능
- 대화 메모리 관리
- 도구 기반 분석 실행

## 📊 지원하는 분석 유형

### 1. 해수면 상승 위험 분석 (Sea Level Rise Risk)
- **필수 매개변수**: year, threshold
- **선택 매개변수**: city_name, coordinates
- **기능**: 해수면 상승 위험 지역 식별 및 인구 노출 분석

### 2. 도시 개발 분석 (Urban Development Analysis)
- **필수 매개변수**: year
- **선택 매개변수**: start_year, end_year, city_name, coordinates
- **기능**: 도시화 추이, 도시 확장, 도시 지역 통계

### 3. 인프라 노출 분석 (Infrastructure Exposure Analysis)
- **필수 매개변수**: year, threshold
- **선택 매개변수**: city_name, coordinates
- **기능**: 중요 인프라의 해수면 상승 위험 평가

### 4. 인구 노출 분석 (Population Exposure Analysis)
- **필수 매개변수**: year, threshold
- **선택 매개변수**: start_year, end_year, city_name, coordinates
- **기능**: 인구의 해수면 상승 노출도 분석

### 5. 토픽 모델링 (Topic Modeling)
- **필수 매개변수**: text_input
- **선택 매개변수**: method, n_topics
- **기능**: 텍스트 분석 및 토픽 모델링

## 🛠️ 설치 및 설정

### 1. 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정
```bash
# .env 파일 생성
OPENAI_API_KEY=your_openai_api_key_here
```

### 3. 서버 실행
```bash
python start_server.py
```

## 🧪 테스트

### Agent 테스트 실행
```bash
cd backend
python test_agents.py
```

### API 테스트
```bash
# Agent 상태 확인
curl http://localhost:8000/agent/status

# 분석 기능 목록
curl http://localhost:8000/agent/capabilities

# LangChain 도구 목록
curl http://localhost:8000/agent/langchain/tools

# 헬스 체크
curl http://localhost:8000/agent/health
```

## 📡 API 엔드포인트

### Agent 관리
- `GET /agent/status` - Agent 상태 조회
- `GET /agent/capabilities` - 분석 기능 목록
- `GET /agent/health` - 헬스 체크

### LangChain 도구
- `GET /agent/langchain/tools` - LangChain 도구 목록
- `GET /agent/langchain/memory` - 메모리 상태 조회
- `DELETE /agent/langchain/memory` - 메모리 초기화

### 대화 관리
- `GET /agent/conversation/history` - 대화 히스토리 조회
- `DELETE /agent/conversation/history` - 대화 히스토리 삭제

### 대시보드 관리
- `GET /agent/dashboard/state` - 대시보드 상태 조회
- `POST /agent/dashboard/clear-queue` - 업데이트 큐 초기화

## 💡 사용 예시

### 1. 기본 분석 요청
```
사용자: "Show me sea level rise risk for Jakarta in 2020"
Agent: 
1. 의도 분류: sea_level_rise
2. 매개변수 추출: year=2020, threshold=2.0 (기본값)
3. 분석 실행: GEE API 호출
4. 대시보드 업데이트: 맵 및 차트 표시
5. 응답: "해수면 상승 위험 분석이 완료되었습니다..."
```

### 2. 명확화 요청
```
사용자: "Analyze urban development"
Agent: 
1. 의도 분류: urban_analysis
2. 매개변수 추출: year 누락
3. 명확화 질문: "What year would you like to analyze?"
```

### 3. 복합 분석 요청
```
사용자: "Show me comprehensive urban analysis from 2015 to 2020 with 2.5m threshold"
Agent:
1. 의도 분류: urban_analysis
2. 매개변수 추출: start_year=2015, end_year=2020, threshold=2.5
3. 분석 실행: 종합 도시 분석
4. 대시보드 업데이트: 시계열 차트 및 맵 표시
```

## 🔧 성능 최적화

### 1. 매개변수 캐싱
- 자주 사용되는 매개변수 조합 캐싱
- 사용자별 기본 설정 저장

### 2. 비동기 처리
- 분석 실행과 대시보드 업데이트 비동기 처리
- 사용자 응답과 백그라운드 작업 분리

### 3. 오류 처리
- 재시도 메커니즘으로 일시적 오류 처리
- 사용자 친화적 오류 메시지

### 4. 메모리 관리
- 대화 히스토리 자동 정리
- LangChain 메모리 최적화

## 🚀 향후 개선 사항

### 1. 추가 분석 유형
- 기후 변화 분석
- 토지 이용 변화 분석
- 환경 지표 분석

### 2. 고급 기능
- 다국어 지원
- 음성 인터페이스
- 모바일 최적화

### 3. 성능 향상
- GPU 가속 분석
- 분산 처리
- 실시간 스트리밍

## 📞 지원

문제가 발생하거나 기능 요청이 있으시면 이슈를 생성해 주세요.

---

**Enhanced DataGround Agent System** - 지리 데이터 분석을 위한 차세대 AI 어시스턴트
