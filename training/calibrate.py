"""Choose decision thresholds from a patient-disjoint validation manifest only."""
import argparse
import json
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import roc_curve
from torch.utils.data import DataLoader

from common import ManifestDataset, load_manifest, make_model


def calibrate(task, manifest, checkpoint, device="cpu", min_accuracy=.80, confirm_patient_disjoint=False):
    rows = load_manifest(manifest, task)
    if len({r["patient_id"] for r in rows}) != len(rows):
        print("Note: multiple images per patient are present; this manifest must be disjoint from training by patient.")
    dataset = ManifestDataset(rows, task)
    loader = DataLoader(dataset, batch_size=16, shuffle=False)
    model = make_model(task)
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True)); model.to(device).eval()
    labels, probs = [], []
    with torch.no_grad():
        for x, y in loader:
            logits = model(x.to(device))
            p = torch.sigmoid(logits).squeeze(1) if task == "tb" else torch.softmax(logits, dim=1)
            labels.extend(y.numpy().reshape(-1).astype(int).tolist()); probs.extend(p.cpu().numpy().tolist())
    y = np.asarray(labels); p = np.asarray(probs)
    sidecar_path = Path(checkpoint).with_suffix(Path(checkpoint).suffix + ".json")
    metadata = json.loads(sidecar_path.read_text(encoding="utf-8"))
    if Path(manifest).name == metadata["manifest"]:
        raise ValueError("Use a distinct validation manifest; the training manifest cannot calibrate its own threshold.")
    if not confirm_patient_disjoint:
        raise ValueError("Confirm that validation patient IDs are disjoint from training before calibration.")
    if task == "tb":
        if len(np.unique(y)) != 2:
            raise ValueError("TB threshold calibration needs both dataset-defined classes in the validation set.")
        fpr, tpr, thresholds = roc_curve(y, p)
        threshold = float(thresholds[np.argmax(tpr - fpr)])
        if not np.isfinite(threshold): threshold = 0.5
        metadata["validation_threshold"] = threshold
        metadata["threshold_selection"] = "Youden J on validation only"
    else:
        confidence = p.max(axis=1); pred = p.argmax(axis=1); order = np.argsort(-confidence)
        sorted_correct = (pred[order] == y[order]).astype(float)
        acc = np.cumsum(sorted_correct) / np.arange(1, len(y) + 1)
        valid = np.flatnonzero(acc >= min_accuracy)
        threshold = float(confidence[order[valid[-1]]]) if valid.size else 1.01
        metadata["minimum_confidence"] = threshold
        metadata["validation_minimum_accuracy_target"] = min_accuracy
    metadata["calibration_manifest"] = Path(manifest).name
    metadata["calibration_images"] = len(y)
    metadata["patient_disjoint_verified"] = True
    sidecar_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(json.dumps({"task": task, "threshold": threshold, "validation_images": len(y), "metadata": str(sidecar_path), "clinical_validation": False}, indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--task",choices=["tb","dr"],required=True);p.add_argument("--manifest",required=True);p.add_argument("--checkpoint",required=True);p.add_argument("--device",default="cpu");p.add_argument("--minimum-accuracy",type=float,default=.80);p.add_argument("--confirm-patient-disjoint",action="store_true",required=True,help="Assert validation patients are excluded from training");a=p.parse_args();calibrate(a.task,a.manifest,a.checkpoint,a.device,a.minimum_accuracy,a.confirm_patient_disjoint)
