import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models.generation_audit import GenerationAudit


class GenerationAuditRepository:
    """Database operations for persisted provenance and audit trail of generation jobs"""

    def __init__(self, db: Session):
        self.db = db

    def create(
        self,
        *,
        job_id: str,
        requested_count: int,
        result_summary: str,
        result_provenance: dict[str, Any] | None,
    ) -> GenerationAudit:
        provider: str | None = None
        schema_version: int | None = None
        provenance_json: str | None = None

        if isinstance(result_provenance, dict):
            provider_value = result_provenance.get("provider")
            if isinstance(provider_value, str):
                provider = provider_value

            schema_value = result_provenance.get("schema_version")
            if isinstance(schema_value, int) and not isinstance(schema_value, bool):
                schema_version = schema_value

            provenance_json = json.dumps(
                result_provenance,
                ensure_ascii=True,
                sort_keys=True,
            )

        row = GenerationAudit(
            job_id=job_id,
            requested_count=requested_count,
            provider=provider,
            provenance_schema_version=schema_version,
            provenance_json=provenance_json,
            result_summary=result_summary,
        )
        self.db.add(row)
        self.db.commit()
        self.db.refresh(row)
        return row

    def get_by_job_id(self, job_id: str) -> Optional[GenerationAudit]:
        return (
            self.db.query(GenerationAudit)
            .filter(GenerationAudit.job_id == job_id)
            .first()
        )
