# Architecture and data flow

```mermaid
flowchart LR
  User[Research operator] --> UI[React + TypeScript dashboard]
  UI --> API[FastAPI typed REST API]
  API --> Gate[Decode, byte/pixel and quality gates]
  Gate --> TB[TB DenseNet pipeline]
  Gate --> DR[DR ResNet pipeline]
  TB --> DB[(SQLite pseudonymous records)]
  DR --> DB
  API --> Report[PDF report generator]
  API --> Audit[Safe metadata audit]
  TB -. only explicit configured weights .-> TBW[TB checkpoint]
  DR -. only explicit configured weights .-> DRW[DR checkpoint]
```

User-selected modality determines the pipeline. Images are decoded in memory and discarded after the request. Only pseudonymous case metadata is persisted. No image bytes or patient identifiers are logged. The two model heads, preprocessing entry points, label schemas, dataset documentation and evaluation results are separate.
