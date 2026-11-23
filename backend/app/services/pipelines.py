from dataclasses import dataclass
import base64
import json
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image

from ..config import settings

TASKS = {
    "tb_screening": {"name": "TB chest X-ray screening support", "architecture": "DenseNet121 binary baseline", "path": settings.tb_checkpoint},
    "dr_grading": {"name": "Diabetic retinopathy fundus grading", "architecture": "ResNet18 five-class baseline", "path": settings.dr_checkpoint},
}
PREPROCESSING_VERSION = "rgb-resize-224-v1"


@dataclass
class Output:
    label: str
    score: float | None
    confidence: float | None
    abstain: bool
    reason: str | None
    model_version: str
    overlay_base64: str | None


class ModelRunner:
    """Loads only explicit checkpoints; never silently downloads pretrained weights."""
    def __init__(self, task: str):
        self.task = task
        self.spec = TASKS[task]
        self.model = None
        self.error = None
        self.metadata = {}
        path = Path(self.spec["path"]) if self.spec["path"] else None
        if not path or not path.is_file():
            self.error = "No trained checkpoint is configured. Add a documented checkpoint to enable inference."
            return
        try:
            metadata_path = path.with_suffix(path.suffix + ".json")
            if not metadata_path.is_file():
                raise ValueError("Checkpoint provenance sidecar is missing.")
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
            expected_task = "tb" if task == "tb_screening" else "dr"
            required = {"task", "dataset_id", "label_schema", "preprocessing_version", "patient_disjoint_verified", "validation_threshold" if task == "tb_screening" else "minimum_confidence"}
            if not required.issubset(metadata) or metadata["task"] != expected_task:
                raise ValueError("Checkpoint provenance or validation calibration is incomplete.")
            if metadata["patient_disjoint_verified"] is not True:
                raise ValueError("Patient-disjoint validation is not attested in checkpoint provenance.")
            if not metadata.get("dataset_id") or not metadata.get("label_schema"):
                raise ValueError("Checkpoint dataset provenance is incomplete.")
            import torch
            from torchvision import models
            model = models.densenet121(weights=None) if task == "tb_screening" else models.resnet18(weights=None)
            if task == "tb_screening":
                model.classifier = torch.nn.Linear(model.classifier.in_features, 1)
            else:
                model.fc = torch.nn.Linear(model.fc.in_features, 5)
            state = torch.load(path, map_location=settings.model_device, weights_only=True)
            model.load_state_dict(state)
            model.to(settings.model_device).eval()
            self.model = model
            self.metadata = metadata
        except Exception as exc:
            self.error = f"Checkpoint could not be loaded ({type(exc).__name__})."

    @property
    def ready(self):
        return self.model is not None

    def predict(self, image: Image.Image) -> Output:
        if not self.ready:
            return Output("indeterminate", None, None, True, "model_not_configured", "not-configured", None)
        import torch
        from torchvision.transforms import Compose, Normalize, Resize, ToTensor
        tensor = Compose([Resize((224, 224)), ToTensor(), Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])])(image).unsqueeze(0)
        tensor = tensor.to(settings.model_device)
        layer = self.model.features.denseblock4 if self.task == "tb_screening" else self.model.layer4
        activation: list = []
        gradients: list = []
        forward_handle = layer.register_forward_hook(lambda _m, _i, out: activation.append(out))
        backward_handle = layer.register_full_backward_hook(lambda _m, _gi, go: gradients.append(go[0]))
        self.model.zero_grad(set_to_none=True)
        with torch.enable_grad():
            logits = self.model(tensor)
            if self.task == "tb_screening":
                score = float(torch.sigmoid(logits).item())
                confidence = max(score, 1 - score)
                margin = abs(score - float(self.metadata["validation_threshold"]))
                abstain = margin < settings.uncertainty_margin
                label = "indeterminate" if abstain else ("review_priority" if score >= float(self.metadata["validation_threshold"]) else "lower_review_priority")
            else:
                probs = torch.softmax(logits, dim=1).squeeze(0)
                score, idx = float(probs.max().item()), int(probs.argmax().item())
                confidence = score
                abstain = score < float(self.metadata["minimum_confidence"])
                label = "indeterminate" if abstain else f"severity_grade_{idx}"
            target = logits.reshape(-1)[0] if self.task == "tb_screening" else logits[0, int(logits.argmax(dim=1).item())]
            target.backward()
        forward_handle.remove(); backward_handle.remove()
        overlay = None
        if activation and gradients:
            weights = gradients[-1].mean(dim=(2, 3), keepdim=True)
            cam = torch.relu((weights * activation[-1]).sum(dim=1, keepdim=True))
            display = image.copy()
            display.thumbnail((512, 512), Image.Resampling.BILINEAR)
            cam = torch.nn.functional.interpolate(cam, size=(display.height, display.width), mode="bilinear", align_corners=False)[0, 0]
            cam = cam.detach().cpu().numpy()
            cam = (cam - cam.min()) / (cam.max() - cam.min() + 1e-8)
            heat = np.zeros((*cam.shape, 3), dtype=np.uint8)
            heat[..., 0] = np.clip(255 * cam, 0, 255)
            heat[..., 1] = np.clip(220 * np.maximum(0, 1 - abs(cam - .55) * 2), 0, 255)
            base = np.asarray(display.convert("RGB"), dtype=np.float32)
            composite = np.clip(base * .58 + heat * .42, 0, 255).astype(np.uint8)
            buf = BytesIO(); Image.fromarray(composite).save(buf, format="PNG")
            overlay = base64.b64encode(buf.getvalue()).decode("ascii")
        return Output(label, score, confidence, abstain, "uncertain_model_output" if abstain else None,
                      Path(self.spec["path"]).stem, overlay)


RUNNERS = {task: ModelRunner(task) for task in TASKS}


def model_status():
    return [{"task": task, "name": spec["name"], "architecture": spec["architecture"],
             "ready": RUNNERS[task].ready, "model_version": Path(spec["path"]).stem if RUNNERS[task].ready else "not-configured",
             "dataset": RUNNERS[task].metadata.get("dataset_id", "Not configured"), "message": RUNNERS[task].error}
            for task, spec in TASKS.items()]
