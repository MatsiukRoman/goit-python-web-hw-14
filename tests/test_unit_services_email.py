import unittest
from unittest.mock import patch, MagicMock, AsyncMock
from pydantic.v1 import EmailStr
from src.services.email import send_email

class TestEmailService(unittest.IsolatedAsyncioTestCase):

    @patch('src.services.email.auth_service.create_email_token')
    @patch('src.services.email.FastMail.send_message', new_callable=AsyncMock)
    async def test_send_email_success(self, mock_send_message: AsyncMock, mock_create_token: MagicMock):
        test_email = EmailStr("test@example.com")
        test_username = "TestUser"
        test_host = "http://localhost:8000"
        
        fake_token = "some_verification_token"
        mock_create_token.return_value = fake_token

        await send_email(test_email, test_username, test_host)

        mock_create_token.assert_called_once_with({"sub": test_email})
        mock_send_message.assert_called_once()

        args, kwargs = mock_send_message.call_args
        sent_message_schema = args[0]

        self.assertEqual(sent_message_schema.subject, "Confirm your email ")
        self.assertEqual(sent_message_schema.recipients, [test_email])
        self.assertIn("template_name", kwargs)
        self.assertEqual(kwargs['template_name'], "verify_email.html")

        template_body = sent_message_schema.template_body
        self.assertEqual(template_body["host"], test_host)
        self.assertEqual(template_body["username"], test_username)
        self.assertEqual(template_body["token"], fake_token)

if __name__ == '__main__':
    unittest.main()
