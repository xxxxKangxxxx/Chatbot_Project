"""
애플리케이션 설정 관리
=====================================================

환경 변수 및 설정 값들을 관리합니다.
"""

from pydantic_settings import BaseSettings
from typing import List, Union
import os
from pathlib import Path
from pydantic import field_validator


class Settings(BaseSettings):
    """애플리케이션 설정"""
    
    # 애플리케이션 기본 설정
    APP_NAME: str = "고령층 개인화 챗봇"
    VERSION: str = "1.0.0"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # CORS 설정
    ALLOWED_ORIGINS: Union[List[str], str] = [
        "http://localhost:3000",  # React 개발 서버
        "http://localhost:3001",  # React 프로덕션
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001"
    ]
    
    # 보안 호스트 설정
    ALLOWED_HOSTS: Union[List[str], str] = ["*"]  # 개발 환경에서는 모든 호스트 허용
    
    @field_validator('ALLOWED_ORIGINS', mode='before')
    @classmethod
    def validate_allowed_origins(cls, v):
        """ALLOWED_ORIGINS 필드 검증 및 변환"""
        if isinstance(v, str):
            # 쉼표로 구분된 문자열을 리스트로 변환
            return [origin.strip() for origin in v.split(',') if origin.strip()]
        return v
    
    @field_validator('ALLOWED_HOSTS', mode='before')
    @classmethod
    def validate_allowed_hosts(cls, v):
        """ALLOWED_HOSTS 필드 검증 및 변환"""
        if isinstance(v, str):
            # 쉼표로 구분된 문자열을 리스트로 변환
            return [host.strip() for host in v.split(',') if host.strip()]
        return v
    
    # MySQL 데이터베이스 설정
    MYSQL_HOST: str = "localhost"
    MYSQL_PORT: int = 3306
    MYSQL_USER: str = "chatbot_user"
    MYSQL_PASSWORD: str = "chatbot_password"
    MYSQL_DATABASE: str = "chatbot_service"
    
    # 데이터베이스 별칭 (main.py 호환성)
    @property
    def DATABASE_HOST(self) -> str:
        return self.MYSQL_HOST
    
    # Qdrant 설정
    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "chat_vectors"
    
    # AI API 설정
    # OpenAI API 설정 (레거시, 마이그레이션 후 제거 예정)
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-3.5-turbo"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-ada-002"
    OPENAI_MAX_TOKENS: int = 1000
    OPENAI_TEMPERATURE: float = 0.7
    
    # Gemini API 설정 (메인)
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.0-flash-exp"
    GEMINI_EMBEDDING_MODEL: str = "text-embedding-004"
    GEMINI_MAX_TOKENS: int = 2000
    GEMINI_TEMPERATURE: float = 0.7
    
    # 임베딩 설정
    EMBEDDING_DIMENSION: int = 1536
    SIMILARITY_THRESHOLD: float = 0.7
    MAX_SEARCH_RESULTS: int = 5
    
    # 보안 설정
    SECRET_KEY: str = "your-secret-key-here"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # 로깅 설정
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 파일 업로드 설정
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10MB
    
    @property
    def DATABASE_URL(self) -> str:
        """MySQL 데이터베이스 URL 생성"""
        return f"mysql+asyncmy://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_HOST}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"
    
    @property
    def QDRANT_URL(self) -> str:
        """Qdrant 서버 URL 생성"""
        return f"http://{self.QDRANT_HOST}:{self.QDRANT_PORT}"
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = True
        extra = "ignore"  # 정의되지 않은 환경 변수 무시


# 전역 설정 인스턴스
settings = Settings()


# 개발/프로덕션 환경별 설정
class DevelopmentSettings(Settings):
    """개발 환경 설정"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # 개발용 데이터베이스
    MYSQL_HOST: str = "localhost"
    MYSQL_DATABASE: str = "chatbot_dev"


class ProductionSettings(Settings):
    """프로덕션 환경 설정"""
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"
    
    # 프로덕션용 보안 설정
    ALLOWED_ORIGINS: List[str] = [
        "https://your-frontend-domain.com"
    ]
    ALLOWED_HOSTS: List[str] = [
        "your-api-domain.com",
        "localhost"
    ]


class TestSettings(Settings):
    """테스트 환경 설정"""
    DEBUG: bool = True
    LOG_LEVEL: str = "DEBUG"
    
    # 테스트용 데이터베이스
    MYSQL_DATABASE: str = "chatbot_test"
    QDRANT_COLLECTION: str = "test_chat_vectors"


def get_settings() -> Settings:
    """환경에 따른 설정 반환"""
    environment = os.getenv("ENVIRONMENT", "development").lower()
    
    if environment == "production":
        return ProductionSettings()
    elif environment == "test":
        return TestSettings()
    else:
        return DevelopmentSettings()


# 환경별 설정 적용
settings = get_settings()


# 로깅 설정
import logging

logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT,
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("app.log")
    ]
)

logger = logging.getLogger(__name__)


# 디렉토리 생성
def create_directories():
    """필요한 디렉토리 생성"""
    directories = [
        settings.UPLOAD_DIR,
        "logs",
        "temp"
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


# 애플리케이션 시작 시 디렉토리 생성
create_directories()


# 설정 검증
def validate_settings():
    """필수 설정 값 검증"""
    required_settings = [
        "OPENAI_API_KEY",
        "SECRET_KEY",
        "MYSQL_PASSWORD"
    ]
    
    missing_settings = []
    for setting in required_settings:
        if not getattr(settings, setting):
            missing_settings.append(setting)
    
    if missing_settings:
        logger.warning(f"누락된 설정: {', '.join(missing_settings)}")
        logger.warning("환경 변수 또는 .env 파일에서 설정을 확인하세요.")


# 설정 검증 실행
validate_settings()


# 설정 정보 출력 (민감 정보 제외)
def print_settings():
    """현재 설정 정보 출력"""
    logger.info("=== 애플리케이션 설정 ===")
    logger.info(f"앱 이름: {settings.APP_NAME}")
    logger.info(f"버전: {settings.VERSION}")
    logger.info(f"환경: {'개발' if settings.DEBUG else '프로덕션'}")
    logger.info(f"호스트: {settings.HOST}:{settings.PORT}")
    logger.info(f"데이터베이스: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    logger.info(f"Qdrant: {settings.QDRANT_HOST}:{settings.QDRANT_PORT}")
    logger.info(f"OpenAI 모델: {settings.OPENAI_MODEL}")
    logger.info("========================")


if __name__ == "__main__":
    print_settings() 