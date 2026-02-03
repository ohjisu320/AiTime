# test_worker_local.py
"""RabbitMQ 없이 worker 로직 테스트"""

import json
import sys
from pathlib import Path

# 프로젝트 루트를 path에 추가
sys.path.insert(0, str(Path(__file__).parent))

from app.worker import get_action_set_by_age, PoseWorker


def test_action_set_by_age():
    """월령별 동작 세트 테스트"""
    print("=" * 50)
    print("1. 월령별 동작 세트 테스트")
    print("=" * 50)
    
    test_cases = [
        (12, ["clapping", "hurray", "walking_back"]),
        (15, ["clapping", "hurray", "walking_back"]),
        (17, ["clapping", "hurray", "walking_back"]),
        (18, ["jumping", "kicking", "throwing"]),
        (20, ["jumping", "kicking", "throwing"]),
        (24, ["jumping", "kicking", "throwing"]),
    ]
    
    for age, expected in test_cases:
        result = get_action_set_by_age(age)
        status = "✅" if result == expected else "❌"
        print(f"  {status} {age}개월 → {result}")
    
    # 에러 케이스
    for age in [10, 11, 25, 30]:
        try:
            get_action_set_by_age(age)
            print(f"  ❌ {age}개월: 에러가 발생해야 함")
        except ValueError as e:
            print(f"  ✅ {age}개월: 예상된 에러 - {e}")
    
    print()


def test_pose_imitation_response():
    """pose_imitation 응답 구조 테스트 (실제 영상 없이)"""
    print("=" * 50)
    print("2. pose_imitation 응답 구조 테스트")
    print("=" * 50)
    
    # 모의 요청 (실제 영상 경로 필요)
    mock_task_15months = {
        "type": "pose_imitation",
        "request_id": "test-uuid-001",
        "video_path": "sample_video/test.mp4",  # 실제 파일이 있어야 동작
        "name": "테스트아동",
        "age_months": 15
    }
    
    mock_task_20months = {
        "type": "pose_imitation",
        "request_id": "test-uuid-002",
        "video_path": "sample_video/test.mp4",
        "name": "테스트아동2",
        "age_months": 20
    }
    
    print("\n[15개월 요청]")
    print(f"  동작 세트: {get_action_set_by_age(15)}")
    print(f"  요청: {json.dumps(mock_task_15months, ensure_ascii=False, indent=2)}")
    
    print("\n[20개월 요청]")
    print(f"  동작 세트: {get_action_set_by_age(20)}")
    print(f"  요청: {json.dumps(mock_task_20months, ensure_ascii=False, indent=2)}")
    
    print()


def test_with_real_video(video_path: str, age_months: int, name: str = "테스트"):
    """실제 영상으로 테스트 (RabbitMQ 없이 직접 호출)"""
    print("=" * 50)
    print("3. 실제 영상 테스트")
    print("=" * 50)
    
    if not Path(video_path).exists():
        print(f"  ❌ 영상 파일 없음: {video_path}")
        return
    
    # Worker 인스턴스 생성 (RabbitMQ 연결 없이)
    print("  ⏳ Worker 초기화 중...")
    worker = PoseWorker()
    
    # 모의 요청
    task = {
        "type": "pose_imitation",
        "request_id": "local-test-001",
        "video_path": video_path,
        "name": name,
        "age_months": age_months
    }
    
    print(f"  📹 분석 시작: {name} ({age_months}개월)")
    print(f"  📁 영상: {video_path}")
    print(f"  🎯 동작 세트: {get_action_set_by_age(age_months)}")
    print()
    
    # 직접 처리 메서드 호출
    result = worker._process_pose_imitation(task)
    
    print("\n[응답 결과]")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    
    return result


if __name__ == "__main__":
    # 1. 월령별 동작 세트 테스트
    test_action_set_by_age()
    
    # 2. 응답 구조 테스트
    test_pose_imitation_response()
    
    # 3. 실제 영상 테스트 (영상 경로가 있을 경우)
    # 사용법: python test_worker_local.py <video_path> <age_months> [name]
    if len(sys.argv) >= 3:
        video_path = sys.argv[1]
        age_months = int(sys.argv[2])
        name = sys.argv[3] if len(sys.argv) > 3 else "테스트아동"
        test_with_real_video(video_path, age_months, name)
    else:
        print("=" * 50)
        print("3. 실제 영상 테스트")
        print("=" * 50)
        print("  ℹ️ 실제 영상 테스트 방법:")
        print("  python test_worker_local.py <video_path> <age_months> [name]")
        print()
        print("  예시:")
        print("  python test_worker_local.py sample_video/test.mp4 15 김민준")
        print("  python test_worker_local.py sample_video/test.mp4 20 이서연")
