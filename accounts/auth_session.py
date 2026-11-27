
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthRetryableError,
)
from httpx import RequestError

from .supabase_client import get_supabase_client


def save_auth_session(request, session):

    request.session["supabase_access_token"] = (
        session.access_token
    )

    request.session["supabase_refresh_token"] = (
        session.refresh_token
    )


def clear_auth_session(request):

    request.session.pop("supabase_access_token", None)
    request.session.pop("supabase_refresh_token", None)


def get_authenticated_client(request):

    access_token = request.session.get(
        "supabase_access_token"
    )

    refresh_token = request.session.get(
        "supabase_refresh_token"
    )

    if not access_token or not refresh_token:
        return None, None

    supabase = get_supabase_client()

    try:

        response = supabase.auth.set_session(
            access_token,
            refresh_token
        )

        if not response.session:
            clear_auth_session(request)
            return None, None

        save_auth_session(request, response.session)

        user_response = supabase.auth.get_user()

        if not user_response or not user_response.user:
            clear_auth_session(request)
            return None, None

        return supabase, user_response.user

    except (AuthApiError, AuthInvalidJwtError):

        clear_auth_session(request)
        return None, None

    except (AuthRetryableError, RequestError):

        return None, None
