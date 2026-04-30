from fastapi import FastAPI

from app.controller.document_ingest_controller import admin_router, cases_router, router as documents_router

app = FastAPI(title="liber-trade backend", version="0.1.0")
app.include_router(documents_router)
app.include_router(cases_router)
app.include_router(admin_router)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
