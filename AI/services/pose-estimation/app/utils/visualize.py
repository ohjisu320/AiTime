# AI/services/pose-estimation/app/utils/visualize.py
"""스켈레톤 시각화 유틸리티 - 신체 부위별 색상 구분"""

"""
'face': 빨강        # 얼굴 (코, 눈, 귀)
'upper_body': 초록  # 상체 (어깨, 팔꿈치, 손목)
'torso': 파랑       # 몸통 (어깨-골반 연결)
'lower_body': 노랑  # 하체 (골반, 무릎, 발목)

얼굴: 3px (가늘게)
상체/하체: 4px (중간)
몸통: 5px (굵게, 중심 강조)
"""
import cv2
import numpy as np
from PIL import Image

# ============================================================================
# 설정 상수
# ============================================================================

# 신체 부위별 스켈레톤 연결 그룹
SKELETON_PARTS = {
    'face': [
        (0, 1), (0, 2),  # nose - eyes
        (1, 3), (2, 4),  # eyes - ears
    ],
    'upper_body': [
        (5, 6),          # shoulders
        (5, 7), (7, 9),  # left arm
        (6, 8), (8, 10), # right arm
    ],
    'torso': [
        (5, 11), (6, 12),  # shoulders - hips
        (11, 12),          # hip connection
    ],
    'lower_body': [
        (11, 13), (13, 15),  # left leg
        (12, 14), (14, 16),  # right leg
    ],
}

# 부위별 색상 (BGR 형식)
PART_COLORS = {
    'face': (0, 0, 255),        # 빨강
    'upper_body': (0, 255, 0),  # 초록
    'torso': (255, 0, 0),       # 파랑
    'lower_body': (0, 255, 255),# 노랑
}

# 부위별 선 두께
PART_THICKNESS = {
    'face': 3,
    'upper_body': 4,
    'torso': 5,
    'lower_body': 4,
}

# 키포인트 이름 순서 (ViTPose 모델이 반환하는 실제 이름)
KEYPOINT_NAMES = [
    "Nose", "L_Eye", "R_Eye", "L_Ear", "R_Ear",
    "L_Shoulder", "R_Shoulder", "L_Elbow", "R_Elbow",
    "L_Wrist", "R_Wrist", "L_Hip", "R_Hip",
    "L_Knee", "R_Knee", "L_Ankle", "R_Ankle"
]

# 키포인트 -> 부위 매핑 (자동 생성)
def _build_keypoint_part_mapping():
    """스켈레톤 연결 정보로부터 키포인트-부위 매핑 생성"""
    mapping = {}
    for part_name, connections in SKELETON_PARTS.items():
        for start_idx, end_idx in connections:
            mapping[start_idx] = part_name
            mapping[end_idx] = part_name
    return mapping

KEYPOINT_TO_PART = _build_keypoint_part_mapping()

# 시각화 설정
KEYPOINT_THRESHOLD = 0.1
BBOX_COLOR = (255, 255, 255)  # 흰색
BBOX_THICKNESS = 2
KEYPOINT_RADIUS = 6
KEYPOINT_INNER_RADIUS = 4
KEYPOINT_OUTLINE_COLOR = (255, 255, 255)
OVERLAY_ALPHA = 0.7  # 투명도

# ============================================================================
# 시각화 함수
# ============================================================================

