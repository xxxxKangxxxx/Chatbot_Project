# 🤖 고령층을 위한 AI 챗봇 서비스

> **KDT 부트캠프 프로젝트** - 고령층의 정서적 지원과 일상 관리를 위한 AI 기반 대화형 챗봇

## 📋 프로젝트 개요

이 프로젝트는 고령층을 대상으로 한 **AI 기반 대화형 챗봇 서비스**입니다. 
외로움 해소, 감정 관리, 일상 대화, 건강 관리 등을 통해 고령층의 삶의 질 향상을 목표로 합니다.

### 🎯 주요 목표
- 고령층의 **외로움과 고립감 해소**
- **자연스러운 한국어 대화** 제공
- **감정 상태 분석** 및 맞춤형 응답
- **개인화된 대화 경험** 제공
- **접근성이 높은 UI/UX** 구현

## ✨ 주요 기능

### 🗣️ 대화 기능
- **자연스러운 한국어 대화**: Gemini 2.0 Flash 모델 기반
- **감정 인식 및 분석**: 사용자의 감정 상태 파악
- **개인화된 응답**: 사용자 프로필 기반 맞춤 대화
- **대화 기록 관리**: 세션별 대화 이력 저장

### 👤 사용자 관리
- **사용자 프로필 관리**: 개인 정보, 선호도, 관심사
- **감정 기록 추적**: 시간별/일별 감정 변화 모니터링
- **관심사 기반 추천**: 취미, 건강 관련 대화 유도

### 📊 분석 및 리포팅
- **대화 패턴 분석**: 사용 빈도, 선호 주제 분석
- **감정 트렌드 분석**: 장기적 감정 변화 추적
- **활동 통계**: 일/주/월별 사용 현황

## 🏗️ 기술 스택

### Backend
- **Framework**: FastAPI (Python 3.13)
- **AI Model**: Google Gemini 2.0 Flash *(무료)*
- **Embedding**: Gemini text-embedding-004 (768차원)
- **Database**: MySQL 8.0
- **Vector DB**: Qdrant *(선택적)*
- **ORM**: SQLAlchemy 2.0 (비동기)

### Frontend *(예정)*
- **Framework**: React.js / Next.js
- **Styling**: Tailwind CSS
- **State Management**: Context API / Zustand

### Infrastructure
- **Environment**: Python Virtual Environment
- **Configuration**: python-dotenv
- **Logging**: Python logging
- **API Documentation**: FastAPI Swagger

## 📁 프로젝트 구조

```
chatbot_project/
├── backend/                    # 백엔드 API 서버
│   ├── app/
│   │   ├── api/               # API 라우터
│   │   │   ├── chat.py        # 대화 API
│   │   │   ├── user.py        # 사용자 관리 API
│   │   │   ├── emotion.py     # 감정 분석 API
│   │   │   ├── schedule.py    # 일정 관리 API
│   │   │   └── interest.py    # 관심사 관리 API
│   │   ├── services/          # 비즈니스 로직
│   │   │   ├── gemini.py      # Gemini AI 서비스
│   │   │   ├── gemini_embedding.py  # Gemini 임베딩
│   │   │   ├── emotion.py     # 감정 분석 서비스
│   │   │   ├── qdrant.py      # 벡터 검색 서비스
│   │   │   └── user_profile.py # 사용자 프로필 서비스
│   │   ├── models/            # 데이터베이스 모델
│   │   ├── schemas/           # Pydantic 스키마
│   │   ├── config.py          # 설정 관리
│   │   └── main.py            # FastAPI 앱
│   ├── requirements.txt       # Python 의존성
│   ├── .env.example          # 환경변수 템플릿
│   └── README.md             # 백엔드 문서
├── database/                  # 데이터베이스 관련
├── docs/                     # 프로젝트 문서
└── README.md                 # 프로젝트 메인 문서
```

## 🚀 빠른 시작

### 사전 요구사항
- Python 3.11+
- MySQL 8.0+
- Git

### 1. 프로젝트 클론
```bash
git clone <repository-url>
cd chatbot_project
```

### 2. 가상환경 설정
```bash
# 가상환경 생성
python -m venv chatbot_venv

# 가상환경 활성화
# Windows
chatbot_venv\Scripts\activate
# macOS/Linux
source chatbot_venv/bin/activate
```

### 3. 의존성 설치
```bash
cd backend
pip install -r requirements.txt
```

### 4. 환경변수 설정
```bash
# .env 파일 생성
cp .env.example .env

# .env 파일 편집 (필수 설정)
# GEMINI_API_KEY=your-gemini-api-key
# MYSQL_HOST=localhost
# MYSQL_USER=chatbot_user
# MYSQL_PASSWORD=chatbot_password
# MYSQL_DATABASE=chatbot_service
```

