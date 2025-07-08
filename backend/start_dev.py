#!/usr/bin/env python3
"""
개발 서버 시작 스크립트
=====================================================

개발 환경에서 FastAPI 서버를 시작하는 스크립트입니다.
"""

import os
import sys
import uvicorn
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# 필요한 디렉토리 생성
def create_directories():
    """개발에 필요한 디렉토리들을 생성"""
    directories = [
        "logs",
        "uploads", 
        "temp"
    ]
    
    for directory in directories:
        dir_path = project_root / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 디렉토리 생성/확인: {dir_path}")


def main():
    """개발 서버 시작"""
    print("🚀 고령층 챗봇 개발 서버 시작 중...")
    
    # 환경 변수 설정
    os.environ.setdefault("ENVIRONMENT", "development")
    
    # 디렉토리 생성
    create_directories()
    
    # 개발 서버 설정
    config = {
        "app": "app.main:app",
        "host": "0.0.0.0", 
        "port": 8000,
        "reload": True,
        "reload_dirs": ["app"],
        "log_level": "info",
        "access_log": True,
    }
    
    print("📋 서버 설정:")
    print(f"   - 주소: http://{config['host']}:{config['port']}")
    print(f"   - 리로드: {config['reload']}")
    print(f"   - 로그 레벨: {config['log_level']}")
    print(f"   - API 문서: http://{config['host']}:{config['port']}/docs")
    print(f"   - ReDoc: http://{config['host']}:{config['port']}/redoc")
    print()
    
    try:
        # FastAPI 서버 시작
        uvicorn.run(**config)
    except KeyboardInterrupt:
        print("\n👋 서버를 종료합니다...")
    except Exception as e:
        print(f"❌ 서버 시작 실패: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 