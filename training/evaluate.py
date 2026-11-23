import argparse
import json

import numpy as np
import torch
from sklearn.metrics import (accuracy_score, average_precision_score, brier_score_loss,
                             classification_report, confusion_matrix, roc_auc_score)
from torch.utils.data import DataLoader

from common import ManifestDataset, load_manifest, make_model


def evaluate(task, manifest, checkpoint, device="cpu"):
    rows = load_manifest(manifest, task)
    dataset = ManifestDataset(rows, task)
    loader = DataLoader(dataset, batch_size=16, shuffle=False, num_workers=0)
    model = make_model(task)
    model.load_state_dict(torch.load(checkpoint, map_location=device, weights_only=True)); model.to(device).eval()
    labels, scores = [], []
    with torch.no_grad():
        for x, y in loader:
            logits = model(x.to(device))
            probs = torch.sigmoid(logits).squeeze(1) if task == "tb" else torch.softmax(logits, dim=1)
            labels.extend(y.numpy().reshape(-1).tolist()); scores.extend(probs.cpu().numpy().tolist())
    y = np.asarray(labels, dtype=int); p = np.asarray(scores)
    if task == "tb":
        pred = (p >= .5).astype(int); tn, fp, fn, tp = confusion_matrix(y, pred, labels=[0, 1]).ravel()
        metrics = {"accuracy": float(accuracy_score(y, pred)), "sensitivity": float(tp / max(tp + fn, 1)), "specificity": float(tn / max(tn + fp, 1)), "roc_auc": float(roc_auc_score(y, p)) if len(np.unique(y)) == 2 else None, "pr_auc": float(average_precision_score(y, p)) if len(np.unique(y)) == 2 else None, "brier": float(brier_score_loss(y, p)), "confusion_matrix": [[int(tn), int(fp)], [int(fn), int(tp)]], "classification_report": classification_report(y, pred, labels=[0, 1], output_dict=True, zero_division=0)}
    else:
        pred = p.argmax(axis=1); metrics = {"accuracy": float(accuracy_score(y, pred)), "roc_auc_ovr_macro": float(roc_auc_score(y, p, multi_class="ovr", average="macro", labels=[0, 1, 2, 3, 4])) if len(np.unique(y)) == 5 else None, "confusion_matrix": confusion_matrix(y, pred, labels=[0, 1, 2, 3, 4]).tolist(), "classification_report": classification_report(y, pred, labels=[0, 1, 2, 3, 4], output_dict=True, zero_division=0)}
    result = {"task": task, "checkpoint": checkpoint, "manifest": manifest, "n_images": len(y), "patient_split": "Caller must provide a locked patient-independent evaluation manifest.", "metrics": metrics, "clinical_validation": False}
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    p=argparse.ArgumentParser();p.add_argument("--task",choices=["tb","dr"],required=True);p.add_argument("--manifest",required=True);p.add_argument("--checkpoint",required=True);p.add_argument("--device",default="cpu");a=p.parse_args();evaluate(a.task,a.manifest,a.checkpoint,a.device)
