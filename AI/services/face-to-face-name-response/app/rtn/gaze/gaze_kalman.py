import cv2
import numpy as np


class GazeKalmanFilter:
    """
    시선 좌표(x, y)를 위한 Kalman Filter.
    Constant Velocity Model을 사용하여 부드러운 움직임을 추정하고 지연을 줄인다.

    State State: [x, y, vx, vy]^T
    Measurement: [x, y]^T
    """

    def __init__(
        self, process_noise: float = 1e-2, measurement_noise: float = 1e-1
    ) -> None:
        self.kf = cv2.KalmanFilter(4, 2)

        # State Transition Matrix (A)
        # x' = x + vx
        # y' = y + vy
        self.kf.transitionMatrix = np.array(
            [[1, 0, 1, 0], [0, 1, 0, 1], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32
        )

        # Measurement Matrix (H)
        # z_x = x
        # z_y = y
        self.kf.measurementMatrix = np.array(
            [[1, 0, 0, 0], [0, 1, 0, 0]], dtype=np.float32
        )

        # Process Noise Covariance (Q)
        # 시스템 모델(등속도)의 불확실성.
        # 값이 클수록 모델을 덜 신뢰하고 측정값에 민감하게 반응(지연 감소, 노이즈 증가)
        self.kf.processNoiseCov = np.eye(4, dtype=np.float32) * process_noise

        # Measurement Noise Covariance (R)
        # 측정값(FaceMesh 결과)의 노이즈.
        # 값이 클수록 측정값을 덜 신뢰하고 모델 예측을 중시(노이즈 감소, 지연 증가)
        self.kf.measurementNoiseCov = np.eye(2, dtype=np.float32) * measurement_noise

        # Error Covariance (P)
        self.kf.errorCovPost = np.eye(4, dtype=np.float32)

        # 초기 상태
        self.kf.statePost = np.zeros((4, 1), dtype=np.float32)

    def reset(self, initial_pos: tuple[float, float]) -> None:
        # 초기 위치는 측정값이므로 신뢰도가 높음 -> 오차 공분산을 작게 설정
        self.kf.errorCovPost = np.eye(4, dtype=np.float32) * 0.1
        self.kf.statePost = np.array(
            [[initial_pos[0]], [initial_pos[1]], [0], [0]], dtype=np.float32
        )

    def update(self, pos: tuple[float, float]) -> tuple[float, float]:
        """
        Predict -> Correct 단계 수행 후 추정된 위치 반환
        """
        # 1. Predict (updates statePre)
        self.kf.predict()

        # 2. Correct
        measurement = np.array(
            [[np.float32(pos[0])], [np.float32(pos[1])]], dtype=np.float32
        )
        self.kf.correct(measurement)

        # Return estimated position (x, y)
        # statePost: [x, y, vx, vy]
        est_x = float(self.kf.statePost[0, 0])
        est_y = float(self.kf.statePost[1, 0])

        return est_x, est_y
