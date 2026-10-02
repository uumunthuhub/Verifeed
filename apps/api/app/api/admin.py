import os
import secrets

from fastapi import Header, HTTPException, status


def require_ingestion_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected_token = os.getenv("ADMIN_INGESTION_TOKEN")
    if not expected_token or not x_admin_token or not secrets.compare_digest(x_admin_token, expected_token):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An administrator token is required for evidence-registry changes.",
        )
