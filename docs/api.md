# API reference

Interactive OpenAPI is available at `/docs` while the local backend is running. All screening responses include a research disclaimer.

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/health` | Service/model readiness |
| GET | `/api/models` | Per-task model readiness and versions |
| POST | `/api/screen/tb` | Multipart `file` chest X-ray workflow |
| POST | `/api/screen/dr` | Multipart `file` fundus workflow |
| POST | `/api/review/{case_id}` | JSON `{status, note?}` reviewer annotation |
| GET | `/api/cases?offset=0&limit=25&task=...` | Paginated pseudonymous history |
| GET | `/api/cases/{case_id}` | Case metadata |
| DELETE | `/api/cases/{case_id}` | Delete local case record |
| GET | `/api/metrics/summary` | Operational totals and stored offline evaluations, not live model metrics |
| POST | `/api/export/report` | JSON `{case_id}` to PDF review report |
