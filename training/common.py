from __future__ import annotations

import csv
import random
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.model_selection import GroupShuffleSplit
from torch.utils.data import Dataset
from torchvision import transforms


class ManifestDataset(Dataset):
    """CSV columns: image_path, patient_id, label. No dataset is bundled."""
    def __init__(self, rows, task, train=False):
        self.rows, self.task, self.train = rows, task, train
        base = [transforms.Resize((224, 224)), transforms.ToTensor(),
                transforms.Normalize([.485, .456, .406], [.229, .224, .225])]
        self.transform = transforms.Compose(([transforms.RandomHorizontalFlip(), transforms.RandomRotation(7)] if train else []) + base)

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(row["image_path"]) as im:
            image = self.transform(im.convert("RGB"))
        label = int(row["label"])
        return image, torch.tensor(label, dtype=torch.float32 if self.task == "tb" else torch.long)


def load_manifest(path, task):
    path = Path(path).resolve()
    with path.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    required = {"image_path", "patient_id", "label"}
    if not rows or not required.issubset(rows[0]):
        raise ValueError("Manifest must include image_path, patient_id and label; no dataset is bundled.")
    classes = {int(r["label"]) for r in rows}
    expected = {0, 1} if task == "tb" else {0, 1, 2, 3, 4}
    if not classes.issubset(expected):
        raise ValueError(f"Labels outside documented {task} schema: {sorted(classes - expected)}")
    for row in rows:
        image_path = Path(row["image_path"])
        row["image_path"] = str((path.parent / image_path).resolve() if not image_path.is_absolute() else image_path)
        if not Path(row["image_path"]).is_file():
            raise FileNotFoundError(f"Manifest image missing: {row['image_path']}")
    return rows


def patient_split(rows, seed=42, test_size=.2):
    splitter = GroupShuffleSplit(n_splits=1, test_size=test_size, random_state=seed)
    train_idx, val_idx = next(splitter.split(rows, groups=[r["patient_id"] for r in rows]))
    train, val = [rows[i] for i in train_idx], [rows[i] for i in val_idx]
    if {r["patient_id"] for r in train} & {r["patient_id"] for r in val}:
        raise RuntimeError("Patient leakage detected in split.")
    return train, val


def seed_everything(seed):
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.use_deterministic_algorithms(True, warn_only=True)


def make_model(task, backbone_checkpoint=None):
    from torchvision import models
    if task == "tb":
        model = models.densenet121(weights=None)
        model.classifier = torch.nn.Linear(model.classifier.in_features, 1)
    else:
        model = models.resnet18(weights=None)
        model.fc = torch.nn.Linear(model.fc.in_features, 5)
    if backbone_checkpoint:
        state = torch.load(backbone_checkpoint, map_location="cpu", weights_only=True)
        compatible = {key: value for key, value in state.items() if key in model.state_dict() and model.state_dict()[key].shape == value.shape}
        if not compatible:
            raise ValueError("No compatible backbone weights found in the supplied local checkpoint.")
        model.load_state_dict(compatible, strict=False)
    return model
