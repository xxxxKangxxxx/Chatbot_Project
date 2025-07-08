# 고령층 개인화 챗봇 API 백엔드

RAG + GPT 기반 고령층 정서 지원 챗봇 서비스의 FastAPI 백엔드입니다.

## 🚀 주요 기능

- **🤖 개인화된 대화 생성**: RAG + GPT-4 기반 맞춤형 대화
- **😊 실시간 감정 분석**: 대화 내용의 감정 분석 및 트렌드 파악
- **📅 통합 일정 관리**: 약물, 병원, 운동, 취미 등 모든 일정 관리
- **🎯 관심사 기반 추천**: 사용자 관심사 분석 및 맞춤 컨텐츠 추천
- **👤 사용자 프로필 분석**: 개인화를 위한 사용자 특성 분석

## 🛠 기술 스택

- **백엔드**: FastAPI + SQLAlchemy + MySQL
- **벡터 DB**: Qdrant (벡터 검색)
- **AI 모델**: OpenAI GPT-4, text-embedding-3-small
- **아키텍처**: RAG (Retrieval-Augmented Generation)

## 📦 설치 및 설정

### 1. 의존성 설치

```bash
cd backend
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 설정을 추가하세요:

```bash
# 데이터베이스 설정
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=chatbot_user
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=chatbot_service

# Qdrant 설정
QDRANT_HOST=localhost
QDRANT_PORT=6333

# OpenAI API 설정
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4
OPENAI_EMBEDDING_MODEL=text-embedding-3-small

# 보안 설정
SECRET_KEY=your_secret_key_here

# 애플리케이션 설정
DEBUG=true
HOST=0.0.0.0
PORT=8000
```

### 3. 데이터베이스 설정

MySQL 데이터베이스와 사용자를 생성하세요:

```sql
CREATE DATABASE chatbot_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'chatbot_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON chatbot_service.* TO 'chatbot_user'@'localhost';
FLUSH PRIVILEGES;
```

### 4. Qdrant 설정

Docker로 Qdrant를 실행하세요:

```bash
docker run -p 6333:6333 qdrant/qdrant
```

## 🎯 서버 실행

### 개발 서버 (권장)

```bash
cd backend
python start_dev.py
```

### 직접 실행

```bash
cd backend
python -m app.main
```

### uvicorn으로 실행

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📋 API 문서

서버 실행 후 다음 주소에서 API 문서를 확인할 수 있습니다:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **서비스 정보**: http://localhost:8000/
- **헬스 체크**: http://localhost:8000/health

## 🔌 API 엔드포인트

### 채팅 관련 (`/api/v1/chat`)
- `POST /chat` - 메시지 전송 및 응답 생성
- `GET /chat/history/{user_id}` - 채팅 기록 조회
- `DELETE /chat/session/{session_id}` - 세션 삭제
- `GET /chat/stats/{user_id}` - 채팅 통계

### 사용자 관련 (`/api/v1/users`)
- `POST /users` - 사용자 등록
- `GET /users/{user_id}` - 사용자 조회
- `PUT /users/{user_id}` - 사용자 정보 수정
- `GET /users/{user_id}/profile` - 프로필 분석

### 감정 관련 (`/api/v1/emotions`)
- `GET /emotions/{user_id}/analysis` - 감정 분석 결과
- `GET /emotions/{user_id}/trends` - 감정 트렌드
- `GET /emotions/{user_id}/summary` - 감정 요약

### 일정 관리 (`/api/v1/schedules`)
- `POST /schedules` - 일정 생성
- `GET /schedules/{user_id}` - 사용자 일정 조회
- `PUT /schedules/{schedule_id}` - 일정 수정
- `DELETE /schedules/{schedule_id}` - 일정 삭제

### 관심사 관련 (`/api/v1/interests`)
- `GET /interests/{user_id}/analysis` - 관심사 분석
- `GET /interests/{user_id}/recommendations` - 추천 컨텐츠
- `POST /interests/{user_id}/feedback` - 추천 피드백

## 🏗 프로젝트 구조

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI 메인 애플리케이션
│   ├── config.py            # 설정 관리
│   ├── database.py          # 데이터베이스 연결
│   ├── qdrant_client.py     # Qdrant 클라이언트
│   │
│   ├── models/              # SQLAlchemy 모델
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── emotion.py
│   │   ├── schedule.py
│   │   └── interest.py
│   │
│   ├── schemas/             # Pydantic 스키마
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── emotion.py
│   │   ├── schedule.py
│   │   └── interest.py
│   │
│   ├── crud/                # CRUD 연산
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── chat.py
│   │   ├── emotion.py
│   │   ├── schedule.py
│   │   └── interest.py
│   │
│   ├── services/            # 비즈니스 로직
│   │   ├── __init__.py
│   │   ├── gpt_service.py
│   │   ├── embedding_service.py
│   │   ├── qdrant_service.py
│   │   ├── emotion_service.py
│   │   └── user_profile_service.py
│   │
│   └── api/                 # API 라우터
│       ├── __init__.py
│       ├── chat.py
│       ├── user.py
│       ├── emotion.py
│       ├── schedule.py
│       └── interest.py
│
├── start_dev.py             # 개발 서버 시작 스크립트
├── requirements.txt         # 의존성 목록
└── README.md               # 이 파일
```

## 🔧 개발 가이드

### 로깅

애플리케이션은 다음 위치에 로그를 기록합니다:
- 콘솔 출력
- `logs/app.log` 파일

### 환경별 설정

`ENVIRONMENT` 환경 변수로 설정을 변경할 수 있습니다:
- `development` (기본): 개발 환경
- `production`: 프로덕션 환경  
- `test`: 테스트 환경

### 에러 처리

모든 API 엔드포인트는 표준화된 에러 응답을 반환합니다:

```json
{
  "success": false,
  "error_code": "ERROR_TYPE",
  "error_message": "에러 메시지",
  "path": "/api/endpoint",
  "method": "POST",
  "timestamp": 1640995200.0
}
```

## 🚨 문제 해결

### 자주 발생하는 문제

1. **데이터베이스 연결 실패**
   - MySQL 서버 실행 상태 확인
   - 연결 정보 (.env 파일) 확인
   - 방화벽/포트 설정 확인

2. **Qdrant 연결 실패**
   - Qdrant 서버 실행 상태 확인
   - 포트 6333 사용 가능 여부 확인

3. **OpenAI API 에러**
   - API 키 유효성 확인
   - 사용량 한도 확인
   - 네트워크 연결 상태 확인

### 로그 확인

```bash
# 실시간 로그 확인
tail -f logs/app.log

# 에러 로그만 확인
grep "ERROR" logs/app.log
```

## 🤝 기여하기

1. 이슈 생성 및 토론
2. 브랜치 생성 (`git checkout -b feature/새기능`)
3. 변경사항 커밋 (`git commit -am '새 기능 추가'`)
4. 브랜치 푸시 (`git push origin feature/새기능`)
5. Pull Request 생성

## 📄 라이센스

MIT License

---

**고령층 개인화 챗봇 API v1.0.0**  
*RAG + GPT 기반 정서 지원 서비스* 