
from django.conf import settings
from supabase import create_client, Client, ClientOptions


def get_supabase_client() -> Client:

    return create_client(
        settings.SUPABASE_URL,
        settings.SUPABASE_PUBLISHABLE_KEY,
        options=ClientOptions(
            auto_refresh_token=False,
            persist_session=False,
        ),
    )
