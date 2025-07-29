from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Request, status, Security
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from src.entity.models import User
from src.database.db import get_db
from src.services.auth import auth_service, Hash
from src.services.email import send_email
from src.schemas.schemas import UserModel

router = APIRouter(prefix="/auth", tags=["auth"])

hash_handler = Hash()
security = HTTPBearer()

@router.post("/signup", status_code=status.HTTP_201_CREATED)
async def signup(body: UserModel, bt: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Registers a new user account.

    This endpoint creates a new user in the database and sends a verification email.

    :param body: User data for registration (username, email, password).
    :type body: :class:`src.schemas.schemas.UserModel`
    :param bt: Background tasks for sending the email.
    :type bt: :class:`fastapi.BackgroundTasks`
    :param request: The incoming request object, used to get the base URL for email verification.
    :type request: :class:`fastapi.Request`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 409 Conflict if an account with the given email already exists.
    :return: A dictionary indicating the email of the newly registered user.
    :rtype: dict
    """
    exist_user = db.query(User).filter(User.email == body.email).first()
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Account already exists")
    new_user = User(username=body.username, email=body.email, password=hash_handler.get_password_hash(body.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    # send email notification
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return {"new_user": new_user.email}

@router.post("/login")
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Authenticates a user and provides access and refresh tokens.

    This endpoint verifies user credentials and issues JWT tokens for subsequent API access.

    :param body: User credentials (username/email and password). Defaults to `OAuth2PasswordRequestForm`.
    :type body: :class:`fastapi.security.OAuth2PasswordRequestForm`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 401 Unauthorized if email is invalid, email is not verified, or password is incorrect.
    :return: A dictionary containing access token, refresh token, and token type.
    :rtype: dict
    """
    user = db.query(User).filter(User.email == body.username).first()
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email!")
    if not user.email_verified:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Email not verified!")
    if not hash_handler.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid password!")
    # Generate JWT
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get('/refresh_token')
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(security), db: Session = Depends(get_db)):
    """
    Refreshes access token using a refresh token.

    This endpoint exchanges a valid refresh token for new access and refresh tokens.

    :param credentials: Bearer token containing the refresh token. Defaults to `Security(security)`.
    :type credentials: :class:`fastapi.security.HTTPAuthorizationCredentials`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 401 Unauthorized if the refresh token is invalid or does not match.
    :return: A dictionary containing new access token, refresh token, and token type.
    :rtype: dict
    """
    token = credentials.credentials
    email = await auth_service.get_email_form_refresh_token(token)
    user = db.query(User).filter(User.email == email).first()
    if user.refresh_token != token:
        user.refresh_token = None
        db.commit()
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")

    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    user.refresh_token = refresh_token
    db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}

@router.get("/secret")
async def read_item(current_user: User = Depends(auth_service.get_current_user)):
    """
    Accesses a protected resource.

    This endpoint requires authentication and demonstrates access to a secret route.

    :param current_user: The authenticated user obtained from the access token. Defaults to `Depends(auth_service.get_current_user)`.
    :type current_user: :class:`src.entity.models.User`
    :return: A dictionary with a message and the owner's email.
    :rtype: dict
    """
    return {"message": 'secret router', "owner": current_user.email}

@router.get("/confirmed_email/{token}")
def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirms a user's email address using a verification token.

    This endpoint is called when a user clicks the verification link in their email.

    :param token: The email verification token.
    :type token: str
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 400 Bad Request if the token is invalid or verification fails.
    :return: A dictionary with a confirmation message.
    :rtype: dict
    """
    email = auth_service.get_email_from_token(token)
    user = auth_service.get_user_by_email(email, db)

    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Verification error")
    
    if user.email_verified:
        return {"message": "Your email is already confirmed"}

    auth_service.confirmed_email(email, db)
    return {"message": "Email confirmed"}