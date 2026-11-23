import logging
import time
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from sqlalchemy import desc, func
from sqlalchemy.orm import Session

from .config import settings
from .database import Base, engine, get_db
from .models import AuditRecord, EvaluationMetadata, ReviewRecord, ScreeningCase, utcnow
from .schemas import DISCLAIMER, CaseSummary, ReviewRequest, ScreenResponse
from .services.image_validation import decode_and_assess
from .services.pipelines import PREPROCESSING_VERSION, RUNNERS, TASKS, model_status
from .services.reports import make_report

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
logger = logging.getLogger("screening")


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(title=settings.app_name, version="0.1.0", description=f"{DISCLAIMER} No models or datasets ship with this research prototype.", lifespan=lifespan)
origins = [x.strip() for x in settings.cors_origins.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=False,
                   allow_methods=["GET", "POST", "DELETE"], allow_headers=["Content-Type"])


@app.get("/api/health")
def health():
    models = model_status()
    return {"status": "ok", "service": "research-prototype", "models_ready": sum(m["ready"] for m in models),
            "model_count": len(models), "disclaimer": DISCLAIMER}


@app.get("/api/models")
def models():
    return {"models": model_status(), "disclaimer": DISCLAIMER}


async def run_screen(task: str, file: UploadFile, db: Session):
    started = time.perf_counter()
    data = await file.read(settings.max_upload_bytes + 1)
    try:
        checked = decode_and_assess(data, file.content_type, task)
    except ValueError as exc:
        raise HTTPException(status_code=413 if "limit" in str(exc).lower() else 422, detail=str(exc)) from exc
    finally:
        await file.close()
    runner = RUNNERS[task]
    if checked.quality_status == "poor":
        output = None
        label = "indeterminate"
        score = confidence = None
        abstain, reason, model_version = True, "image_quality_rejection", "not-run"
    else:
        try:
            output = runner.predict(checked.image)
            label, score, confidence = output.label, output.score, output.confidence
            abstain, reason, model_version = output.abstain, output.reason, output.model_version
        except Exception as exc:
            logger.error("Inference failed task=%s error_type=%s", task, type(exc).__name__)
            output = None
            label, score, confidence = "indeterminate", None, None
            abstain, reason, model_version = True, "inference_error", "inference-error"
    duration = round((time.perf_counter() - started) * 1000)
    case = ScreeningCase(task=task, quality_status=checked.quality_status, quality_reasons=checked.reasons,
                         output_label=label, score=score, confidence=confidence, abstain=abstain,
                         abstention_reason=reason, duration_ms=duration, model_version=model_version,
                         preprocessing_version=PREPROCESSING_VERSION, review_status="pending", image_sha256=None)
    db.add(case)
    db.add(AuditRecord(case_id=case.id, action="inference", detail={"task": task, "quality": checked.quality_status, "abstain": abstain}))
    db.commit()
    db.refresh(case)
    explanation = {"type": "unavailable", "overlay_available": False,
                   "limitations": "Qualitative influence maps are only emitted when a supported model and tested Grad-CAM hook are configured; no lesion localization is claimed."}
    if output and output.overlay_base64:
        explanation = {"type": "grad_cam", "overlay_available": True, "overlay_png_base64": output.overlay_base64,
                       "limitations": "This qualitative influence overlay is not a lesion map, proof of reasoning, or medical evidence."}
    return ScreenResponse(case_id=case.id, task=task, created_at=case.created_at,
                          quality={"status": case.quality_status, "reasons": case.quality_reasons},
                          prediction={"label": case.output_label, "score": case.score, "confidence": case.confidence},
                          uncertainty={"abstain": case.abstain, "reason": case.abstention_reason}, explanation=explanation,
                          provenance={"model_version": case.model_version, "preprocessing_version": case.preprocessing_version},
                          review={"status": case.review_status}, processing_ms=case.duration_ms)


