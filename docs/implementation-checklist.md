# Blueprint traceability and implementation status

This table follows the attached blueprint requirements. “Implemented” means the repository contains the code path; it does not mean clinical performance is proven. Dataset and model evidence is explicitly unavailable until data and weights are added.

| Blueprint requirement | Implementation location | Status / limitation |
|---|---|---|
| Explicit TB and DR task workflows, no auto-routing | `frontend/src/App.tsx`, `backend/app/services/pipelines.py` | Implemented as separate UI choices, model heads, tasks and label schemas |
| Dashboard, status, recent cases, safety notice | `frontend/src/App.tsx` | Implemented; statistics reflect local records only |
| Upload, preview, supported raster types, size limit | `frontend/src/App.tsx`, `backend/app/services/image_validation.py` | Implemented; no DICOM |
| Decode, pixel cap, quality and error handling | `backend/app/services/image_validation.py` | Basic technical heuristics only; not clinically validated modality/quality assessment |
| TB transfer-learning-capable DenseNet baseline | `training/tb`, `training/train.py`, `backend/app/services/pipelines.py` | Implemented; optional local backbone initialization; no trained checkpoint included |
| DR grading ResNet baseline and severity labels | `training/dr`, `training/train.py`, `backend/app/services/pipelines.py` | Implemented; verify label mapping for chosen dataset before use |
| Model missing/uncertain/poor-quality abstention | `backend/app/main.py`, `backend/app/services/pipelines.py` | Implemented |
| Grad-CAM with original/overlay comparison when supported | `backend/app/services/pipelines.py`, `frontend/src/App.tsx` | Implemented for configured supported architectures; no overlay until a compatible checkpoint is configured |
| SQLite records: cases, reviews, versions, eval and audit | `backend/app/models.py`, `backend/app/database.py` | Schema initialization via SQLAlchemy; no migration framework yet |
| Case search/filter/date/review/delete | `backend/app/main.py`, `frontend/src/App.tsx` | Implemented; API list is paginated |
| Human review notes and override/indeterminate state | `backend/app/main.py`, `frontend/src/App.tsx` | Implemented; notes are free text and must not include identifiers |
| PDF report with provenance and safety | `backend/app/services/reports.py`, `/api/export/report` | Implemented; overlay not retained or embedded in report |
| Actual-only evaluation metrics/model cards | `backend/app/models.py`, `/api/metrics/summary`, `frontend/src/App.tsx`, `docs/model_cards/` | No evaluation records; UI shows unavailable state, never sample scores |
| Config/env/CORS/upload/privacy defaults | `backend/app/config.py`, `.env.example`, `backend/app/main.py` | Local-only defaults; no user authentication/RBAC or rate limiter |
| Safe temporary handling and no raw-image storage | `backend/app/main.py`, `backend/app/services/image_validation.py` | In-memory upload path, no image file writes; image retention disabled |
| API, image, review/report tests | `backend/tests/test_api.py` | Implemented; run results are listed in completion note |
| UI tests and production build | `frontend/src/App.test.tsx`, `frontend/package.json` | Implemented; run results are listed in completion note |
| Docker frontend/API and health checks | `docker-compose.yml`, `backend/Dockerfile`, `frontend/Dockerfile` | Configured for loopback local launch; runtime verification still required |
| Dataset access/licensing and patient split | `training/common.py`, `docs/dataset_cards/README.md` | Dataset-free scaffolding; no data downloaded or integrated |
| Threat model, validation plan and safety boundary | `docs/threat_model.md`, `docs/validation_plan.md`, `README.md` | Implemented; public deployment is intentionally not enabled |
| CI | `.github/workflows/ci.yml` | Implemented; hosted workflow not run from this local checkout |
