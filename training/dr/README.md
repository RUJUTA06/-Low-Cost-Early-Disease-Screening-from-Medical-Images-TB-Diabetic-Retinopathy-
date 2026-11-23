# DR fundus baseline

The baseline is an independent ResNet18 five-grade classifier (0=no DR through 4=proliferative DR only when the selected dataset uses that mapping). Confirm the dataset's grading protocol before use. No dataset, checkpoint, calibrated threshold, or clinical validation is included. Train with `python training/train.py --task dr --manifest /path/to/manifest.csv --output backend/models/dr/model.pt`.