def draw_skeleton(
    image: Image.Image,
    results: list[dict],
    keypoint_threshold: float = KEYPOINT_THRESHOLD,
    show_bbox: bool = True,
    show_keypoints: bool = True,
    show_frame: bool = True
) -> Image.Image:
    """
    이미지에 색상 구분된 스켈레톤 시각화
    
    Args:
        image: PIL 이미지
        results: detect() 반환값
        keypoint_threshold: 키포인트 표시 최소 신뢰도
        show_bbox: 바운딩 박스 그리기 여부 (RT-DETR bbox 사용)
        show_keypoints: 키포인트 그리기 여부
        show_frame: 스켈레톤 그리기 여부
    
    Returns:
        스켈레톤이 그려진 PIL 이미지
    """
    # PIL -> OpenCV (RGB -> BGR)
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    
    # 반투명 오버레이를 위한 레이어
    overlay = img.copy()
    
    for person in results:
        keypoints = person["keypoints"]
        
        # 키포인트를 dict로 변환 (name -> {x, y, score})
        kp_dict = {kp["name"]: kp for kp in keypoints}
        
        # 1. 바운딩 박스 그리기 (RT-DETR bbox 사용)
        if show_bbox:
            _draw_bbox(overlay, person)
        
        # 2. 색상 구분된 스켈레톤 그리기
        if show_frame:
            _draw_skeleton_lines(overlay, kp_dict, keypoint_threshold)
        
        # 3. 키포인트 그리기 (부위별 색상)
        if show_keypoints:
            _draw_keypoints(overlay, keypoints, keypoint_threshold)
    
    # 오버레이 블렌딩 (약간 투명하게)
    img = cv2.addWeighted(overlay, OVERLAY_ALPHA, img, 1 - OVERLAY_ALPHA, 0)
    
    # OpenCV -> PIL (BGR -> RGB)
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def _draw_bbox(overlay: np.ndarray, person: dict) -> None:
    """바운딩 박스 및 Person ID 라벨 그리기"""
    bbox = person["bbox"]
    # XYWH (center_x, center_y, width, height) -> XYXY (x1, y1, x2, y2)
    center_x, center_y, w, h = bbox
    x1 = int(center_x - w / 2)
    y1 = int(center_y - h / 2)
    x2 = int(center_x + w / 2)
    y2 = int(center_y + h / 2)
    
    # 박스 그리기
    cv2.rectangle(overlay, (x1, y1), (x2, y2), BBOX_COLOR, BBOX_THICKNESS)
    
    # Person ID 라벨 배경
    text = f"Person {person['person_id']}"
    text_size = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
    cv2.rectangle(
        overlay, 
        (x1, max(0, y1 - text_size[1] - 10)),
        (x1 + text_size[0] + 10, y1),
        BBOX_COLOR,
        -1
    )
    cv2.putText(
        overlay, text, 
        (x1 + 5, max(text_size[1], y1 - 5)), 
        cv2.FONT_HERSHEY_SIMPLEX, 
        0.6, (0, 0, 0), 2
    )


def _draw_skeleton_lines(
    overlay: np.ndarray, 
    kp_dict: dict, 
    threshold: float
) -> None:
    """부위별 색상 구분된 스켈레톤 선 그리기"""
    for part_name, connections in SKELETON_PARTS.items():
        color = PART_COLORS[part_name]
        thickness = PART_THICKNESS[part_name]
        
        for start_idx, end_idx in connections:
            start_name = KEYPOINT_NAMES[start_idx]
            end_name = KEYPOINT_NAMES[end_idx]
            
            if start_name not in kp_dict or end_name not in kp_dict:
                continue
            
            start_kp = kp_dict[start_name]
            end_kp = kp_dict[end_name]
            
            # 신뢰도 체크
            if start_kp["score"] < threshold or end_kp["score"] < threshold:
                continue
            
            pt1 = (int(start_kp["x"]), int(start_kp["y"]))
            pt2 = (int(end_kp["x"]), int(end_kp["y"]))
            
            # 스켈레톤 선 그리기
            cv2.line(overlay, pt1, pt2, color, thickness)


def _draw_keypoints(
    overlay: np.ndarray, 
    keypoints: list[dict], 
    threshold: float
) -> None:
    """부위별 색상이 적용된 키포인트 그리기"""
    for kp in keypoints:
        if kp["score"] < threshold:
            continue
        
        x, y = int(kp["x"]), int(kp["y"])
        
        # 키포인트 인덱스 찾기
        kp_idx = KEYPOINT_NAMES.index(kp["name"])
        part_name = KEYPOINT_TO_PART.get(kp_idx, 'upper_body')
        color = PART_COLORS[part_name]
        
        # 외곽선이 있는 원
        cv2.circle(overlay, (x, y), KEYPOINT_RADIUS, KEYPOINT_OUTLINE_COLOR, -1)
        cv2.circle(overlay, (x, y), KEYPOINT_INNER_RADIUS, color, -1)


# ============================================================================
# 역할별 시각화 (부모/아이 구분)
# ============================================================================

# 역할별 색상 정의 (BGR)
ROLE_COLORS = {
    "parent": {
        "primary": (255, 150, 0),     # 파란색 계열
        "secondary": (255, 200, 100), # 하늘색
        "label_bg": (200, 100, 0),    # 진한 파랑
    },
    "child": {
        "primary": (0, 128, 255),     # 주황색 계열
        "secondary": (0, 200, 255),   # 노란색
        "label_bg": (0, 80, 200),     # 진한 주황
    }
}


