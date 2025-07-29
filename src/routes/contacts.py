from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, Query, Path, status, Request
from sqlalchemy.orm import Session
from typing import List, Optional

from slowapi import Limiter
from slowapi.util import get_remote_address

from sqlalchemy import text, extract, or_, and_
from src.entity.models import User, Contact
from src.database.db import get_db
from src.services.auth import auth_service
from src.schemas.schemas import ContactSchema, ContactResponse, UserModel

router = APIRouter(prefix="/contacts", tags=["contacts"])
limiter = Limiter(key_func=get_remote_address)

@router.get("/", response_model=list[ContactResponse]) # Змінив /contacts на /
def get_contacts(
    current_user: User = Depends(auth_service.get_current_user), 
    first_name: Optional[str] = Query(None, title="First Name"),
    last_name: Optional[str] = Query(None, title="Last Name"),
    email: Optional[str] = Query(None, title="Email"),
    db: Session = Depends(get_db),
):
    """
    Retrieves a list of contacts for the current user, with optional filtering.

    This endpoint allows authenticated users to fetch their contacts,
    optionally filtered by first name, last name, or email.

    :param current_user: The authenticated user. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param first_name: Optional filter for contact's first name (case-insensitive search).
    :type first_name: str, optional
    :param last_name: Optional filter for contact's last name (case-insensitive search).
    :type last_name: str, optional
    :param email: Optional filter for contact's email (case-insensitive search).
    :type email: str, optional
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :return: A list of contacts matching the criteria.
    :rtype: list[:class:`src.schemas.schemas.ContactResponse`]
    """
    query = db.query(Contact).filter(Contact.user_id == current_user.id)

    if first_name:
        query = query.filter(Contact.first_name.ilike(f"%{first_name}%"))
    if last_name:
        query = query.filter(Contact.last_name.ilike(f"%{last_name}%"))
    if email:
        query = query.filter(Contact.email.ilike(f"%{email}%"))

    contacts = query.all()
    return contacts

@router.get("/{contact_id}", response_model=ContactResponse) # Змінив /contacts/{contact_id} на /{contact_id}
async def get_contact_by_id(
    contact_id: int = Path(ge=1), current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)
):
    """
    Retrieves a single contact by its ID for the current user.

    :param contact_id: The unique identifier of the contact. Must be a positive integer.
    :type contact_id: int
    :param current_user: The authenticated user. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 404 Not Found if the contact does not exist or does not belong to the current user.
    :return: The found contact.
    :rtype: :class:`src.schemas.schemas.ContactResponse`
    """
    contact = db.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")
    return contact

@router.post("/", response_model=ContactResponse, status_code=status.HTTP_201_CREATED) # Змінив /contacts на /, додав status_code
@limiter.limit("3/minute")
async def create_contact(request: Request, body: ContactSchema, current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """
    Creates a new contact for the current user.

    This endpoint adds a new contact to the database. It is rate-limited to 3 requests per minute.

    :param request: The incoming request object for rate limiting.
    :type request: :class:`fastapi.Request`
    :param body: The contact data to be created.
    :type body: :class:`src.schemas.schemas.ContactSchema`
    :param current_user: The authenticated user. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 409 Conflict if a contact with the same email already exists for the user.
    :return: The newly created contact.
    :rtype: :class:`src.schemas.schemas.ContactResponse`
    """
    contact = db.query(Contact).filter_by(email=body.email, user_id=current_user.id).first() # Додав user_id до фільтрації
    if contact:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Contact with this email already exists for this user!"
        )

    contact = Contact(**body.model_dump(),user_id=current_user.id) 
    db.add(contact)
    db.commit()
    db.refresh(contact) # Додаємо refresh для отримання повних даних, включаючи id
    return contact

