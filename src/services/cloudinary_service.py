import cloudinary
import cloudinary.uploader
from src.conf.config import get_settings

settings = get_settings()

cloudinary.config(
    cloud_name=settings.CLOUDINARY_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET,
    secure=True
)

def upload_avatar(file_path: str, public_id: str) -> str:
    """
    Uploads an avatar image to Cloudinary.

    This function configures Cloudinary with credentials from settings and
    then uploads the specified image file, setting it as an avatar.
    It overwrites existing images with the same public_id in the 'avatars' folder.

    :param file_path: The local path to the image file to be uploaded.
    :type file_path: str
    :param public_id: The unique identifier for the image in Cloudinary.
                      Typically, this should be related to the user ID.
    :type public_id: str
    :return: The secure URL of the uploaded avatar image.
    :rtype: str
    """
    result = cloudinary.uploader.upload(file_path, public_id=public_id, folder="avatars", overwrite=True)
    return result.get("secure_url")