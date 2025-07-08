-- =====================================================
-- 고령층 개인화 챗봇 서비스 - MySQL 데이터베이스 스키마
-- =====================================================

-- 데이터베이스 생성 (선택사항)
-- CREATE DATABASE chatbot_service CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE chatbot_service;

-- =====================================================
-- 1. 사용자 테이블 (users)
-- =====================================================
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50) NOT NULL COMMENT '사용자 이름',
    age INT CHECK (age >= 0 AND age <= 120) COMMENT '나이',
    gender ENUM('M', 'F', 'OTHER') DEFAULT 'F' COMMENT '성별',
    speech_style TEXT COMMENT '말투 스타일 (JSON 형태 저장 가능)',
    phone VARCHAR(20) COMMENT '연락처 (응급시 사용)',
    profile_image VARCHAR(255) COMMENT '프로필 이미지 경로',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    last_login DATETIME COMMENT '마지막 로그인 시간',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '수정일시',
    
    INDEX idx_name (name),
    INDEX idx_active (is_active),
    INDEX idx_last_login (last_login)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 정보';

-- =====================================================
-- 2. 대화 로그 테이블 (chat_logs)
-- =====================================================
CREATE TABLE chat_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '사용자 ID',
    role ENUM('user', 'bot') NOT NULL COMMENT '발화 주체',
    message TEXT NOT NULL COMMENT '대화 내용',
    emotion VARCHAR(20) COMMENT '감정 태그 (기쁨, 우울, 화남, 평온 등)',
    emotion_score FLOAT DEFAULT 0.0 COMMENT '감정 점수 (-1.0 ~ 1.0)',
    message_type ENUM('text', 'button', 'medication', 'mood') DEFAULT 'text' COMMENT '메시지 유형',
    session_id VARCHAR(100) COMMENT '대화 세션 ID',
    qdrant_vector_id VARCHAR(100) COMMENT 'Qdrant 벡터 ID (연동용)',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_role (role),
    INDEX idx_session_id (session_id),
    INDEX idx_created_at (created_at),
    INDEX idx_emotion (emotion)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='대화 로그';

-- =====================================================
-- 3. 감정 히스토리 테이블 (emotions)
-- =====================================================
CREATE TABLE emotions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '사용자 ID',
    emotion VARCHAR(20) NOT NULL COMMENT '감정 유형',
    intensity FLOAT NOT NULL CHECK (intensity >= 0.0 AND intensity <= 1.0) COMMENT '감정 강도 (0.0 ~ 1.0)',
    context TEXT COMMENT '감정 발생 맥락',
    trigger_message_id INT COMMENT '감정을 유발한 메시지 ID',
    detected_method ENUM('rule_based', 'ml_model', 'manual') DEFAULT 'rule_based' COMMENT '감정 감지 방법',
    detected_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '감지일시',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    FOREIGN KEY (trigger_message_id) REFERENCES chat_logs(id) ON DELETE SET NULL,
    INDEX idx_user_id (user_id),
    INDEX idx_emotion (emotion),
    INDEX idx_detected_at (detected_at),
    INDEX idx_intensity (intensity)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='감정 히스토리';

