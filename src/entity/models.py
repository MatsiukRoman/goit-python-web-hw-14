from sqlalchemy import Column, Integer, String, Date, ForeignKey, Boolean
from src.database.db import Base
from sqlalchemy.orm import relationship

class Contact(Base):
    """
    Represents a contact entry in the database.

    This model stores individual contact details, including personal information,
    communication details, and a reference to the owning user.

    :param id: Primary key, unique identifier for the contact.
    :type id: int
    :param first_name: The first name of the contact.
    :type first_name: str
    :param last_name: The last name of the contact.
    :type last_name: str
    :param email: The email address of the contact, must be unique across all contacts.
    :type email: str
    :param phone_number: The phone number of the contact.
    :type phone_number: str, optional
    :param birthday: The birthday of the contact.
    :type birthday: :class:`datetime.date`
    :param additional_info: Any additional information or notes about the contact.
    :type additional_info: str, optional
    :param user_id: Foreign key referencing the ID of the user who owns this contact.
    :type user_id: int
    :param user: The User object associated with this contact.
    :type user: :class:`User`
    """
    __tablename__ = "contacts"
    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    email = Column(String(150), nullable=False, unique=True, index=True)
    phone_number = Column(String(50), nullable=True)
    birthday = Column(Date, nullable=False)
    additional_info = Column(String, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id")) 

    user = relationship("User", back_populates="contacts")

class User(Base):
    """
    Represents a user in the application.

    This model stores user authentication details, profile information,
    and manages their associated contacts.

    :param id: Primary key, unique identifier for the user.
    :type id: int
    :param username: The user's chosen username, must be unique.
    :type username: str
    :param email: The user's unique email address, used for login.
    :type email: str
    :param password: Hashed password for the user.
    :type password: str
    :param refresh_token: Token used to obtain new access tokens without re-authenticating.
    :type refresh_token: str, optional
    :param email_verified: Boolean indicating if the user's email has been confirmed.
    :type email_verified: bool
    :param avatar: URL to the user's profile avatar.
    :type avatar: str, optional
    :param contacts: A list of contacts associated with this user.
    :type contacts: list[:class:`Contact`]
    """
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(150), nullable=False, unique=True)
    email = Column(String(150), nullable=False, unique=True)
    password = Column(String(255), nullable=False)
    refresh_token = Column(String(255), nullable=True)
    email_verified = Column(Boolean, default=False)
    avatar = Column(String, nullable=True)
    contacts = relationship("Contact", back_populates="user")