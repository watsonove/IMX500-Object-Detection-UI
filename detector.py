#!/usr/bin/env python3
# imx500_gui/detector.py

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import List, Tuple, Optional, Dict, Any
import sys

import numpy as np

from picamera2 import Picamera2
from picamera2.devices.imx500 import IMX500, NetworkIntrinsics, postprocess_nanodet_detection  # type: ignore


RAW_TOPK = 20  # raw candidates to show in Student Step 5/6


@dataclass(frozen=True)
class Det:
    label: str
    conf: float
    box: Tuple[int, int, int, int]  # (x, y, w, h) in stream coords


@dataclass
class FrameSnapshot:
    frame_rgb: Optional[np.ndarray] = None
    src_size: Tuple[int, int] = (1280, 720)  # (w, h)

    dets: List[Det] = None          # filtered detections (>= threshold), sorted desc
    raw_dets: List[Det] = None      # raw Top-K before threshold, sorted desc

    top3: List[Tuple[str, float]] = None
    top_dets: List[Det] = None

    debug: Dict[str, Any] = None

    def __post_init__(self) -> None:
        self.dets = self.dets or []
        self.raw_dets = self.raw_dets or []
        self.top3 = self.top3 or []
        self.top_dets = self.top_dets or []
        self.debug = self.debug or {}


