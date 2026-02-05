import logging

import cv2
import numpy as np

try:
    from openvino import Core

    OPENVINO_AVAILABLE = True
except ImportError:
    OPENVINO_AVAILABLE = False

from app.rtn.config import YOLOConfig

logger = logging.getLogger("RTNAnalyzer.vision.openvino")


class OpenVINOFaceDetector:
    def __init__(self, cfg: YOLOConfig) -> None:
        if not OPENVINO_AVAILABLE:
            raise RuntimeError(
                "OpenVINO not found. Please install proper package (e.g. pip install openvino)."
            )

        self.cfg = cfg
        self.input_size = cfg.input_size
        self.conf_thres = cfg.conf_thres
        self.iou_thres = cfg.iou_thres

        logger.info("Initializing OpenVINOFaceDetector: model=%s", cfg.model_path)

        try:
            self.core = Core()
            # ONNX 파일을 직접 읽을 수 있음
            self.model = self.core.read_model(cfg.model_path)

            # Dynamic shape 오류 해결을 위해 입력 크기 고정
            # YOLOv11n-face: [1, 3, 640, 640]
            if len(self.model.inputs) > 0:
                input_node = self.model.inputs[0]
                self.model.reshape(
                    {input_node.any_name: [1, 3, self.input_size, self.input_size]}
                )

            self.compiled_model = self.core.compile_model(self.model, "CPU")
            self.infer_request = self.compiled_model.create_infer_request()

            # 입출력 정보
            self.input_layer = self.compiled_model.input(0)
            self.output_layer = self.compiled_model.output(0)

            logger.info(
                "OpenVINO model compiled on CPU (Reshaped to %dx%d).",
                self.input_size,
                self.input_size,
            )

            self.input_size_h = self.input_size
            self.input_size_w = self.input_size

        except Exception as e:
            logger.error("Failed to load OpenVINO model: %s", e)
            raise RuntimeWarning(f"OpenVINO 모델 로드 실패: {cfg.model_path}") from e

    def detect(
        self, img_bgr: np.ndarray
    ) -> list[tuple[float, float, float, float, float]]:
        """
        Args:
            img_bgr: (H, W, 3) BGR image
        Returns:
            list of (x1, y1, x2, y2, score)
        """
        img_h, img_w = img_bgr.shape[:2]

        # Preprocess (Letterbox)
        img_in, r, (dw, dh) = self._letterbox(
            img_bgr, (self.input_size_w, self.input_size_h)
        )

        # BGR->RGB, HWC->CHW, Normalize
        img_in = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB)
        img_in = img_in.transpose(2, 0, 1)
        img_in = np.ascontiguousarray(img_in, dtype=np.float32)
        img_in /= 255.0
        img_in = img_in[None, ...]  # Batch dim

        # Inference
        results = self.infer_request.infer({self.input_layer: img_in})

        # Postprocess
        # output shape: (1, 5, 8400) for YOLO usually
        # output[0]
        preds = results[self.output_layer][0]  # (5, 8400) or similar

        # Transpose if needed: (8400, 5) makes it easier
        preds = preds.transpose(1, 0)

        # Filter by confidence (Assuming index 4 is score)
        mask = preds[:, 4] > self.conf_thres
        preds = preds[mask]

        if len(preds) == 0:
            return []

        boxes = preds[:, :4]  # cx, cy, w, h
        scores = preds[:, 4]

        # xywh -> xyxy
        boxes_xyxy = np.copy(boxes)
        boxes_xyxy[:, 0] = boxes[:, 0] - boxes[:, 2] / 2  # x1
        boxes_xyxy[:, 1] = boxes[:, 1] - boxes[:, 3] / 2  # y1
        boxes_xyxy[:, 2] = boxes[:, 0] + boxes[:, 2] / 2  # x2
        boxes_xyxy[:, 3] = boxes[:, 1] + boxes[:, 3] / 2  # y2

        # NMS
        indices = cv2.dnn.NMSBoxes(
            bboxes=boxes_xyxy.tolist(),
            scores=scores.tolist(),
            score_threshold=self.conf_thres,
            nms_threshold=self.iou_thres,
        )

        results_list = []
        if len(indices) > 0:
            for i in indices.flatten():
                box = boxes_xyxy[i]

                # Undo letterbox
                x1 = (box[0] - dw) / r
                y1 = (box[1] - dh) / r
                x2 = (box[2] - dw) / r
                y2 = (box[3] - dh) / r

                # Clip
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))

                score = float(scores[i])
                results_list.append((float(x1), float(y1), float(x2), float(y2), score))

        return results_list

    def _letterbox(
        self,
        im: np.ndarray,
        new_shape: tuple[int, int] = (640, 640),
        color: tuple[int, int, int] = (114, 114, 114),
    ) -> tuple[np.ndarray, float, tuple[float, float]]:
        shape = im.shape[:2]  # [height, width]

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])

        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]

        dw /= 2
        dh /= 2

        if shape[::-1] != new_unpad:
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(
            im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )
        return im, r, (left, top)
