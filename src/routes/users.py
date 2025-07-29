import tempfile
import os

from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile
from sqlalchemy.orm import Session

from src.entity.models import User
from src.database.db import get_db
from src.services.auth import auth_service
from src.services.cloudinary_service import upload_avatar

router = APIRouter(prefix="/users", tags=["users"])

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # max size 5 mb

@router.get("/{user_id}/avatar")
def get_user_avatar(user_id: int, db: Session = Depends(get_db)):
    """
    Retrieves the avatar URL for a specific user.

    This endpoint fetches the avatar URL associated with a given user ID.

    :param user_id: The unique identifier of the user.
    :type user_id: int
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 404 Not Found if the user or their avatar is not found.
    :return: A dictionary containing the user ID and avatar URL.
    :rtype: dict
    """
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    return {
        "user_id": user.id,
        "avatar_url": user.avatar
    }

@router.post("/avatar") # Changed from /users/avatar to /avatar due to prefix
async def update_avatar(
    file: UploadFile = File(...),
    current_user: User = Depends(auth_service.get_current_user),
    db: Session = Depends(get_db),
):
    """
    Updates the avatar for the currently authenticated user.

    This endpoint allows an authenticated user to upload a new avatar.
    It performs validation on file type and size before uploading to Cloudinary.

    :param file: The avatar image file to upload.
    :type file: :class:`fastapi.UploadFile`
    :param current_user: The authenticated user whose avatar will be updated. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 400 Bad Request if the file type is unsupported or the file size exceeds the limit.
    :return: A dictionary indicating the success of the update and the new avatar URL.
    :rtype: dict
    """
    # check extension file
    ext = os.path.splitext(file.filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type. Allowed: JPG, PNG, GIF")

    file_data = await file.read()

    # check size
    if len(file_data) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File size exceeds 5MB limit.")

    # temp file
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(file_data)
        temp_file_path = tmp.name

    try:
        public_id = f"user_{current_user.id}_avatar"
        avatar_url = upload_avatar(temp_file_path, public_id)

        current_user.avatar = avatar_url
        db.commit()
        db.refresh(current_user) # Refresh the user object to reflect the changes

        return {
            "message": "Avatar updated successfully",
            "avatar_url": avatar_url
        }
    finally:
        os.remove(temp_file_path)