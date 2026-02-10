
import unittest
from unittest.mock import MagicMock, patch
import json
import time
import queue
from app.worker import PoseWorker

class TestThreadedWorker(unittest.TestCase):
    @patch('app.worker.get_model')
    @patch('app.worker.MotionAnalyzer')
    @patch('pika.BlockingConnection')
    def test_process_message_heartbeat(self, mock_conn_cls, mock_analyzer_cls, mock_get_model):
        """
        긴 분석 작업(3초) 동안 process_data_events(하트비트)가 호출되는지 검증
        """
        # Setup
        mock_conn = MagicMock()
        mock_conn_cls.return_value = mock_conn
        
        mock_channel = MagicMock()
        mock_conn.channel.return_value = mock_channel
        
        # Analyzer가 3초 동안 동작하는 것처럼 Mocking
        mock_analyzer_instance = mock_analyzer_cls.return_value
        def long_running_analysis(*args, **kwargs):
            time.sleep(3) # 3초 대기
            result = MagicMock()
            result.metrics = {"per_trial": []}
            result.ados = {}
            return result
        mock_analyzer_instance.analyze_multi_trial.side_effect = long_running_analysis

        # Worker 초기화
        worker = PoseWorker()
        worker.connection = mock_conn
        worker.channel = mock_channel

        # 메시지 생성
        body = json.dumps({
            "examId": "test_exam",
            "videoId": "test_video",
            "videoType": "POSE_IMITATION",
            "ageMonths": 24,
            "video_path": "dummy_path", # 로컬 경로 사용
            "childName": "TestChild"
        }).encode('utf-8')

        mock_method = MagicMock()
        mock_method.delivery_tag = 1

        # 실행 (비디오 로드 부분도 Mocking 필요)
        with patch.object(worker, '_load_video', return_value="dummy_path"):
            with patch('os.path.exists', return_value=True):
                 worker.process_message(mock_channel, mock_method, None, body)

        # 검증
        # 1. analyze_multi_trial이 호출되었는지
        mock_analyzer_instance.analyze_multi_trial.assert_called_once()
        
        # 2. process_data_events가 호출되었는지 (하트비트)
        # 3초 동안 0.1초 간격으로 호출되므로 적어도 20번 이상은 호출되어야 함
        heartbeat_calls = worker.connection.process_data_events.call_count
        print(f"Heartbeat calls: {heartbeat_calls}")
        self.assertTrue(heartbeat_calls > 10, "Heartbeat가 충분히 호출되지 않았습니다.")

        # 3. Ack가 호출되었는지
        mock_channel.basic_ack.assert_called_with(delivery_tag=1)

if __name__ == '__main__':
    unittest.main()
