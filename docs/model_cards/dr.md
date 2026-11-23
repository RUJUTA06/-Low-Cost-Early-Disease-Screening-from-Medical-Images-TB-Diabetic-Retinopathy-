# Diabetic retinopathy model card

- **Status:** Baseline implementation only; no trained model checkpoint is included.
- **Architecture:** Torchvision ResNet18 with a five-class output head, initialized without downloaded pretrained weights.
- **Intended use:** Research/education grading experiments using a dataset with a verified compatible severity mapping.
- **Label mapping:** Classes 0–4 correspond to no DR, mild, moderate, severe and proliferative DR only when the selected dataset defines these levels this way. Validate before training.
- **Evaluation:** Not performed. No class-wise performance, threshold, calibration, subgroup or external-site results are available.
- **Limitations:** Current field-of-view/exposure/blur checks are heuristic technical gates, not an ophthalmic quality assessment. No referable-DR threshold is configured.
- **Safety:** No “healthy” or disease-free guarantee; outputs are preliminary support and require professional interpretation.
