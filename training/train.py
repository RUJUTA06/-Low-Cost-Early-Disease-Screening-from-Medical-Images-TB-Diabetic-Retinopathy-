import argparse
import json
from pathlib import Path

import torch
from torch.utils.data import DataLoader

from common import ManifestDataset, load_manifest, make_model, patient_split, seed_everything


def train(task, manifest, output, dataset_id, dataset_card, epochs=5, batch_size=16, seed=42, device="cpu", init_checkpoint=None):
    seed_everything(seed)
    rows = load_manifest(manifest, task)
    card = Path(dataset_card)
    if not card.is_file():
        raise FileNotFoundError("A dataset card is required before training.")
    card_text = card.read_text(encoding="utf-8").lower()
    if any(key not in card_text for key in ("source", "license", "label")):
        raise ValueError("Dataset card must document its source, license/access conditions, and label schema.")
    train_rows, val_rows = patient_split(rows, seed)
    train_ds, val_ds = ManifestDataset(train_rows, task, True), ManifestDataset(val_rows, task)
    train_dl = DataLoader(train_ds, batch_size=batch_size, shuffle=True, num_workers=0)
    val_dl = DataLoader(val_ds, batch_size=batch_size, shuffle=False, num_workers=0)
    model = make_model(task, init_checkpoint).to(device)
    labels = [int(row["label"]) for row in train_rows]
    counts = torch.bincount(torch.tensor(labels), minlength=2 if task == "tb" else 5).float()
    if (counts == 0).any():
        raise ValueError("Every task label class must be represented in the patient-level training split.")
    loss_fn = (torch.nn.BCEWithLogitsLoss(pos_weight=(counts[0] / counts[1]).to(device)) if task == "tb"
               else torch.nn.CrossEntropyLoss(weight=(counts.sum() / (len(counts) * counts)).to(device)))
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    for epoch in range(epochs):
        model.train(); running = 0.0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            optimizer.zero_grad(set_to_none=True)
            logits = model(x).squeeze(1) if task == "tb" else model(x)
            loss = loss_fn(logits, y)
            loss.backward(); optimizer.step(); running += float(loss.detach()) * len(x)
        model.eval(); validation_loss = 0.0
        with torch.no_grad():
            for x, y in val_dl:
                x, y = x.to(device), y.to(device)
                logits = model(x).squeeze(1) if task == "tb" else model(x)
                validation_loss += float(loss_fn(logits, y)) * len(x)
        print(json.dumps({"epoch": epoch + 1, "train_loss": running / len(train_ds), "validation_loss": validation_loss / len(val_ds)}))
    # Keep model/data provenance beside the state dict; evaluate thresholds on validation only.
    output = Path(output); output.parent.mkdir(parents=True, exist_ok=True)
    torch.save(model.cpu().state_dict(), output)
    sidecar = {"task": task, "architecture": "DenseNet121" if task == "tb" else "ResNet18", "dataset_id": dataset_id,
               "label_schema": {"tb": {"0":"dataset-negative","1":"dataset-positive"}, "dr": {str(i): name for i, name in enumerate(["no DR", "mild", "moderate", "severe", "proliferative DR"])} }[task],
               "dataset_card": str(card.resolve()), "manifest": Path(manifest).name, "rows": len(rows), "train_rows": len(train_rows), "validation_rows": len(val_rows),
               "patient_split": True, "seed": seed, "epochs": epochs, "device": device, "initialization_checkpoint": init_checkpoint,
               "preprocessing_version": "rgb-resize-224-v1",
               "validation_threshold_selection_required": True, "clinical_validation": False}
    output.with_suffix(output.suffix + ".json").write_text(json.dumps(sidecar, indent=2), encoding="utf-8")
    print(f"Checkpoint saved to {output}. This is not clinically validated; run evaluate.py and document limitations.")


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--task", choices=["tb", "dr"], required=True); p.add_argument("--manifest", required=True); p.add_argument("--dataset-id", required=True);p.add_argument("--dataset-card", required=True);p.add_argument("--output", required=True); p.add_argument("--epochs", type=int, default=5); p.add_argument("--batch-size", type=int, default=16); p.add_argument("--seed", type=int, default=42); p.add_argument("--device", default="cpu");p.add_argument("--init-checkpoint", help="Optional explicitly supplied compatible local backbone weights; no automatic downloads")
    a = p.parse_args(); train(a.task, a.manifest, a.output, a.dataset_id, a.dataset_card, a.epochs, a.batch_size, a.seed, a.device,a.init_checkpoint)
