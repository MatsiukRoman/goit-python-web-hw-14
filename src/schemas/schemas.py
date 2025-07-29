from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import date
from typing import Optional

class ContactSchema(BaseModel):
    """
    Schema for creating and updating contact information.

    This schema defines the required fields for submitting contact details
    to the API.

    :param first_name: The first name of the contact.
    :type first_name: str
    :param last_name: The last name of the contact.
    :type last_name: str
    :param email: The email address of the contact. Must be a valid email format.
    :type email: :class:`pydantic.EmailStr`
    :param phone_number: The phone number of the contact.
    :type phone_number: str
    :param birthday: The birthday of the contact in YYYY-MM-DD format.
    :type birthday: :class:`datetime.date`
    :param additional_info: Optional additional information or notes about the contact.
    :type additional_info: str, optional
    """
    first_name: str
    last_name: str
    email: EmailStr
    phone_number: str
    birthday: date
    additional_info: Optional[str] = None

class ContactResponse(ContactSchema):
    """
    Schema for responding with contact information.

    This schema extends `ContactSchema` by including the contact's unique ID
    when returning contact details from the API.

    :param id: The unique identifier of the contact.
    :type id: int
    """
    id: int = 1
    model_config = ConfigDict(from_attributes=True)

class UserModel(BaseModel):
    """
    Schema for user registration and login requests.

    This schema defines the fields required when a user signs up or attempts to log in.

    :param username: The chosen username for the user.
    :type username: str
    :param email: The user's email address.
    :type email: str
    :param password: The user's password.
    :type password: str
    """
    username: str
    email: str
    password: str

class UserResponse(BaseModel):
    """
    Schema for responding with user information.

    This schema defines the user details returned by the API after successful
    operations like registration, login, or retrieving user profile.

    :param id: The unique identifier of the user.
    :type id: int
    :param username: The user's username.
    :type username: str
    :param email: The user's email address.
    :type email: :class:`pydantic.EmailStr`
    :param avatar: URL to the user's profile avatar.
    :type avatar: str, optional
    :param email_verified: Boolean indicating if the user's email has been confirmed.
    :type email_verified: bool
    """
    id: int
    username: str
    email: EmailStr
    avatar: Optional[str] = None
    email_verified: bool

    model_config = ConfigDict(from_attributes=True)