class IMX500Detector:
    def __init__(self, args):
        self.args = args
        self.imx500 = IMX500(args.model)
        self.intrinsics: NetworkIntrinsics = self.imx500.network_intrinsics

        self._init_intrinsics()
        self.picam2 = self._init_camera()

    def _init_intrinsics(self) -> None:
        intr = self.intrinsics
        if not intr:
            intr = NetworkIntrinsics()
            intr.task = "object detection"
            self.intrinsics = intr
        elif intr.task != "object detection":
            print("Network is not an object detection task.", file=sys.stderr)
            sys.exit(1)

        if getattr(self.args, "labels", None):
            with open(self.args.labels, "r", encoding="utf-8") as f:
                intr.labels = f.read().splitlines()

        if getattr(self.args, "bbox_normalization", None) is not None:
            intr.bbox_normalization = self.args.bbox_normalization
        if getattr(self.args, "bbox_order", None) is not None:
            intr.bbox_order = self.args.bbox_order
        if getattr(self.args, "preserve_aspect_ratio", None) is not None:
            intr.preserve_aspect_ratio = self.args.preserve_aspect_ratio

        if getattr(self.args, "postprocess", None) is not None:
            pp = self.args.postprocess if self.args.postprocess != "" else ""
            intr.postprocess = pp

        if intr.labels is None:
            intr.labels = [f"Class {i}" for i in range(1000)]

        intr.update_with_defaults()

    def _init_camera(self) -> Picamera2:
        picam2 = Picamera2(self.imx500.camera_num)

        config = picam2.create_preview_configuration(
            main={"size": (self.args.cam_width, self.args.cam_height), "format": "RGB888"},
            controls={"FrameRate": self.intrinsics.inference_rate},
            buffer_count=6,
        )

        self.imx500.show_network_fw_progress_bar()
        picam2.configure(config)
        picam2.start()

        if self.intrinsics.preserve_aspect_ratio:
            self.imx500.set_auto_aspect_ratio()

        return picam2

    @lru_cache(maxsize=1)
    def get_labels(self) -> List[str]:
        labels = self.intrinsics.labels or []
        if getattr(self.intrinsics, "ignore_dash_labels", False):
            labels = [label for label in labels if label and label != "-"]
        return labels

    def _apply_bbox_normalization_and_order(
        self, boxes: np.ndarray, input_w: int, input_h: int
    ) -> np.ndarray:
        bbox_norm = bool(self.intrinsics.bbox_normalization) if self.intrinsics.bbox_normalization is not None else False
        bbox_order = self.intrinsics.bbox_order or "yx"

        out = np.array(boxes, dtype=np.float32, copy=True)

        if bbox_norm:
            if bbox_order == "yx":
                out[:, 0] *= input_h
                out[:, 1] *= input_w
                out[:, 2] *= input_h
                out[:, 3] *= input_w
            else:
                out[:, 0] *= input_w
                out[:, 1] *= input_h
                out[:, 2] *= input_w
                out[:, 3] *= input_h

        return out

    def _nanodet_xywh_center_to_xyxy(self, boxes_xywh_c: np.ndarray) -> np.ndarray:
        x_c = boxes_xywh_c[:, 0]
        y_c = boxes_xywh_c[:, 1]
        w = boxes_xywh_c[:, 2]
        h = boxes_xywh_c[:, 3]
        x0 = x_c - w / 2.0
        y0 = y_c - h / 2.0
        x1 = x_c + w / 2.0
        y1 = y_c + h / 2.0
        return np.stack([x0, y0, x1, y1], axis=1).astype(np.float32)

    def _map_to_int_xywh(self, mapped: Tuple[float, float, float, float]) -> Tuple[int, int, int, int]:
        x, y, w, h = mapped
        return int(x), int(y), int(w), int(h)

    def _safe_get_roi_and_scalercrop(
        self, metadata: Dict[str, Any]
    ) -> Tuple[Optional[Tuple[int, int, int, int]], Optional[Tuple[int, int, int, int]]]:
        roi = None
        sc = None

        try:
            b = self.imx500.get_roi_scaled(metadata)
            if isinstance(b, tuple) and len(b) == 4:
                roi = tuple(int(v) for v in b)
            else:
                roi = (int(b.x), int(b.y), int(b.width), int(b.height))
        except Exception:
            roi = None

        for k in ("ScalerCrop", "scaler_crop", "scalerCrop"):
            if k in metadata:
                v = metadata.get(k)
                try:
                    if isinstance(v, (list, tuple)) and len(v) == 4:
                        sc = tuple(int(x) for x in v)
                except Exception:
                    pass
                break

        return roi, sc

    def parse_detections(
        self, metadata: Dict[str, Any]
    ) -> Tuple[List[Det], List[Det], List[Tuple[str, float]], Dict[str, Any]]:
        threshold = float(self.args.threshold)
        iou = float(self.args.iou)
        max_detections = int(self.args.max_detections)

        np_outputs = self.imx500.get_outputs(metadata, add_batch=True)
        input_w, input_h = self.imx500.get_input_size()

        debug: Dict[str, Any] = {
            "threshold": threshold,
            "iou": iou,
            "max_detections": max_detections,
            "raw_topk": RAW_TOPK,
            "input_size": (input_w, input_h),
            "bbox_order": self.intrinsics.bbox_order,
            "bbox_normalization": self.intrinsics.bbox_normalization,
            "preserve_aspect_ratio": self.intrinsics.preserve_aspect_ratio,
            "postprocess": self.intrinsics.postprocess,
            "network_name": getattr(self.intrinsics, "network_name", None),
        }

        try:
            shapes = self.imx500.get_output_shapes(metadata)
            debug["output_shapes"] = [tuple(int(x) for x in s) for s in shapes] if shapes else None
        except Exception:
            debug["output_shapes"] = None

        roi, sc = self._safe_get_roi_and_scalercrop(metadata)
        debug["roi"] = roi
        debug["scaler_crop"] = sc

        if np_outputs is None:
            debug["raw_candidates"] = 0
            debug["kept"] = 0
            return [], [], [], debug

        labels = self.get_labels()

        raw_dets: List[Det] = []
        kept_dets: List[Det] = []

        if self.intrinsics.postprocess == "nanodet":
            boxes, scores, classes = postprocess_nanodet_detection(
                outputs=np_outputs[0],
                conf=0.0,
                iou_thres=iou,
                max_out_dets=max(max_detections, RAW_TOPK),
            )

            boxes = np.asarray(boxes)
            scores = np.asarray(scores)
            classes = np.asarray(classes)
            debug["raw_candidates"] = int(len(scores))

            boxes_xyxy = self._nanodet_xywh_center_to_xyxy(np.asarray(boxes, dtype=np.float32))

            for box_xyxy, score, category in zip(boxes_xyxy, scores, classes):
                conf = float(score)
                cat = int(category)
                name = labels[cat] if 0 <= cat < len(labels) else f"Class {cat}"

                mapped = self.imx500.convert_inference_coords(tuple(box_xyxy), metadata, self.picam2)
                det = Det(label=name, conf=conf, box=self._map_to_int_xywh(mapped))
                raw_dets.append(det)
                if conf >= threshold:
                    kept_dets.append(det)

        else:
            boxes = np.asarray(np_outputs[0][0], dtype=np.float32)
            scores = np.asarray(np_outputs[1][0], dtype=np.float32)
            classes = np.asarray(np_outputs[2][0], dtype=np.float32)
            debug["raw_candidates"] = int(len(scores))

            boxes = self._apply_bbox_normalization_and_order(boxes, input_w=input_w, input_h=input_h)

            for box, score, category in zip(boxes, scores, classes):
                conf = float(score)
                cat = int(category)
                name = labels[cat] if 0 <= cat < len(labels) else f"Class {cat}"

                mapped = self.imx500.convert_inference_coords(tuple(box), metadata, self.picam2)
                det = Det(label=name, conf=conf, box=self._map_to_int_xywh(mapped))
                raw_dets.append(det)
                if conf >= threshold:
                    kept_dets.append(det)

        raw_sorted = sorted(raw_dets, key=lambda d: d.conf, reverse=True)
        kept_sorted = sorted(kept_dets, key=lambda d: d.conf, reverse=True)

        raw_topk = raw_sorted[:RAW_TOPK]
        top3 = [(d.label, d.conf) for d in kept_sorted[:3]]

        debug["kept"] = int(len(kept_sorted))

        return kept_sorted, raw_topk, top3, debug

    def capture_snapshot(self) -> FrameSnapshot:
        request = self.picam2.capture_request()
        try:
            metadata = request.get_metadata()
            frame = request.make_array("main")
            frame = frame[..., ::-1].copy()

            src_h, src_w = frame.shape[:2]

            dets, raw_topk, top3, debug = self.parse_detections(metadata)
            debug["src_size"] = (src_w, src_h)

            return FrameSnapshot(
                frame_rgb=frame,
                src_size=(src_w, src_h),
                dets=dets,
                raw_dets=raw_topk,
                top3=top3,
                top_dets=dets[:3],
                debug=debug,
            )
        finally:
            request.release()

    def stop(self) -> None:
        self.picam2.stop()
