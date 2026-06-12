import hmac
import hashlib
import base64
import json
import time
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "ecosalud_super_secret_jwt_key_2026"
ACCESS_TOKEN_EXPIRE_SECONDS = 300  # 5 minutes
REFRESH_TOKEN_EXPIRE_SECONDS = 900 # 15 minutes

security = HTTPBearer()

def base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').replace('=', '')

def base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)

def create_jwt(payload: dict, expires_in_seconds: int) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload_copy = payload.copy()
    payload_copy["exp"] = int(time.time()) + expires_in_seconds
    
    header_b64 = base64url_encode(json.dumps(header).encode('utf-8'))
    payload_b64 = base64url_encode(json.dumps(payload_copy).encode('utf-8'))
    
    message = f"{header_b64}.{payload_b64}"
    signature = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
    signature_b64 = base64url_encode(signature)
    
    return f"{message}.{signature_b64}"

def verify_jwt(token: str) -> dict:
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        header_b64, payload_b64, signature_b64 = parts
        
        # Verify signature
        message = f"{header_b64}.{payload_b64}"
        expected_signature = hmac.new(SECRET_KEY.encode('utf-8'), message.encode('utf-8'), hashlib.sha256).digest()
        expected_signature_b64 = base64url_encode(expected_signature)
        
        if not hmac.compare_digest(signature_b64, expected_signature_b64):
            return None
            
        payload = json.loads(base64url_decode(payload_b64).decode('utf-8'))
        if payload.get("exp", 0) < time.time():
            return None # Expired
            
        return payload
    except Exception:
        return None

def create_access_token(paciente_id: int) -> str:
    return create_jwt({"sub": str(paciente_id), "type": "access"}, ACCESS_TOKEN_EXPIRE_SECONDS)

def create_refresh_token(paciente_id: int) -> str:
    return create_jwt({"sub": str(paciente_id), "type": "refresh"}, REFRESH_TOKEN_EXPIRE_SECONDS)

def get_current_paciente_id(credentials: HTTPAuthorizationCredentials = Depends(security)) -> int:
    token = credentials.credentials
    payload = verify_jwt(token)
    if not payload or payload.get("type") != "access":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesión expirada o Token de acceso no válido",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return int(payload.get("sub"))
