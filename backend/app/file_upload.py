from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status, Header
from sqlalchemy.orm import Session
from . import models, database, utils
from typing import Optional
import os
import shutil

router = APIRouter()

# Dependency to get DB session

def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(Authorization: Optional[str] = Header(None), db: Session = Depends(get_db)):
    if not Authorization or not Authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Not authenticated")
    token = Authorization.split(" ")[1]
    payload = utils.decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = db.query(models.User).filter(models.User.id == int(payload["sub"])).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

UPLOAD_DIR = "uploaded_files"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
def upload_file(file: UploadFile = File(...), current_user: models.User = Depends(get_current_user)):
    file_location = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_location, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    return {"filename": file.filename, "content_type": file.content_type, "size": os.path.getsize(file_location)}
