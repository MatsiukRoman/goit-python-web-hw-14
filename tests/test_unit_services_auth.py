import unittest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session
from jose import jwt
from fastapi import HTTPException
from datetime import datetime, timedelta, timezone

from src.entity.models import User
from src.services.auth import Hash, Auth

class TestAuthModule(unittest.IsolatedAsyncioTestCase):

    def setUp(self):
        self.db = MagicMock(spec=Session)
        self.user = User(id=1, email="user@example.com", email_verified=False)
        self.auth = Auth()
        self.hash = Hash()

    def test_get_password_hash_and_verify_password(self):
        password = "password123"
        hashed = self.hash.get_password_hash(password)
        self.assertTrue(self.hash.verify_password(password, hashed))
        self.assertFalse(self.hash.verify_password("wrong", hashed))

    async def test_create_access_token(self):
        token = await self.auth.create_access_token({"sub": self.user.email})
        decoded = jwt.decode(token, self.auth.SECRET_KEY, algorithms=[self.auth.ALGORITHM])
        self.assertEqual(decoded["sub"], self.user.email)
        self.assertEqual(decoded["scope"], "access_token")

    async def test_create_refresh_token(self):
        token = await self.auth.create_refresh_token({"sub": self.user.email})
        decoded = jwt.decode(token, self.auth.SECRET_KEY, algorithms=[self.auth.ALGORITHM])
        self.assertEqual(decoded["sub"], self.user.email)
        self.assertEqual(decoded["scope"], "refresh_token")

    async def test_get_email_form_refresh_token_valid(self):
        token = await self.auth.create_refresh_token({"sub": self.user.email})
        email = await self.auth.get_email_form_refresh_token(token)
        self.assertEqual(email, self.user.email)

    async def test_get_email_form_refresh_token_invalid_scope(self):
        payload = {"sub": self.user.email, "scope": "access_token", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
        token = jwt.encode(payload, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)
        with self.assertRaises(HTTPException):
            await self.auth.get_email_form_refresh_token(token)

    async def test_get_email_form_refresh_token_jwt_error(self):
        with self.assertRaises(HTTPException):
            await self.auth.get_email_form_refresh_token("invalid.token")

    async def test_get_current_user_success(self):
        token = await self.auth.create_access_token({"sub": self.user.email})
        self.db.query().filter().first.return_value = self.user
        user = await self.auth.get_current_user(token=token, db=self.db)
        self.assertEqual(user.email, self.user.email)

    async def test_get_current_user_invalid_scope(self):
        payload = {"sub": self.user.email, "scope": "refresh_token", "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
        token = jwt.encode(payload, self.auth.SECRET_KEY, algorithm=self.auth.ALGORITHM)
        with self.assertRaises(HTTPException):
            await self.auth.get_current_user(token=token, db=self.db)

    async def test_get_current_user_no_user_in_db(self):
        token = await self.auth.create_access_token({"sub": self.user.email})
        self.db.query().filter().first.return_value = None
        with self.assertRaises(HTTPException):
            await self.auth.get_current_user(token=token, db=self.db)

    def test_get_user_by_email_found(self):
        self.db.query().filter_by().first.return_value = self.user
        user = self.auth.get_user_by_email(email=self.user.email, db=self.db)
        self.assertEqual(user, self.user)

    def test_get_user_by_email_not_found(self):
        self.db.query().filter_by().first.return_value = None
        user = self.auth.get_user_by_email(email="notfound@example.com", db=self.db)
        self.assertIsNone(user)

    def test_confirmed_email_success(self):
        self.db.query().filter_by().first.return_value = self.user
        self.auth.confirmed_email(email=self.user.email, db=self.db)
        self.assertTrue(self.user.email_verified)
        self.db.commit.assert_called_once()

    def test_confirmed_email_user_not_found(self):
        self.db.query().filter_by().first.return_value = None
        with self.assertRaises(HTTPException):
            self.auth.confirmed_email(email="notfound@example.com", db=self.db)

    def test_create_email_token_and_decode(self):
        token = self.auth.create_email_token({"sub": self.user.email})
        email = self.auth.get_email_from_token(token)
        self.assertEqual(email, self.user.email)

    def test_get_email_from_token_invalid(self):
        with self.assertRaises(HTTPException):
            self.auth.get_email_from_token("invalid.token")


if __name__ == '__main__':
    unittest.main()
