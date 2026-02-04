import logging

import cv2
import numpy as np
import onnxruntime as ort

from app.rtn.config import YOLOConfig

logger = logging.getLogger("RTNAnalyzer.vision.yolo")


class YOLOFaceDetector:
    def __init__(self, cfg: YOLOConfig) -> None:
        self.cfg = cfg
        self.input_size = cfg.input_size
        self.conf_thres = cfg.conf_thres
        self.iou_thres = cfg.iou_thres

        logger.info("Initializing YOLOFaceDetector: model=%s", cfg.model_path)
        try:
            # CPU Provider priority
            providers = ["CPUExecutionProvider"]
            self.session = ort.InferenceSession(cfg.model_path, providers=providers)

            self.input_name = self.session.get_inputs()[0].name
            self.output_names = [o.name for o in self.session.get_outputs()]

            # Check input shape
            input_shape = self.session.get_inputs()[0].shape
            # Assuming [1, 3, 640, 640] or similar
            if isinstance(input_shape[2], int):
                self.input_size = input_shape[2]  # Update from model if fixed

            logger.info(
                "YOLOFaceDetector loaded. Inputs: %s, Outputs: %s",
                self.input_name,
                self.output_names,
            )
        except Exception as e:
            logger.error("Failed to load YOLO model: %s", e)
            raise RuntimeWarning(
                f"YOLO 모델 로드 실패: {cfg.model_path}. 파일이 존재하는지 확인하세요."
            ) from e

    def detect(
        self, img_bgr: np.ndarray
    ) -> list[tuple[float, float, float, float, float]]:
        """
        Args:
            img_bgr: (H, W, 3) BGR image
        Returns:
            list of (x1, y1, x2, y2, score)
        """
        # Preprocess
        img_h, img_w = img_bgr.shape[:2]
        img_in, ratio, (dw, dh) = self._letterbox(
            img_bgr, (self.input_size, self.input_size)
        )

        # BGR -> RGB, HWC -> CHW, 0-255 -> 0.0-1.0
        img_in = cv2.cvtColor(img_in, cv2.COLOR_BGR2RGB)
        img_in = img_in.transpose(2, 0, 1)  # HWC -> CHW
        img_in = np.ascontiguousarray(img_in, dtype=np.float32)
        img_in /= 255.0
        img_in = img_in[None, ...]  # Batch dimension

        # Inference
        outputs = self.session.run(self.output_names, {self.input_name: img_in})

        # Postprocess (assuming YOLOv8/v11 output format: [1, 5+kps, 8400])
        # output[0] shape: (1, 4+1+..., 8400)
        # cx, cy, w, h, score, ...

        preds = outputs[0]  # (1, C, N)
        preds = preds[0].transpose(1, 0)  # (N, C)

        # Filter by confidence
        # Index 4 is usually score for single class, or 4... for multiple
        # For face detection (1 class), usage might vary.
        # Check standard YOLOv8 output: 0-3: box, 4: score (if 1 class)
        # Let's assume index 4 is score.
        mask = preds[:, 4] > self.conf_thres
        preds = preds[mask]

        if len(preds) == 0:
            return []

        boxes = preds[:, :4]  # cx, cy, w, h
        scores = preds[:, 4]

        # Convert xywh -> xyxy
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

        results = []
        if len(indices) > 0:
            for i in indices.flatten():
                # Rescale boxes to original image
                box = boxes_xyxy[i]

                # Undo letterbox
                # x = (x - dw) / ratio
                # y = (y - dh) / ratio
                x1 = (box[0] - dw) / ratio
                y1 = (box[1] - dh) / ratio
                x2 = (box[2] - dw) / ratio
                y2 = (box[3] - dh) / ratio

                # Clip
                x1 = max(0, min(x1, img_w))
                y1 = max(0, min(y1, img_h))
                x2 = max(0, min(x2, img_w))
                y2 = max(0, min(y2, img_h))

                score = float(scores[i])
                results.append((float(x1), float(y1), float(x2), float(y2), score))

        return results

    def _letterbox(
        self,
        im: np.ndarray,
        new_shape: tuple[int, int] = (640, 640),
        color: tuple[int, int, int] = (114, 114, 114),
    ) -> tuple[np.ndarray, float, tuple[float, float]]:
        # Resize and pad image while meeting stride-multiple constraints
        shape = im.shape[:2]  # current shape [height, width]
        if isinstance(new_shape, int):
            new_shape = (new_shape, new_shape)

        # Scale ratio (new / old)
        r = min(new_shape[0] / shape[0], new_shape[1] / shape[1])
        # Compute padding
        new_unpad = int(round(shape[1] * r)), int(round(shape[0] * r))
        dw, dh = new_shape[1] - new_unpad[0], new_shape[0] - new_unpad[1]  # wh padding

        dw /= 2  # divide padding into 2 sides
        dh /= 2

        if shape[::-1] != new_unpad:  # resize
            im = cv2.resize(im, new_unpad, interpolation=cv2.INTER_LINEAR)

        top, bottom = int(round(dh - 0.1)), int(round(dh + 0.1))
        left, right = int(round(dw - 0.1)), int(round(dw + 0.1))
        im = cv2.copyMakeBorder(
            im, top, bottom, left, right, cv2.BORDER_CONSTANT, value=color
        )  # add border

        return im, r, (left, top)
