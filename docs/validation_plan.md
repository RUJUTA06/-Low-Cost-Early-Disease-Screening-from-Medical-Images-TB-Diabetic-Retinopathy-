# Validation plan

## Software verification

- Backend tests cover health/readiness, TB and DR routes, corrupt/unsupported uploads, abstention without configured weights, review, history, delete and PDF export.
- Frontend tests cover safety content, the two distinct workflows and navigation.
- Operational checks: CPU-only startup without checkpoints, Docker health checks, and image/temp-data retention review.
- Add Playwright end-to-end checks after the app is run in an environment with browser tooling.

## Model evaluation before research claims

1. Verify dataset permission, license, terms, label definitions, source/version and redistribution constraints.
2. Split at patient level, preserve a locked test set, and record site, exclusions and preprocessing.
3. Select thresholds on validation data only. Measure confusion matrix, class-wise precision/recall/F1, sensitivity, specificity, ROC-AUC, PR-AUC and calibration when mathematically supported.
4. Evaluate subgroups only when lawful and represented in metadata; never infer demographics from pixels.
5. Test external-site generalization, shift, image quality/abstention, false-negative behavior and workflow effects.
6. Publish all denominators, confidence intervals, protocol, checkpoint hashes, seeds, versions and limitations. No metrics currently exist in this repository.

## Current state

No datasets, checkpoints or offline evaluation records are included. Therefore no model-performance test is available and the API abstains when no checkpoint is configured. Synthetic software fixtures are not medical images and are not evidence of model performance.
