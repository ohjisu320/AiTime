# AI/services/pose-estimation/app/vitpose.py
"""
VitPose 모델 로딩 및 추론 로직

2단계 추론 파이프라인(Top-down)
1. RT-DETR로 사람 감지
2. ViTPose로 자세 추정
"""

import torch
import numpy as np
from PIL import Image
import supervision as sv
from transformers import AutoProcessor, RTDetrForObjectDetection, VitPoseForPoseEstimation

from app.config import settings

class PoseModel:
    """싱글톤"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            # 아직 만들어진 게 없으면 새로 만들고 초기화
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance # 이미 있으면 있는 거 반환
    
    def _initialize(self):
        """
        모델 초기화
        - 연산 장치(CPU/GPU) 설정
        - 사람 감지 모델(RT-DETR) 로드
        - 자세 추정 모델(ViTPose) 로드
        """
        self.device = torch.device(
            settings.DEVICE if torch.cuda.is_available() else "cpu"
        )
        print(f"✅ 사용 중인 디바이스: {self.device}")
        
        # RT-DETR (사람 감지)
        print(f"✅ 사람 감지 모델 로딩 중입니다: {settings.PERSON_DETECTOR}")
        self.person_processor = AutoProcessor.from_pretrained(settings.PERSON_DETECTOR)
        self.person_model = RTDetrForObjectDetection.from_pretrained(
            settings.PERSON_DETECTOR, device_map=self.device
        )
        
        # ViTPose (자세 추정)
        print(f"✅ 포즈 모델 로딩 중입니다: {settings.POSE_MODEL}")
        self.pose_processor = AutoProcessor.from_pretrained(settings.POSE_MODEL)
        self.pose_model = VitPoseForPoseEstimation.from_pretrained(
            settings.POSE_MODEL, device_map=self.device
        )
        
        print("✅ 성공적으로 로드되었습니다!")
    
    @torch.inference_mode()
    def detect(self, image: Image.Image, threshold: float = 0.3) -> list[dict]:
        """
        이미지에서 사람 감지 및 자세 추정
        
        Args:
            image: PIL 이미지
            threshold: 감지 신뢰도 임계값
            
        Returns:
            list[dict]: 감지된 사람별 자세 정보
        """
        # 1. Person Detection
        # 사람 바운딩 박스 검출
        inputs = self.person_processor(images=image, return_tensors="pt").to(self.device)
        outputs = self.person_model(**inputs)
        results = self.person_processor.post_process_object_detection(
            outputs,
            target_sizes=torch.tensor([(image.height, image.width)]),
            threshold=threshold
        )
        result = results[0]
        
        # Supervision 라이브러리 사용해서
        # 감지된 객체 중 '사람(class_id == 0)'만 필터링하고,
        # 좌표 형식을 XYXY(좌상단,우하단) -> XYWH(중심x,중심y,너비,높이)로 변환
        # (ViTPose 프로세서가 박스 입력을 받을 때 포맷을 맞추기 위함)
        detections = sv.Detections.from_transformers(result)
        person_detections_xywh = sv.xyxy_to_xywh(detections[detections.class_id == 0].xyxy)
        
        if len(person_detections_xywh) == 0:
            return []
        
        # 2. Pose Estimation
        inputs = self.pose_processor(
            image, boxes=[person_detections_xywh], return_tensors="pt"
        ).to(self.device)
        
        # MoE 모델인 경우 dataset_index 추가
        if self.pose_model.config.backbone_config.num_experts > 1:
            dataset_index = torch.tensor([0] * len(inputs["pixel_values"]))
            inputs["dataset_index"] = dataset_index.to(self.device)
        
        outputs = self.pose_model(**inputs)
        pose_results = self.pose_processor.post_process_pose_estimation(
            outputs, boxes=[person_detections_xywh]
        )
        
        # 3. Format Results
        return self._format_results(pose_results[0])
    
    def _format_results(self, pose_results: list) -> list[dict]:
        """결과를 JSON 직렬화 가능한 형태로 변환"""
        results = []
        
        for i, person_pose in enumerate(pose_results):
            data = {
                "person_id": i,
                "bbox": person_pose["bbox"].numpy().tolist(),
                "keypoints": []
            }
            
            for keypoint, label, score in zip(
                person_pose["keypoints"],
                person_pose["labels"],
                person_pose["scores"],
                strict=True
            ):
                keypoint_name = self.pose_model.config.id2label[label.item()]
                x, y = keypoint
                data["keypoints"].append({
                    "name": keypoint_name,
                    "x": float(x.item()),
                    "y": float(y.item()),
                    "score": float(score.item())
                })
            
            results.append(data)
        
        return results


# 싱글톤 인스턴스 (import 시 자동 로딩하지 않음)
_model: PoseModel | None = None


def get_model() -> PoseModel:
    """모델 인스턴스 반환 (지연 로딩)"""
    global _model
    if _model is None:
        _model = PoseModel()
    return _model