@router.put("/{contact_id}", response_model=ContactResponse) # Змінив /contacts/{contact_id} на /{contact_id}
async def update_contact(
    body: ContactSchema, contact_id: int = Path(ge=1), current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)
):
    """
    Updates an existing contact for the current user.

    :param body: The updated contact data.
    :type body: :class:`src.schemas.schemas.ContactSchema`
    :param contact_id: The unique identifier of the contact to update. Must be a positive integer.
    :type contact_id: int
    :param current_user: The authenticated user. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 404 Not Found if the contact does not exist or does not belong to the current user.
    :return: The updated contact.
    :rtype: :class:`src.schemas.schemas.ContactResponse`
    """
    contact = db.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Contact not found")

    contact.first_name = body.first_name
    contact.last_name = body.last_name
    contact.email = body.email
    contact.phone_number = body.phone_number
    contact.birthday = body.birthday
    contact.additional_info = body.additional_info

    db.commit()
    db.refresh(contact) # Додаємо refresh для отримання оновлених даних
    return contact


@router.delete("/{contact_id}", response_model=ContactResponse) # Змінив /contacts/{contact_id} на /{contact_id}
async def delete_contact(contact_id: int = Path(ge=1), current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """
    Deletes a contact for the current user.

    :param contact_id: The unique identifier of the contact to delete. Must be a positive integer.
    :type contact_id: int
    :param current_user: The authenticated user. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :raises HTTPException: 404 Not Found if the contact does not exist or does not belong to the current user.
    :return: The deleted contact.
    :rtype: :class:`src.schemas.schemas.ContactResponse`
    """
    contact = db.query(Contact).filter_by(id=contact_id, user_id=current_user.id).first()
    
    if contact is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="NOT FOUND")

    db.delete(contact)
    db.commit()
    return contact

@router.get("/upcoming-birthdays/", response_model=List[ContactResponse]) # Змінив /contacts/upcoming-birthdays/ на /upcoming-birthdays/
async def get_upcoming_birthdays(current_user: User = Depends(auth_service.get_current_user), db: Session = Depends(get_db)):
    """
    Retrieves contacts with upcoming birthdays within the next 7 days for the current user.

    This endpoint identifies contacts whose birthdays fall within the next week,
    considering year-end transitions (December to January).

    :param current_user: The authenticated user. Defaults to `auth_service.get_current_user`.
    :type current_user: :class:`src.entity.models.User`
    :param db: The database session. Defaults to `get_db`.
    :type db: :class:`sqlalchemy.orm.Session`
    :return: A list of contacts with upcoming birthdays.
    :rtype: list[:class:`src.schemas.schemas.ContactResponse`]
    """
    today = datetime.now().date()
    end_date = today + timedelta(days=7)

    # Base query for the current user's contacts
    query = db.query(Contact).filter(Contact.user_id == current_user.id)

    # Logic to handle year-end (December to January) birthday ranges
    if today.month == 12 and end_date.month == 1:
        # Birthdays from today to end of December, PLUS birthdays from start of January to end_date
        contacts = query.filter(
            or_(
                and_(
                    extract("month", Contact.birthday) == today.month,
                    extract("day", Contact.birthday) >= today.day,
                ),
                and_(
                    extract("month", Contact.birthday) == end_date.month,
                    extract("day", Contact.birthday) <= end_date.day,
                ),
            )
        ).all()
    else:
        # Birthdays within the same year's month range
        contacts = query.filter(
            and_(
                or_(
                    extract("month", Contact.birthday) == today.month,
                    extract("month", Contact.birthday) == end_date.month,
                ),
                # If month is current, day must be >= today.day
                # If month is end_date_month, day must be <= end_date.day
                or_(
                    and_(
                        extract("month", Contact.birthday) == today.month,
                        extract("day", Contact.birthday) >= today.day,
                    ),
                    and_(
                        extract("month", Contact.birthday) == end_date.month,
                        extract("day", Contact.birthday) <= end_date.day,
                    ),
                    # This handles cases where the range spans across full months
                    # e.g., from day 20 of month X to day 10 of month Y (where X < Y)
                    # and there's a full month Z in between (X < Z < Y)
                    and_(
                        extract("month", Contact.birthday) > today.month,
                        extract("month", Contact.birthday) < end_date.month,
                    ),
                )
            )
        ).all()

    return contacts