@app.post("/api/screen/tb", response_model=ScreenResponse)
async def screen_tb(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await run_screen("tb_screening", file, db)


@app.post("/api/screen/dr", response_model=ScreenResponse)
async def screen_dr(file: UploadFile = File(...), db: Session = Depends(get_db)):
    return await run_screen("dr_grading", file, db)


@app.get("/api/cases", response_model=list[CaseSummary])
def list_cases(task: str | None = None, review_status: str | None = None,
               offset: int = Query(0, ge=0), limit: int = Query(25, ge=1, le=100), db: Session = Depends(get_db)):
    query = db.query(ScreeningCase)
    if task in TASKS:
        query = query.filter(ScreeningCase.task == task)
    if review_status:
        query = query.filter(ScreeningCase.review_status == review_status)
    rows = query.order_by(desc(ScreeningCase.created_at)).offset(offset).limit(limit).all()
    return [CaseSummary(case_id=c.id, task=c.task, created_at=c.created_at, quality_status=c.quality_status,
                        output_label=c.output_label, confidence=c.confidence, abstain=c.abstain, review_status=c.review_status) for c in rows]


@app.get("/api/cases/{case_id}")
def get_case(case_id: str, db: Session = Depends(get_db)):
    case = db.get(ScreeningCase, case_id)
    if not case:
        raise HTTPException(404, "Case not found.")
    return {"case_id": case.id, "task": case.task, "created_at": case.created_at, "quality": {"status": case.quality_status, "reasons": case.quality_reasons},
            "prediction": {"label": case.output_label, "score": case.score, "confidence": case.confidence},
            "uncertainty": {"abstain": case.abstain, "reason": case.abstention_reason}, "provenance": {"model_version": case.model_version, "preprocessing_version": case.preprocessing_version},
            "processing_ms": case.duration_ms, "review": {"status": case.review_status, "note": case.review.note if case.review else None}, "disclaimer": DISCLAIMER}


@app.delete("/api/cases/{case_id}", status_code=204)
def delete_case(case_id: str, db: Session = Depends(get_db)):
    case = db.get(ScreeningCase, case_id)
    if not case:
        raise HTTPException(404, "Case not found.")
    db.add(AuditRecord(case_id=case_id, action="delete", detail={"task": case.task}))
    db.delete(case)
    db.commit()
    return Response(status_code=204)


@app.post("/api/review/{case_id}")
def review_case(case_id: str, payload: ReviewRequest, db: Session = Depends(get_db)):
    case = db.get(ScreeningCase, case_id)
    if not case:
        raise HTTPException(404, "Case not found.")
    case.review_status = payload.status
    if case.review:
        case.review.status, case.review.note, case.review.created_at = payload.status, payload.note, utcnow()
    else:
        case.review = ReviewRecord(status=payload.status, note=payload.note)
    db.add(AuditRecord(case_id=case_id, action="review", detail={"status": payload.status, "note_present": bool(payload.note)}))
    db.commit()
    return {"case_id": case_id, "review": {"status": case.review_status}, "disclaimer": DISCLAIMER}


@app.get("/api/metrics/summary")
def metrics_summary(db: Session = Depends(get_db)):
    total = db.query(func.count(ScreeningCase.id)).scalar() or 0
    evaluations = db.query(EvaluationMetadata).all()
    return {"live_cases_count": total, "evaluation_records": [{"task": e.task, "model_version": e.model_version, "dataset_id": e.dataset_id, "metrics": e.metrics} for e in evaluations],
            "message": "No offline evaluation records are configured. Live case counts are operational counts, not model performance metrics.", "disclaimer": DISCLAIMER}


@app.post("/api/export/report")
def export_report(payload: dict, db: Session = Depends(get_db)):
    case_id = payload.get("case_id")
    if not isinstance(case_id, str):
        raise HTTPException(422, "case_id is required.")
    case = db.get(ScreeningCase, case_id)
    if not case:
        raise HTTPException(404, "Case not found.")
    db.add(AuditRecord(case_id=case_id, action="export", detail={"format": "pdf"}))
    db.commit()
    return Response(make_report(case), media_type="application/pdf", headers={"Content-Disposition": f'attachment; filename="screening-{case_id}.pdf"'})
