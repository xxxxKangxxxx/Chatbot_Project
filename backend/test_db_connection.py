#!/usr/bin/env python3
"""
데이터베이스 연결 테스트 스크립트
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.config import settings
from app.database import engine, Base
from sqlalchemy import text
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_database_connection():
    """데이터베이스 연결 테스트"""
    
    print("🔍 데이터베이스 연결 테스트 시작...")
    print(f"📋 연결 정보:")
    print(f"   - 호스트: {settings.MYSQL_HOST}:{settings.MYSQL_PORT}")
    print(f"   - 사용자: {settings.MYSQL_USER}")
    print(f"   - 데이터베이스: {settings.MYSQL_DATABASE}")
    print(f"   - 연결 URL: {settings.DATABASE_URL}")
    print()
    
    try:
        # 데이터베이스 연결 테스트
        async with engine.begin() as conn:
            result = await conn.execute(text("SELECT 1 as test"))
            row = result.fetchone()
            print(f"✅ 데이터베이스 연결 성공! 테스트 쿼리 결과: {row}")
            
        # 테이블 존재 확인
        async with engine.begin() as conn:
            result = await conn.execute(text("SHOW TABLES"))
            tables = result.fetchall()
            print(f"📊 기존 테이블 개수: {len(tables)}")
            if tables:
                print("   테이블 목록:")
                for table in tables:
                    print(f"   - {table[0]}")
            else:
                print("   테이블이 없습니다.")
                
        print("\n🎉 데이터베이스 연결 테스트 완료!")
        return True
        
    except Exception as e:
        print(f"❌ 데이터베이스 연결 실패: {e}")
        print(f"   오류 타입: {type(e).__name__}")
        
        # 상세 오류 정보
        if hasattr(e, 'orig'):
            print(f"   원본 오류: {e.orig}")
            
        return False

async def main():
    """메인 함수"""
    success = await test_database_connection()
    
    if not success:
        print("\n🔧 문제 해결 방법:")
        print("1. MySQL 서버가 실행 중인지 확인: brew services list | grep mysql")
        print("2. MySQL 서버 시작: brew services start mysql")
        print("3. 사용자 계정 확인: mysql -u root -p")
        print("4. 사용자 계정 재생성:")
        print("   CREATE USER 'chatbot_user'@'localhost' IDENTIFIED BY 'chatbot_password';")
        print("   GRANT ALL PRIVILEGES ON chatbot_service.* TO 'chatbot_user'@'localhost';")
        print("   FLUSH PRIVILEGES;")
        
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 