"""Vision service powered by ViT."""

from __future__ import annotations

import base64
import io
import os
from dataclasses import dataclass
from pathlib import Path

import structlog
import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

from ..core.settings import Settings

logger = structlog.get_logger(__name__)


def _resolve_device(preferred: str) -> str:
    if preferred == "cuda" and torch.cuda.is_available():
        return "cuda"
    return "cpu"


@dataclass
class ImagePrediction:
    label: str
    confidence: float
    scores: dict[str, float]


class ViTImageClassifier:
    """Wrapper around a HuggingFace ViT model."""

    def __init__(
        self,
        settings: Settings,
        *,
        processor: AutoImageProcessor | None = None,
        model: AutoModelForImageClassification | None = None,
    ) -> None:
        self.settings = settings
        self.device = _resolve_device(settings.TORCH_DEVICE)
        
        # Use model path exactly as provided - but ensure it's treated as a local directory
        model_path = settings.VIT_MODEL
        
        # Check if path exists as a directory - if so, load directly
        if os.path.isdir(model_path):
            logger.info("loading_vit_model_from_local", path=model_path, device=self.device)
            from transformers import ViTImageProcessor, ViTForImageClassification
            self.processor = processor or ViTImageProcessor.from_pretrained(model_path)
            self.model = model or ViTForImageClassification.from_pretrained(model_path)
        else:
            logger.info("loading_vit_model_from_hub", model=model_path, device=self.device)
            self.processor = processor or AutoImageProcessor.from_pretrained(model_path)
            self.model = model or AutoModelForImageClassification.from_pretrained(model_path)
        
        self.model.to(self.device)
        self.model.eval()

    def predict_from_base64(self, data_url: str) -> ImagePrediction:
        image = self._decode_base64_image(data_url)
        return self.predict_image(image)

    def predict_image(self, image: Image.Image) -> ImagePrediction:
        inputs = self.processor(image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        with torch.no_grad():
            outputs = self.model(**inputs)
            logits = outputs.logits
            probs = torch.nn.functional.softmax(logits, dim=-1)
            confidence, index = probs.max(dim=-1)
            confidence_value = confidence.item()
            idx = index.item()
            label = self.model.config.id2label.get(idx, str(idx))
            probs_cpu = probs.cpu().squeeze().tolist()
        top_scores = {
            self.model.config.id2label.get(i, str(i)): float(score)
            for i, score in enumerate(probs_cpu)
        }
        return ImagePrediction(label=label, confidence=confidence_value, scores=top_scores)

    def _decode_base64_image(self, data_url: str) -> Image.Image:
        if "," in data_url:
            _, encoded = data_url.split(",", 1)
        else:
            encoded = data_url
        image_bytes = base64.b64decode(encoded)
        image = Image.open(io.BytesIO(image_bytes))
        return image.convert("RGB")

    def close(self) -> None:
        self.model.to("cpu")
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