def draw_skeleton_with_role(
    image: Image.Image,
    results: list[dict],
    role: str = "child",
    keypoint_threshold: float = KEYPOINT_THRESHOLD,
    show_bbox: bool = True,
    show_keypoints: bool = True,
    show_label: bool = True
) -> Image.Image:
    """
    역할에 따라 다른 색상으로 스켈레톤 그리기.
    
    Args:
        image: PIL 이미지
        results: detect() 반환값 (person list)
        role: "parent" 또는 "child"
        keypoint_threshold: 키포인트 표시 최소 신뢰도
        show_bbox: 바운딩 박스 그리기 여부
        show_keypoints: 키포인트 그리기 여부
        show_label: 역할 라벨 표시 여부
    
    Returns:
        스켈레톤이 그려진 PIL 이미지
    """
    # PIL -> OpenCV (RGB -> BGR)
    img = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
    overlay = img.copy()
    
    colors = ROLE_COLORS.get(role, ROLE_COLORS["child"])
    
    for person in results:
        keypoints = person["keypoints"]
        kp_dict = {kp["name"]: kp for kp in keypoints}
        
        # 1. 바운딩 박스 (역할 색상)
        if show_bbox:
            _draw_bbox_with_role(overlay, person, colors, role, show_label)
        
        # 2. 스켈레톤 선 (역할 색상)
        _draw_skeleton_lines_with_role(overlay, kp_dict, keypoint_threshold, colors)
        
        # 3. 키포인트 (역할 색상)
        if show_keypoints:
            _draw_keypoints_with_role(overlay, keypoints, keypoint_threshold, colors)
    
    # 오버레이 블렌딩
    img = cv2.addWeighted(overlay, OVERLAY_ALPHA, img, 1 - OVERLAY_ALPHA, 0)
    
    return Image.fromarray(cv2.cvtColor(img, cv2.COLOR_BGR2RGB))


def _draw_bbox_with_role(
    overlay: np.ndarray, 
    person: dict, 
    colors: dict,
    role: str,
    show_label: bool
) -> None:
    """역할 색상이 적용된 바운딩 박스 그리기"""
    bbox = person["bbox"]
    center_x, center_y, w, h = bbox
    x1 = int(center_x - w / 2)
    y1 = int(center_y - h / 2)
    x2 = int(center_x + w / 2)
    y2 = int(center_y + h / 2)
    
    # 박스 그리기
    cv2.rectangle(overlay, (x1, y1), (x2, y2), colors["primary"], 3)
    
    # 역할 라벨
    if show_label:
        label = "P" if role == "parent" else "C"
        label_text = f"{label}"
        
        text_size = cv2.getTextSize(label_text, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)[0]
        label_x = x1
        label_y = max(0, y1 - 5)
        
        # 라벨 배경
        cv2.rectangle(
            overlay,
            (label_x, label_y - text_size[1] - 10),
            (label_x + text_size[0] + 10, label_y),
            colors["label_bg"],
            -1
        )
        # 라벨 텍스트
        cv2.putText(
            overlay, label_text,
            (label_x + 5, label_y - 5),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8, (255, 255, 255), 2
        )


def _draw_skeleton_lines_with_role(
    overlay: np.ndarray,
    kp_dict: dict,
    threshold: float,
    colors: dict
) -> None:
    """역할 색상이 적용된 스켈레톤 선 그리기"""
    # 모든 부위를 동일한 역할 색상으로
    for part_name, connections in SKELETON_PARTS.items():
        thickness = PART_THICKNESS[part_name]
        
        for start_idx, end_idx in connections:
            start_name = KEYPOINT_NAMES[start_idx]
            end_name = KEYPOINT_NAMES[end_idx]
            
            if start_name not in kp_dict or end_name not in kp_dict:
                continue
            
            start_kp = kp_dict[start_name]
            end_kp = kp_dict[end_name]
            
            if start_kp["score"] < threshold or end_kp["score"] < threshold:
                continue
            
            pt1 = (int(start_kp["x"]), int(start_kp["y"]))
            pt2 = (int(end_kp["x"]), int(end_kp["y"]))
            
            cv2.line(overlay, pt1, pt2, colors["primary"], thickness)


