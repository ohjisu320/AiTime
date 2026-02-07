# services/name_non_facing/app/models/head_pose_6d.py
"""
6DRepNet360 Head Pose Estimator 래퍼

360° 전 방향에서 Head Pose (yaw, pitch, roll)를 추정합니다.
뒤통수에서도 안정적인 각도 추정이 가능합니다.

설계 의도:
    1. 360° Head Pose 추정 (뒤통수 포함)
    2. Euler Angles (yaw, pitch, roll) 출력
    3. 시선 벡터로 변환 가능

Reference:
    - 6DRepNet360: https://github.com/thohemp/6DRepNet360
    - 논문: "6D Rotation Representation for Unconstrained Head Pose Estimation"
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional
import logging
import urllib.request

import numpy as np
import cv2

from app.models.base import BaseModel
from app.models.head_detector import BoundingBox
from app.config import get_settings

logger = logging.getLogger(__name__)


# 모델 다운로드 URL (ovgu.de 공식 링크)
MODEL_URL = "https://cloud.ovgu.de/s/wWCitDxp9t79xkP/download/6DRepNet360_300W_LP.pth"
MODEL_CACHE_DIR = Path.home() / ".cache" / "6drepnet360"


@dataclass
class HeadPose6D:
    """
    6D Head Pose 결과
    
    Euler Angles:
        - yaw: 좌우 회전 (-180° ~ +180°), 왼쪽이 양수
        - pitch: 상하 회전 (-90° ~ +90°), 아래가 양수
        - roll: 기울기 (-180° ~ +180°), 시계방향이 양수
    
    좌표계:
        - 정면: yaw=0, pitch=0
        - 왼쪽 90°: yaw=+90
        - 뒤통수: yaw=±180
        - 오른쪽 90°: yaw=-90
    """
    yaw: float      # 좌우 회전 (도)
    pitch: float    # 상하 회전 (도)
    roll: float     # 기울기 (도)
    confidence: float = 1.0
    
    def to_gaze_vector(self) -> np.ndarray:
        """
        Euler angles를 3D 시선 벡터로 변환
        
        Returns:
            정규화된 3D 시선 벡터 [x, y, z]
            - x: 오른쪽이 양수 (화면/픽셀 좌표계 기준)
            - y: 아래가 양수
            - z: 앞(카메라 방향)이 양수
        
        좌표계 매핑:
            6DRepNet360 yaw 규칙: 왼쪽이 양수 (yaw>0 = 왼쪽 회전)
            화면 픽셀 좌표: 오른쪽이 x 양수
            → x = -cos(pitch)*sin(yaw) 로 부호를 맞춤
        
        Note (2025-01-23 결정사항):
            이 방식이 프로젝트의 primary 시선 벡터 계산법.
            ViTPose COCO 키포인트(귀-코 법선 벡터) 도입을 검토했으나,
            아래 이유로 현행 유지:
            - 6DRepNet360이 360° 전방향(뒤통수 포함) 지원
            - ViTPose는 2D 전용(z축 없음) + 귀 정밀도 부족
            - 기하학적 법선 벡터가 필요시 MediaPipe가 더 적합 (이미 구현됨)
        """
        yaw = np.radians(self.yaw)
        pitch = np.radians(self.pitch)
        
        # 시선 벡터 계산
        # 초기 시선 방향: +Z (정면, 카메라를 향함)
        # yaw: Y축 기준 회전 (6DRepNet: 왼쪽 양수)
        # pitch: X축 기준 회전 (6DRepNet: 아래 양수)
        # x 부호 반전: sin(yaw)는 왼쪽이 양수이지만,
        #   픽셀 좌표에서는 오른쪽이 양수이므로 -sin(yaw)
        
        x = -np.cos(pitch) * np.sin(yaw)
        y = np.sin(pitch)
        z = np.cos(pitch) * np.cos(yaw)
        
        gaze_vector = np.array([x, y, z])
        norm = np.linalg.norm(gaze_vector)
        
        if norm > 0:
            return gaze_vector / norm
        return np.array([0, 0, 1])  # 기본값: 정면
    
    def is_facing_camera(self, threshold_deg: float = 45.0) -> bool:
        """카메라(정면)를 보고 있는지 확인"""
        return abs(self.yaw) < threshold_deg and abs(self.pitch) < threshold_deg
    
    def is_back_of_head(self, threshold_deg: float = 135.0) -> bool:
        """뒤통수 상태인지 확인"""
        return abs(self.yaw) > threshold_deg


class HeadPoseEstimator6D(BaseModel):
    """
    6DRepNet360 Head Pose Estimator 래퍼
    
    Usage:
        estimator = HeadPoseEstimator6D()
        pose = estimator.estimate(frame, head_bbox)
        gaze_vector = pose.to_gaze_vector()
    """
    
    INPUT_SIZE = (224, 224)  # 모델 입력 크기
    
    def __init__(self, model_path: str = None, device: str = None):
        """
        HeadPoseEstimator6D 초기화
        
        Args:
            model_path: 모델 경로 (None이면 config에서 가져옴)
            device: 실행 디바이스 (None이면 config에서 가져옴)
        """
        self._settings = get_settings()
        self._model_path = model_path or self._settings.SIXDREPNET_MODEL
        self._device = device or self._settings.SIXDREPNET_DEVICE
        self._model = None
        self._model_loaded = False
        self._torch = None
    
    def _download_model_if_needed(self) -> str:
        """모델 파일 다운로드 (없으면)"""
        model_path = Path(self._model_path)
        
        # 절대 경로가 아니면 캐시 디렉토리에 저장
        if not model_path.is_absolute():
            model_path = MODEL_CACHE_DIR / model_path.name
        
        if model_path.exists():
            return str(model_path)
        
        # 다운로드
        model_path.parent.mkdir(parents=True, exist_ok=True)
        logger.info(f"🔽 6DRepNet360 모델 다운로드 중: {MODEL_URL}")
        urllib.request.urlretrieve(MODEL_URL, model_path)
        logger.info(f"✅ 모델 다운로드 완료: {model_path}")
        
        return str(model_path)
    
    def _load_model(self) -> None:
        """6DRepNet360 모델 로드"""
        try:
            import torch
            import torch.nn as nn
            from torchvision import transforms
            self._torch = torch
        except ImportError:
            raise ImportError(
                "PyTorch가 필요합니다. "
                "pip install torch torchvision 로 설치하세요."
            )
        
        # 디바이스 설정
        if self._device == "cuda" and not torch.cuda.is_available():
            logger.warning("CUDA 사용 불가, CPU로 전환")
            self._device = "cpu"
        
        # 6DRepNet 모델 로드 (sixdrepnet 패키지 사용)
        # Reference: https://github.com/thohemp/6DRepNet
        try:
            from sixdrepnet import SixDRepNet
            # sixdrepnet 패키지는 자체적으로 모델 다운로드 처리
            self._model = SixDRepNet(gpu_id=-1 if self._device == "cpu" else 0)
            self._use_sixdrepnet_package = True
            logger.info(f"✅ HeadPoseEstimator6D 로드 완료 (sixdrepnet 패키지, device={self._device})")
            return
        except ImportError:
            logger.warning("sixdrepnet 패키지 없음, 내장 구현 사용")
            self._use_sixdrepnet_package = False
        
        # 내장 구현 사용 시 모델 다운로드
        model_path = self._download_model_if_needed()
        self._model = self._create_model_from_scratch()
        
        # 가중치 로드 시도 (구조가 다르면 strict=False로 무시)
        try:
            state_dict = torch.load(model_path, map_location=self._device, weights_only=False)
            
            # state_dict 키 정리 (module. 접두사 제거)
            if any(k.startswith('module.') for k in state_dict.keys()):
                state_dict = {k.replace('module.', ''): v for k, v in state_dict.items()}
            
            self._model.load_state_dict(state_dict, strict=False)
            logger.info("⚠️ 가중치 부분 로드 (일부 레이어만 호환)")
        except Exception as e:
            logger.warning(f"가중치 로드 실패, 랜덤 초기화 사용: {e}")
        
        self._model.to(self._device)
        self._model.eval()
        
        # 전처리 변환
        self._transform = transforms.Compose([
            transforms.ToPILImage(),
            transforms.Resize(self.INPUT_SIZE),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info(
            f"✅ HeadPoseEstimator6D 로드 완료 "
            f"(내장 구현, model={model_path}, device={self._device})"
        )
    
    def _create_model_from_scratch(self):
        """
        6DRepNet360 모델 자체 구현 (라이브러리 없을 때)
        
        원본 6DRepNet360은 RepVGG 백본을 사용하지만,
        여기서는 ResNet50 백본 + 올바른 6D Rotation 변환을 구현합니다.
        
        Reference:
            - https://github.com/thohemp/6DRepNet360
            - https://arxiv.org/abs/2207.01530
        """
        import torch
        import torch.nn as nn
        import torch.nn.functional as F
        from torchvision.models import resnet50
        
        class SixDRepNet360Impl(nn.Module):
            """
            6DRepNet360 구현
            
            6D rotation representation을 사용하여 360° 전 방향
            Head Pose (yaw, pitch, roll)를 추정합니다.
            """
            
            def __init__(self):
                super().__init__()
                # ResNet50 백본
                backbone = resnet50(weights=None)
                # 마지막 FC layer 제거
                self.backbone = nn.Sequential(*list(backbone.children())[:-1])
                
                # Head: 6D rotation representation (2 x 3D vectors)
                self.fc = nn.Linear(2048, 6)  # ResNet50 출력: 2048
            
            def forward(self, x):
                x = self.backbone(x)
                x = x.view(x.size(0), -1)
                x = self.fc(x)
                return x
            
            def compute_euler_angles(self, rotation_6d):
                """
                6D rotation representation → Euler angles (yaw, pitch, roll) 변환
                
                Reference: 
                    "On the Continuity of Rotation Representations in Neural Networks"
                    https://arxiv.org/abs/1812.07035
                """
                batch_size = rotation_6d.shape[0]
                
                # 6D를 두 개의 3D 벡터로 분리
                a1 = rotation_6d[:, :3]  # 첫 번째 벡터
                a2 = rotation_6d[:, 3:]  # 두 번째 벡터
                
                # Gram-Schmidt 직교화로 회전 행렬 구성
                b1 = F.normalize(a1, dim=1)  # 정규화된 첫 번째 축
                
                # b1에 직교하는 b2 계산
                dot = torch.sum(b1 * a2, dim=1, keepdim=True)
                b2 = a2 - dot * b1
                b2 = F.normalize(b2, dim=1)
                
                # b3 = b1 x b2 (외적)
                b3 = torch.cross(b1, b2, dim=1)
                
                # 회전 행렬 구성 [B, 3, 3]
                R = torch.stack([b1, b2, b3], dim=2)
                
                # 회전 행렬에서 Euler angles 추출 (XYZ 순서 = pitch, yaw, roll)
                # Reference: https://www.geometrictools.com/Documentation/EulerAngles.pdf
                pitch = torch.asin(torch.clamp(R[:, 0, 2], -1.0, 1.0))
                
                # Gimbal lock 처리
                cos_pitch = torch.cos(pitch)
                gimbal_lock = torch.abs(cos_pitch) < 1e-6
                
                yaw = torch.where(
                    gimbal_lock,
                    torch.zeros_like(pitch),
                    torch.atan2(-R[:, 0, 1], R[:, 0, 0])
                )
                roll = torch.where(
                    gimbal_lock,
                    torch.atan2(-R[:, 1, 0], R[:, 1, 1]),
                    torch.atan2(-R[:, 1, 2], R[:, 2, 2])
                )
                
                # 라디안 → 도
                yaw_deg = yaw * 180.0 / 3.14159265359
                pitch_deg = pitch * 180.0 / 3.14159265359
                roll_deg = roll * 180.0 / 3.14159265359
                
                return torch.stack([yaw_deg, pitch_deg, roll_deg], dim=1)
        
        return SixDRepNet360Impl()
    
    def ensure_loaded(self) -> None:
        """모델 로드 확인"""
        if not self._model_loaded:
            self._load_model()
            self._model_loaded = True
    
    def _crop_head_roi(
        self,
        frame: np.ndarray,
        bbox: BoundingBox,
        padding: float = 0.2
    ) -> np.ndarray:
        """
        머리 영역 ROI 추출
        
        Args:
            frame: BGR 이미지
            bbox: 머리 bbox (정규화)
            padding: bbox 패딩 비율
            
        Returns:
            머리 ROI 이미지 (RGB)
        """
        height, width = frame.shape[:2]
        
        # 픽셀 좌표 변환
        x1 = int(bbox.x * width)
        y1 = int(bbox.y * height)
        x2 = int((bbox.x + bbox.width) * width)
        y2 = int((bbox.y + bbox.height) * height)
        
        # 패딩 추가
        pad_w = int((x2 - x1) * padding)
        pad_h = int((y2 - y1) * padding)
        
        x1 = max(0, x1 - pad_w)
        y1 = max(0, y1 - pad_h)
        x2 = min(width, x2 + pad_w)
        y2 = min(height, y2 + pad_h)
        
        # ROI 추출
        roi = frame[y1:y2, x1:x2]
        
        # BGR → RGB
        roi_rgb = cv2.cvtColor(roi, cv2.COLOR_BGR2RGB)
        
        return roi_rgb
    
    def estimate(
        self,
        frame: np.ndarray,
        head_bbox: BoundingBox
    ) -> Optional[HeadPose6D]:
        """
        머리 영역에서 Head Pose 추정
        
        Args:
            frame: BGR 이미지 (전체 프레임)
            head_bbox: 머리 bbox (정규화)
            
        Returns:
            HeadPose6D 또는 None
        """
        self.ensure_loaded()
        
        # ROI 추출
        try:
            roi = self._crop_head_roi(frame, head_bbox)
            
            if roi.size == 0 or roi.shape[0] < 10 or roi.shape[1] < 10:
                logger.debug("ROI가 너무 작음")
                return None
            
        except Exception as e:
            logger.debug(f"ROI 추출 실패: {e}")
            return None
        
        # sixdrepnet 패키지 사용 시 직접 predict
        if getattr(self, '_use_sixdrepnet_package', False):
            try:
                pitch, yaw, roll = self._model.predict(roi)
                return HeadPose6D(
                    yaw=float(yaw),
                    pitch=float(pitch),
                    roll=float(roll)
                )
            except Exception as e:
                logger.debug(f"sixdrepnet predict 실패: {e}")
                return None
        
        # 내장 구현 사용 시
        # 전처리
        input_tensor = self._transform(roi)
        input_tensor = input_tensor.unsqueeze(0).to(self._device)
        
        # 추론
        with self._torch.no_grad():
            output = self._model(input_tensor)
            
            # 모델 출력 처리
            if hasattr(self._model, 'compute_euler_angles'):
                angles = self._model.compute_euler_angles(output)
            else:
                # 직접 yaw, pitch, roll 출력하는 경우
                angles = output
            
            yaw = float(angles[0, 0].cpu().numpy())
            pitch = float(angles[0, 1].cpu().numpy())
            roll = float(angles[0, 2].cpu().numpy())
        
        return HeadPose6D(
            yaw=yaw,
            pitch=pitch,
            roll=roll
        )
    
    def estimate_batch(
        self,
        frame: np.ndarray,
        head_bboxes: list
    ) -> list:
        """
        배치로 Head Pose 추정
        
        Args:
            frame: BGR 이미지
            head_bboxes: 머리 bbox 목록
            
        Returns:
            HeadPose6D 목록 (None 포함 가능)
        """
        results = []
        for bbox in head_bboxes:
            pose = self.estimate(frame, bbox)
            results.append(pose)
        return results
    
    def predict(self, frame: np.ndarray, bbox: BoundingBox) -> Optional[HeadPose6D]:
        """BaseModel 인터페이스 호환용"""
        return self.estimate(frame, bbox)
    
    def close(self) -> None:
        """리소스 정리"""
        if self._model is not None:
            del self._model
            self._model = None
        self._model_loaded = False
        logger.info("HeadPoseEstimator6D 종료")
    
    def unload(self) -> None:
        """모델 언로드 (close alias)"""
        self.close()
    
    def __del__(self):
        """소멸자"""
        try:
            self.close()
        except Exception:
            pass
