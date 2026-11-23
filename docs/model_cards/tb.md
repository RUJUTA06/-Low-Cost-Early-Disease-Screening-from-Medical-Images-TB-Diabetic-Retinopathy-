# TB chest X-ray model card

- **Status:** Baseline implementation only; no trained model checkpoint is included.
- **Architecture:** Torchvision DenseNet121 with a binary output head, initialized without downloaded pretrained weights.
- **Intended use:** Research/education experiments on task-appropriate chest X-ray datasets.
- **Output:** Dataset-defined binary screening score; the configured threshold maps to a review-priority label, not diagnosis or clinical probability.
- **Input:** RGB-converted JPEG, PNG, WebP or BMP. DICOM is out of MVP scope.
- **Training:** See `training/train.py`; patient-level split required; no dataset ships here.
- **Evaluation:** Not performed. No sensitivity, specificity, AUC, calibration, subgroup or external-site results are available.
- **Limitations:** View compatibility and modality are not clinically validated; quality heuristics are not a substitute for radiographer review; domain shift, bias and false negatives have not been assessed.
- **Safety:** Outputs must be reviewed by a qualified clinician. Never use to rule out TB, delay care, or make autonomous patient decisions.
