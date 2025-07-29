import unittest
from unittest.mock import patch, MagicMock
from src.services.cloudinary_service import upload_avatar

class TestCloudinaryUtils(unittest.TestCase):

    @patch('src.services.cloudinary_service.cloudinary.uploader.upload')
    def test_upload_avatar(self, mock_upload: MagicMock):
        test_file_path = "path/to/some/image.jpg"
        test_public_id = "users/testuser1"
        expected_url = "https://res.cloudinary.com/mock_name/image/upload/v12345/avatars/users/testuser1.jpg"
        mock_upload.return_value = MagicMock(get=MagicMock(return_value=expected_url))
        result_url = upload_avatar(file_path=test_file_path, public_id=test_public_id)
        self.assertEqual(result_url, expected_url)
        mock_upload.assert_called_once()
        mock_upload.assert_called_once_with(
            test_file_path, 
            public_id=test_public_id, 
            folder="avatars", 
            overwrite=True
        )

if __name__ == '__main__':
    unittest.main()