-- =====================================================
-- 4. 약 복용 스케줄 테이블 (medication_schedules)
-- =====================================================
CREATE TABLE medication_schedules (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '사용자 ID',
    medication_name VARCHAR(100) NOT NULL COMMENT '약물명',
    dosage VARCHAR(50) COMMENT '복용량 (예: 1정, 2ml)',
    schedule_time TIME NOT NULL COMMENT '복용 시간',
    schedule_date DATE NOT NULL COMMENT '복용 날짜',
    is_taken BOOLEAN DEFAULT FALSE COMMENT '복용 여부',
    taken_at DATETIME COMMENT '실제 복용 시간',
    reminder_sent BOOLEAN DEFAULT FALSE COMMENT '알림 발송 여부',
    notes TEXT COMMENT '특이사항',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_schedule_date (schedule_date),
    INDEX idx_schedule_time (schedule_time),
    INDEX idx_is_taken (is_taken),
    INDEX idx_is_active (is_active),
    UNIQUE KEY unique_user_med_datetime (user_id, medication_name, schedule_date, schedule_time)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='약 복용 스케줄';

-- =====================================================
-- 5. 관심사 테이블 (interests)
-- =====================================================
CREATE TABLE interests (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '사용자 ID',
    keyword VARCHAR(50) NOT NULL COMMENT '관심사 키워드',
    category VARCHAR(30) COMMENT '카테고리 (가족, 취미, 건강, 음식 등)',
    weight FLOAT DEFAULT 1.0 COMMENT '관심도 가중치',
    mentioned_count INT DEFAULT 1 COMMENT '언급 횟수',
    last_mentioned DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '마지막 언급 시간',
    is_active BOOLEAN DEFAULT TRUE COMMENT '활성 상태',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '생성일시',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_keyword (keyword),
    INDEX idx_category (category),
    INDEX idx_weight (weight),
    INDEX idx_is_active (is_active),
    UNIQUE KEY unique_user_keyword (user_id, keyword)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='사용자 관심사';

-- =====================================================
-- 6. 대화 세션 테이블 (chat_sessions) - 추가 제안
-- =====================================================
CREATE TABLE chat_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL COMMENT '사용자 ID',
    session_id VARCHAR(100) NOT NULL COMMENT '세션 ID',
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '세션 시작 시간',
    end_time DATETIME COMMENT '세션 종료 시간',
    message_count INT DEFAULT 0 COMMENT '메시지 수',
    avg_emotion_score FLOAT COMMENT '평균 감정 점수',
    session_summary TEXT COMMENT '세션 요약',
    
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id),
    INDEX idx_session_id (session_id),
    INDEX idx_start_time (start_time),
    UNIQUE KEY unique_session_id (session_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='대화 세션 관리';

-- =====================================================
-- 초기 데이터 삽입 (테스트용)
-- =====================================================

-- 테스트 사용자 생성
INSERT INTO users (name, age, gender, speech_style, phone) VALUES 
('김영희', 65, 'F', '친근하고 따뜻한 말투를 선호함', '010-1234-5678'),
('박철수', 70, 'M', '격식을 차린 정중한 말투를 선호함', '010-9876-5432'),
('이순자', 68, 'F', '활발하고 유머러스한 말투를 선호함', '010-5555-7777');

-- 테스트 관심사 데이터
INSERT INTO interests (user_id, keyword, category, weight) VALUES 
(1, '손녀', '가족', 2.0),
(1, '꽃 기르기', '취미', 1.5),
(1, '혈압약', '건강', 1.8),
(2, '바둑', '취미', 2.0),
(2, '뉴스', '정보', 1.3),
(3, '요리', '취미', 1.7),
(3, '드라마', '엔터테인먼트', 1.4);

-- =====================================================
-- 유용한 뷰 생성
-- =====================================================

-- 사용자별 최근 대화 조회 뷰
CREATE VIEW user_recent_chats AS
SELECT 
    u.id as user_id,
    u.name,
    cl.message,
    cl.role,
    cl.emotion,
    cl.created_at
FROM users u
JOIN chat_logs cl ON u.id = cl.user_id
WHERE cl.created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
ORDER BY cl.created_at DESC;

-- 사용자별 감정 트렌드 조회 뷰
CREATE VIEW user_emotion_trends AS
SELECT 
    u.id as user_id,
    u.name,
    e.emotion,
    AVG(e.intensity) as avg_intensity,
    COUNT(*) as count,
    DATE(e.detected_at) as emotion_date
FROM users u
JOIN emotions e ON u.id = e.user_id
WHERE e.detected_at >= DATE_SUB(NOW(), INTERVAL 30 DAY)
GROUP BY u.id, e.emotion, DATE(e.detected_at)
ORDER BY emotion_date DESC;

-- =====================================================
-- 인덱스 최적화를 위한 추가 복합 인덱스
-- =====================================================

-- 대화 로그 검색 최적화
CREATE INDEX idx_user_role_created ON chat_logs(user_id, role, created_at);
CREATE INDEX idx_user_emotion_created ON chat_logs(user_id, emotion, created_at);

-- 감정 분석 최적화
CREATE INDEX idx_user_emotion_detected ON emotions(user_id, emotion, detected_at);

-- 약 복용 스케줄 검색 최적화
CREATE INDEX idx_user_date_time ON medication_schedules(user_id, schedule_date, schedule_time);
CREATE INDEX idx_active_not_taken ON medication_schedules(is_active, is_taken, schedule_date);

-- =====================================================
-- 스키마 생성 완료
-- ===================================================== 