def _draw_keypoints_with_role(
    overlay: np.ndarray,
    keypoints: list[dict],
    threshold: float,
    colors: dict
) -> None:
    """역할 색상이 적용된 키포인트 그리기"""
    for kp in keypoints:
        if kp["score"] < threshold:
            continue
        
        x, y = int(kp["x"]), int(kp["y"])
        
        cv2.circle(overlay, (x, y), KEYPOINT_RADIUS, (255, 255, 255), -1)
        cv2.circle(overlay, (x, y), KEYPOINT_INNER_RADIUS, colors["secondary"], -1)


def draw_multi_person_skeleton(
    image: Image.Image,
    parent_results: list[dict] = None,
    child_results: list[dict] = None,
    keypoint_threshold: float = KEYPOINT_THRESHOLD,
    show_bbox: bool = True,
    show_keypoints: bool = True,
    show_label: bool = True,
    show_child_face: bool = True
) -> Image.Image:
    """
    부모와 아이를 다른 색상으로 동시에 그리기.
    
    Args:
        image: PIL 이미지
        parent_results: 부모 자세 데이터 (없으면 None)
        child_results: 아이 자세 데이터
        keypoint_threshold: 키포인트 표시 최소 신뢰도
        show_bbox: 바운딩 박스 그리기 여부
        show_keypoints: 키포인트 그리기 여부
        show_label: 역할 라벨 표시 여부
        show_child_face: 아이 얼굴 영역 표시 여부
    
    Returns:
        스켈레톤이 그려진 PIL 이미지
    """
    result_image = image
    
    # 부모 먼저 그리기 (뒤에 위치)
    if parent_results:
        result_image = draw_skeleton_with_role(
            result_image, parent_results, role="parent",
            keypoint_threshold=keypoint_threshold,
            show_bbox=show_bbox,
            show_keypoints=show_keypoints,
            show_label=show_label
        )
    
    # 아이 그리기 (앞에 위치)
    if child_results:
        result_image = draw_skeleton_with_role(
            result_image, child_results, role="child",
            keypoint_threshold=keypoint_threshold,
            show_bbox=show_bbox,
            show_keypoints=show_keypoints,
            show_label=show_label
        )
        
        # 아이 얼굴 영역 표시 (핑크색 박스)
        if show_child_face:
            result_image = _draw_child_face_box(result_image, child_results, keypoint_threshold)
    
    return result_image


def _draw_child_face_box(
    image: Image.Image,
    child_results: list[dict],
    threshold: float
) -> Image.Image:
    """
    아이 얼굴 영역에 핑크색 박스 그리기.
    
    Args:
        image: PIL 이미지
        child_results: 아이 자세 데이터
        threshold: 키포인트 신뢰도 임계값
        
    Returns:
        얼굴 박스가 그려진 PIL 이미지
    """
    from PIL import ImageDraw, ImageFont
    
    draw = ImageDraw.Draw(image)
    
    for person in child_results:
        keypoints = person["keypoints"]
        kp_dict = {kp["name"]: kp for kp in keypoints}
        
        # 얼굴 키포인트 추출 (코, 눈, 귀)
        face_keypoints = []
        for key in ["Nose", "L_Eye", "R_Eye", "L_Ear", "R_Ear"]:
            if key in kp_dict and kp_dict[key]["score"] > threshold:
                face_keypoints.append((kp_dict[key]["x"], kp_dict[key]["y"]))
        
        if len(face_keypoints) >= 2:  # 최소 2개 이상의 키포인트
            xs = [p[0] for p in face_keypoints]
            ys = [p[1] for p in face_keypoints]
            x_min, x_max = min(xs), max(xs)
            y_min, y_max = min(ys), max(ys)
            
            # 얼굴 영역 확장 (여유 공간 추가)
            margin_x = (x_max - x_min) * 0.1
            margin_y = (y_max - y_min) * 1.4
            
            x1 = int(max(0, x_min - margin_x))
            y1 = int(max(0, y_min - margin_y))
            x2 = int(min(image.width, x_max + margin_x))
            y2 = int(min(image.height, y_max + margin_y))
            
            # 핑크색 박스 그리기 (255, 105, 180)
            draw.rectangle([x1, y1, x2, y2], outline=(255, 105, 180), width=3)
            
            # 라벨
            try:
                font = ImageFont.truetype("arial.ttf", 16)
            except:
                font = ImageFont.load_default()
            draw.text((x1, y1 - 20), "Child Face", fill=(255, 105, 180), font=font)
    
    return image