### 5. 데이터베이스 설정
```sql
-- MySQL에 데이터베이스 생성
CREATE DATABASE chatbot_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'chatbot_user'@'localhost' IDENTIFIED BY 'chatbot_password';
GRANT ALL PRIVILEGES ON chatbot_service.* TO 'chatbot_user'@'localhost';
FLUSH PRIVILEGES;
```

### 6. 서버 실행
```bash
# 개발 서버 시작
python start_dev.py

# 또는 uvicorn 직접 실행
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. API 확인
- **Swagger UI**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **API 엔드포인트**: http://localhost:8000/api/v1/

## 🔧 API 엔드포인트

### 📡 주요 API
| 엔드포인트 | 메소드 | 설명 |
|-----------|--------|------|
| `/api/v1/chat/send` | POST | 메시지 전송 |
| `/api/v1/chat/history` | GET | 대화 기록 조회 |
| `/api/v1/users/profile` | GET/PUT | 사용자 프로필 |
| `/api/v1/emotions/analyze` | POST | 감정 분석 |
| `/api/v1/emotions/history` | GET | 감정 기록 조회 |
| `/api/v1/schedules/` | GET/POST | 일정 관리 |
| `/api/v1/interests/` | GET/POST | 관심사 관리 |

### 📊 API 통계
- **총 엔드포인트**: 48개
- **API 모듈**: 5개 (Chat, User, Emotion, Schedule, Interest)
- **인증**: JWT 토큰 기반
- **응답 형식**: JSON

## 🔄 마이그레이션 이력

### OpenAI → Gemini 마이그레이션 (2025.07.08)
- **AI 모델**: GPT-4 → Gemini 2.0 Flash
- **임베딩**: text-embedding-3-small → text-embedding-004
- **비용**: 유료 → 무료
- **성능**: 한국어 특화 성능 향상
- **호환성**: 기존 API 인터페이스 100% 유지

## 🧪 테스트

### 백엔드 테스트
```bash
cd backend

# 간단한 테스트
python test_simple.py

# 데이터베이스 연결 테스트
python test_db_connection.py

# 개발 서버 시작 후 수동 테스트
# http://localhost:8000/docs
```

### API 테스트 예시
```bash
# Health Check
curl http://localhost:8000/health

# 채팅 테스트
curl -X POST "http://localhost:8000/api/v1/chat/send" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test-user",
    "message": "안녕하세요!"
  }'
```

## 📝 환경변수 설정

### 필수 환경변수
```bash
# AI API
GEMINI_API_KEY=your-gemini-api-key-here

# 데이터베이스
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=chatbot_user
MYSQL_PASSWORD=chatbot_password
MYSQL_DATABASE=chatbot_service

# 애플리케이션
DEBUG=true
SECRET_KEY=your-secret-key
```

### 선택적 환경변수
```bash
# Qdrant (벡터 검색)
QDRANT_HOST=localhost
QDRANT_PORT=6333

# 로깅
LOG_LEVEL=INFO

# CORS
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:3001
```

## 🐛 문제 해결

### 자주 발생하는 문제

#### 1. Qdrant 연결 경고
```
⚠️ Qdrant 초기화 실패 (테스트 환경에서는 정상)
```
**해결책**: 정상적인 경고입니다. 벡터 검색 없이도 모든 기능이 정상 작동합니다.

#### 2. MySQL 연결 실패
```
Can't connect to MySQL server
```
**해결책**: 
- MySQL 서버 실행 확인
- 데이터베이스 및 사용자 생성 확인
- `.env` 파일의 데이터베이스 설정 확인

#### 3. Gemini API 키 오류
```
Invalid API key
```
**해결책**:
- Google AI Studio에서 API 키 발급: https://aistudio.google.com/
- `.env` 파일에 올바른 API 키 설정

## 🚧 개발 로드맵

### Phase 1: 백엔드 API ✅
- [x] FastAPI 기반 REST API
- [x] Gemini AI 통합
- [x] 데이터베이스 모델링
- [x] 감정 분석 기능
- [x] 사용자 관리 시스템

### Phase 2: 프론트엔드 개발 🔄
- [ ] React 기반 웹 앱
- [ ] 반응형 UI/UX 디자인
- [ ] 실시간 채팅 인터페이스
- [ ] 사용자 대시보드

### Phase 3: 고도화 📋
- [ ] 음성 인식/합성
- [ ] 모바일 앱 개발
- [ ] 고급 감정 분석
- [ ] 추천 시스템

## 🤝 기여하기

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 📄 라이센스

이 프로젝트는 MIT 라이센스 하에 배포됩니다. 자세한 내용은 `LICENSE` 파일을 참조하세요.

> 💡 **팁**: 이 README는 지속적으로 업데이트됩니다. 최신 정보는 항상 이 문서를 확인해주세요.

**⭐ 이 프로젝트가 도움이 되셨다면 Star를 눌러주세요!** 