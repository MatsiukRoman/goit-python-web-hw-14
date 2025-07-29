from datetime import datetime, timedelta, timezone
from typing import Optional
from fastapi import Depends, HTTPException
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from starlette import status

from src.database.db import get_db
from src.entity.models import User
from src.conf.config import get_settings

settings = get_settings()

class Hash:
    """
    Utility class for password hashing and verification.

    This class provides methods to hash plain text passwords using bcrypt
    and verify if a given plain password matches a hashed one.
    """
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verifies a plain text password against a hashed password.

        :param plain_password: The plain text password to verify.
        :type plain_password: str
        :param hashed_password: The hashed password to compare against.
        :type hashed_password: str
        :return: True if the plain password matches the hashed password, False otherwise.
        :rtype: bool
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str) -> str:
        """
        Hashes a plain text password.

        :param password: The plain text password to hash.
        :type password: str
        :return: The bcrypt hashed password.
        :rtype: str
        """
        return self.pwd_context.hash(password)


class Auth:
    """
    Service class for user authentication, JWT token management, and email verification.

    This class encapsulates logic for creating and verifying JWT access and refresh tokens,
    managing user sessions, and handling email confirmation.
    """
    SECRET_KEY = settings.SECRET_KEY
    ALGORITHM = settings.ALGORITHM
    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        Creates a new JWT access token.

        :param data: A dictionary containing data to encode into the token (e.g., {"sub": user_email}).
        :type data: dict
        :param expires_delta: Optional expiration time in seconds. Defaults to 900 seconds (15 minutes).
        :type expires_delta: float, optional
        :return: The encoded JWT access token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta or 900)
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire, "scope": "access_token"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None) -> str:
        """
        Creates a new JWT refresh token.

        :param data: A dictionary containing data to encode into the token (e.g., {"sub": user_email}).
        :type data: dict
        :param expires_delta: Optional expiration time in seconds. Defaults to 604800 seconds (7 days).
        :type expires_delta: float, optional
        :return: The encoded JWT refresh token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(seconds=expires_delta or 604800)
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire, "scope": "refresh_token"})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    async def get_email_form_refresh_token(self, refresh_token: str) -> str:
        """
        Decodes a refresh token and extracts the user's email.

        :param refresh_token: The refresh token string.
        :type refresh_token: str
        :raises HTTPException: 401 Unauthorized if the token is invalid or has an incorrect scope.
        :return: The email address (subject) from the token.
        :rtype: str
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload.get("scope") != "refresh_token":
                raise HTTPException(status_code=401, detail="Invalid scope for token")
            return payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=401, detail="Invalid refresh token")

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
        """
        Dependency function to retrieve the current authenticated user.

        This function decodes the access token, validates it, and fetches the
        corresponding user from the database. It is used as a FastAPI dependency
        for protected routes.

        :param token: The JWT access token provided in the Authorization header. Defaults to `oauth2_scheme`.
        :type token: str
        :param db: The database session. Defaults to `get_db`.
        :type db: :class:`sqlalchemy.orm.Session`
        :raises HTTPException: 401 Unauthorized if credentials are invalid or the user is not found.
        :return: The authenticated User object.
        :rtype: :class:`src.entity.models.User`
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload.get("sub")
            if email is None:
                raise credentials_exception
            # Ensure the token is an access token if you have distinct scopes for access/refresh
            if payload.get("scope") != "access_token":
                raise credentials_exception 
        except JWTError:
            raise credentials_exception

        user = db.query(User).filter(User.email == email).first()
        if user is None:
            raise credentials_exception
        return user

    def get_user_by_email(self, email: str, db: Session) -> Optional[User]:
        """
        Retrieves a user from the database by their email address.

        :param email: The email address of the user to retrieve.
        :type email: str
        :param db: The database session.
        :type db: :class:`sqlalchemy.orm.Session`
        :return: The User object if found, otherwise None.
        :rtype: :class:`src.entity.models.User`, optional
        """
        return db.query(User).filter_by(email=email).first()

    def confirmed_email(self, email: str, db: Session):
        """
        Marks a user's email as verified in the database.

        :param email: The email address of the user to confirm.
        :type email: str
        :param db: The database session.
        :type db: :class:`sqlalchemy.orm.Session`
        :raises HTTPException: 404 Not Found if the user is not found.
        """
        user = self.get_user_by_email(email, db)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.email_verified = True
        db.commit()

    def create_email_token(self, data: dict) -> str:
        """
        Creates a JWT token for email verification.

        :param data: A dictionary containing data to encode (e.g., {"sub": user_email}).
        :type data: dict
        :return: The encoded JWT email verification token.
        :rtype: str
        """
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=7) # Email verification token typically lasts longer
        to_encode.update({"iat": datetime.now(timezone.utc), "exp": expire})
        return jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)

    def get_email_from_token(self, token: str) -> str:
        """
        Decodes an email verification token and extracts the user's email.

        :param token: The email verification token string.
        :type token: str
        :raises HTTPException: 422 Unprocessable Entity if the token is invalid.
        :return: The email address (subject) from the token.
        :rtype: str
        """
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            return payload.get("sub")
        except JWTError:
            raise HTTPException(status_code=422, detail="Invalid token for email verification")


auth_service = Auth()