import jwt
from datetime import datetime, timedelta
from fastapi import HTTPException, Security, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

# Ovo bi u produkciji trebalo da bude u .env fajlu!
SECRET_KEY = "moj_super_tajni_kljuc_za_oblak"
ALGORITHM = "HS256"

security = HTTPBearer()

def create_access_token(username: str):
    """Generiše JWT token koji ističe za 1 sat."""
    expiration = datetime.utcnow() + timedelta(hours=1)
    payload = {"sub": username, "exp": expiration}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verifikuje token iz zaglavlja zahteva."""
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload["sub"]
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token je istekao")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Nevažeći token")