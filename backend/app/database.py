"""
SQLAlchemy 데이터베이스 연결 설정
=====================================================

MySQL 데이터베이스 연결 및 세션 관리
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import AsyncGenerator
import logging

from app.config import settings

logger = logging.getLogger(__name__)

# 비동기 엔진 생성
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # 개발 환경에서 SQL 쿼리 로그 출력
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,  # 연결 상태 확인
    pool_recycle=3600,   # 1시간마다 연결 재생성
)

# 비동기 세션 팩토리
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# 베이스 모델 클래스
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    데이터베이스 세션 의존성 주입
    
    FastAPI 의존성으로 사용됩니다.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"데이터베이스 세션 오류: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    데이터베이스 초기화
    
    테이블 생성 및 초기 데이터 삽입
    """
    try:
        # 모든 테이블 생성
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ 데이터베이스 테이블 생성 완료")
        
        # 초기 데이터 삽입
        await insert_initial_data()
        
    except Exception as e:
        logger.error(f"❌ 데이터베이스 초기화 실패: {e}")
        raise


async def insert_initial_data():
    """
    초기 데이터 삽입
    """
    try:
        from app.models.user import User
        from app.models.interest import Interest
        
        async with AsyncSessionLocal() as session:
            # 기존 사용자 확인
            from sqlalchemy import select
            result = await session.execute(select(User))
            existing_users = result.scalars().all()
            
            if not existing_users:
                # 테스트 사용자 생성
                test_users = [
                    User(
                        name="김영희",
                        age=65,
                        gender="F",
                        speech_style="친근하고 따뜻한 말투를 선호함",
                        phone="010-1234-5678"
                    ),
                    User(
                        name="박철수",
                        age=70,
                        gender="M",
                        speech_style="격식을 차린 정중한 말투를 선호함",
                        phone="010-9876-5432"
                    ),
                    User(
                        name="이순자",
                        age=68,
                        gender="F",
                        speech_style="활발하고 유머러스한 말투를 선호함",
                        phone="010-5555-7777"
                    )
                ]
                
                for user in test_users:
                    session.add(user)
                
                await session.commit()
                logger.info("✅ 테스트 사용자 데이터 생성 완료")
                
                # 관심사 데이터 생성
                test_interests = [
                    Interest(user_id=1, keyword="손녀", category="가족", weight=2.0),
                    Interest(user_id=1, keyword="꽃 기르기", category="취미", weight=1.5),
                    Interest(user_id=1, keyword="혈압약", category="건강", weight=1.8),
                    Interest(user_id=2, keyword="바둑", category="취미", weight=2.0),
                    Interest(user_id=2, keyword="뉴스", category="정보", weight=1.3),
                    Interest(user_id=3, keyword="요리", category="취미", weight=1.7),
                    Interest(user_id=3, keyword="드라마", category="엔터테인먼트", weight=1.4),
                ]
                
                for interest in test_interests:
                    session.add(interest)
                
                await session.commit()
                logger.info("✅ 테스트 관심사 데이터 생성 완료")
            
            else:
                logger.info("기존 사용자 데이터가 존재합니다.")
                
    except Exception as e:
        logger.error(f"❌ 초기 데이터 삽입 실패: {e}")


async def check_db_connection():
    """
    데이터베이스 연결 상태 확인
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute("SELECT 1")
        logger.info("✅ 데이터베이스 연결 정상")
        return True
    except Exception as e:
        logger.error(f"❌ 데이터베이스 연결 실패: {e}")
        return False


async def close_db():
    """
    데이터베이스 연결 종료
    """
    try:
        await engine.dispose()
        logger.info("✅ 데이터베이스 연결 종료")
    except Exception as e:
        logger.error(f"❌ 데이터베이스 종료 실패: {e}")


# 헬스 체크용 함수
async def get_db_status():
    """
    데이터베이스 상태 정보 반환
    """
    try:
        async with AsyncSessionLocal() as session:
            # 연결 테스트
            await session.execute("SELECT 1")
            
            # 사용자 수 조회
            from sqlalchemy import select, func
            from app.models.user import User
            
            result = await session.execute(select(func.count(User.id)))
            user_count = result.scalar()
            
            return {
                "status": "connected",
                "user_count": user_count,
                "engine_pool_size": engine.pool.size(),
                "engine_pool_checked_in": engine.pool.checkedin(),
                "engine_pool_checked_out": engine.pool.checkedout(),
            }
    except Exception as e:
        logger.error(f"데이터베이스 상태 확인 실패: {e}")
        return {
            "status": "disconnected",
            "error": str(e)
        }


# 트랜잭션 관리 유틸리티
class DatabaseTransaction:
    """
    데이터베이스 트랜잭션 컨텍스트 매니저
    """
    
    def __init__(self, session: AsyncSession):
        self.session = session
    
    async def __aenter__(self):
        return self.session
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            await self.session.rollback()
            logger.error(f"트랜잭션 롤백: {exc_type.__name__}: {exc_val}")
        else:
            await self.session.commit()


# 배치 처리 유틸리티
async def batch_insert(session: AsyncSession, objects: list, batch_size: int = 1000):
    """
    대량 데이터 배치 삽입
    
    Args:
        session: 데이터베이스 세션
        objects: 삽입할 객체 리스트
        batch_size: 배치 크기
    """
    try:
        for i in range(0, len(objects), batch_size):
            batch = objects[i:i + batch_size]
            session.add_all(batch)
            await session.commit()
            logger.info(f"배치 삽입 완료: {i + len(batch)}/{len(objects)}")
    except Exception as e:
        await session.rollback()
        logger.error(f"배치 삽입 실패: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    
    async def test_connection():
        """연결 테스트"""
        print("데이터베이스 연결 테스트 시작...")
        
        # 연결 확인
        is_connected = await check_db_connection()
        print(f"연결 상태: {'성공' if is_connected else '실패'}")
        
        # 상태 정보 출력
        status = await get_db_status()
        print(f"상태 정보: {status}")
        
        # 연결 종료
        await close_db()
        print("테스트 완료")
    
    asyncio.run(test_connection()) 