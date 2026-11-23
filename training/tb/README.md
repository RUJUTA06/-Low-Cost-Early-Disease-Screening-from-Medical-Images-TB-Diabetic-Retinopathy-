# TB X-ray baseline

The baseline is an independent DenseNet121 binary classifier. The manifest must define labels that match the chosen dataset; no dataset, threshold calibration, or checkpoint is included. Label meaning is dataset-specific. Do not call the output a clinical probability. Train with `python training/train.py --task tb --manifest /path/to/manifest.csv --output backend/models/tb/model.pt`; evaluate against a patient-independent locked manifest before registering any metrics.
