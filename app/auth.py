from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from app.config import settings
import secrets

security = HTTPBasic()


def verify_user(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Verifies user credentials using HTTP Basic Auth.
    Uses secrets.compare_digest for secure string comparison.
    """
    correct_username = secrets.compare_digest(credentials.username, settings.BASIC_AUTH_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, settings.BASIC_AUTH_PASSWORD)

    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username
