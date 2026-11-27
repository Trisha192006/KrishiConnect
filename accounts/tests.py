
from unittest.mock import patch, MagicMock

from django.test import SimpleTestCase, RequestFactory

from accounts.auth_service import (
    normalize_phone,
    send_otp,
    verify_phone_otp,
)

from accounts.auth_session import (
    save_auth_session,
    clear_auth_session,
    get_authenticated_client,
)


class PhoneValidationTests(SimpleTestCase):

    def test_valid_phone_number(self):
        self.assertEqual(
            normalize_phone("9876543210"),
            "+919876543210"
        )

    def test_short_phone_number(self):
        with self.assertRaises(ValueError):
            normalize_phone("98765")

    def test_alphabetic_phone_number(self):
        with self.assertRaises(ValueError):
            normalize_phone("abcdefghij")

    def test_invalid_starting_digit(self):
        with self.assertRaises(ValueError):
            normalize_phone("1234567890")

    def test_phone_with_spaces(self):
        self.assertEqual(
            normalize_phone(" 9876543210 "),
            "+919876543210"
        )


class SupabaseOTPTests(SimpleTestCase):

    @patch("accounts.auth_service.get_supabase_client")
    def test_send_otp(self, mock_client):

        supabase = mock_client.return_value

        send_otp("9876543210")

        supabase.auth.sign_in_with_otp.assert_called_once_with({
            "phone": "+919876543210",
            "options": {
                "should_create_user": True,
                "channel": "sms",
            },
        })

    @patch("accounts.auth_service.get_supabase_client")
    def test_verify_otp(self, mock_client):

        supabase = mock_client.return_value

        verify_phone_otp("9876543210", "123456")

        supabase.auth.verify_otp.assert_called_once_with({
            "phone": "+919876543210",
            "token": "123456",
            "type": "sms",
        })

    @patch("accounts.auth_service.get_supabase_client")
    def test_invalid_otp_length(self, mock_client):

        with self.assertRaises(ValueError):
            verify_phone_otp("9876543210", "123")

        mock_client.assert_not_called()

    @patch("accounts.auth_service.get_supabase_client")
    def test_invalid_otp_characters(self, mock_client):

        with self.assertRaises(ValueError):
            verify_phone_otp("9876543210", "abcdef")

        mock_client.assert_not_called()


class AuthenticationSessionTests(SimpleTestCase):

    def setUp(self):

        self.factory = RequestFactory()

        self.request = self.factory.get("/")

        self.request.session = {}

    def test_save_auth_session(self):

        session = MagicMock()

        session.access_token = "test-access-token"
        session.refresh_token = "test-refresh-token"

        save_auth_session(self.request, session)

        self.assertEqual(
            self.request.session["supabase_access_token"],
            "test-access-token"
        )

        self.assertEqual(
            self.request.session["supabase_refresh_token"],
            "test-refresh-token"
        )

    def test_clear_auth_session(self):

        self.request.session["supabase_access_token"] = (
            "test-access-token"
        )

        self.request.session["supabase_refresh_token"] = (
            "test-refresh-token"
        )

        clear_auth_session(self.request)

        self.assertNotIn(
            "supabase_access_token",
            self.request.session
        )

        self.assertNotIn(
            "supabase_refresh_token",
            self.request.session
        )

    def test_unauthenticated_session(self):

        client, user = get_authenticated_client(
            self.request
        )

        self.assertIsNone(client)
        self.assertIsNone(user)

    @patch("accounts.auth_session.get_supabase_client")
    def test_authenticated_session(self, mock_client):

        self.request.session["supabase_access_token"] = (
            "test-access-token"
        )

        self.request.session["supabase_refresh_token"] = (
            "test-refresh-token"
        )

        supabase = mock_client.return_value

        session = MagicMock()

        session.access_token = "new-access-token"
        session.refresh_token = "new-refresh-token"

        supabase.auth.set_session.return_value.session = session

        verified_user = MagicMock()

        supabase.auth.get_user.return_value.user = verified_user

        client, user = get_authenticated_client(
            self.request
        )

        self.assertEqual(client, supabase)
        self.assertEqual(user, verified_user)

        supabase.auth.set_session.assert_called_once_with(
            "test-access-token",
            "test-refresh-token"
        )

        supabase.auth.get_user.assert_called_once()

        self.assertEqual(
            self.request.session["supabase_access_token"],
            "new-access-token"
        )

        self.assertEqual(
            self.request.session["supabase_refresh_token"],
            "new-refresh-token"
        )

    @patch("accounts.auth_session.get_supabase_client")
    def test_invalid_jwt_rejected(self, mock_client):

        from supabase_auth.errors import AuthInvalidJwtError

        self.request.session = {
            "supabase_access_token": "invalid-access-token",
            "supabase_refresh_token": "invalid-refresh-token",
        }

        supabase = mock_client.return_value

        supabase.auth.set_session.side_effect = (
            AuthInvalidJwtError("Invalid JWT structure")
        )

        client, user = get_authenticated_client(
            self.request
        )

        self.assertIsNone(client)
        self.assertIsNone(user)
        self.assertEqual(self.request.session, {})

        supabase.auth.get_user.assert_not_called()

    @patch("accounts.auth_session.get_supabase_client")
    def test_network_failure_handled(self, mock_client):

        from supabase_auth.errors import AuthRetryableError

        self.request.session = {
            "supabase_access_token": "test-access-token",
            "supabase_refresh_token": "test-refresh-token",
        }

        supabase = mock_client.return_value

        supabase.auth.set_session.side_effect = (
            AuthRetryableError("Temporary network failure", 503)
        )

        client, user = get_authenticated_client(
            self.request
        )

        self.assertIsNone(client)
        self.assertIsNone(user)

        self.assertEqual(
            self.request.session["supabase_access_token"],
            "test-access-token"
        )

        self.assertEqual(
            self.request.session["supabase_refresh_token"],
            "test-refresh-token"
        )

        supabase.auth.get_user.assert_not_called()
