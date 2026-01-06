from typing import Annotated
import os
import aiofiles
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.core.config import settings

router = APIRouter(prefix="/uploads", tags=["Uploads"])

@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: Annotated[UploadFile, File()],
    current_user: Annotated[User, Depends(get_current_user)]
):
    """Upload a generic file."""
    # Ensure upload directory exists
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    
    # Generate unique filename
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.pdf', '.doc', '.docx', '.txt']:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="File type not supported"
        )
        
    filename = f"{datetime.now().strftime('%Y%m%d')}_{uuid.uuid4().hex[:8]}{ext}"
    file_path = os.path.join(settings.UPLOAD_DIR, filename)
    
    # Save file
    async with aiofiles.open(file_path, 'wb') as f:
        content = await file.read()
        await f.write(content)
        
    # Return static URL
    # Assuming app mounts /static to settings.UPLOAD_DIR
    url = f"/static/{filename}"
    
    return {"url": url, "filename": filename, "original_name": file.filename}
