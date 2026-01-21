from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from typing import Optional
from pydantic import BaseModel
import os

# Secret key and algorithm for JWT
SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-secret-key")
ALGORITHM = "HS256"

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

class TokenData(BaseModel):
	username: Optional[str] = None

def verify_jwt_token(token: str = Depends(oauth2_scheme)) -> TokenData:
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		username = payload.get("sub")
		if username is None:
			raise HTTPException(
				status_code=status.HTTP_401_UNAUTHORIZED,
				detail="Invalid JWT token: missing subject",
				headers={"WWW-Authenticate": "Bearer"},
			)
		return TokenData(username=username)
	except JWTError:
		raise HTTPException(
			status_code=status.HTTP_401_UNAUTHORIZED,
			detail="Invalid JWT token",
			headers={"WWW-Authenticate": "Bearer"},
		)

@router.get("/protected")
async def protected_route(token_data: TokenData = Depends(verify_jwt_token)):
	return {"message": f"Hello, {token_data.username}. You are authenticated!"}
