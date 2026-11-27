
import re

from .supabase_client import get_supabase_client


def normalize_phone(phone_number):

    phone_number = phone_number.strip()

    if not re.fullmatch(r"[6-9][0-9]{9}", phone_number):
        raise ValueError("Enter a valid Indian mobile number.")

    return f"+91{phone_number}"


def send_otp(phone_number):

    phone = normalize_phone(phone_number)

    supabase = get_supabase_client()

    return supabase.auth.sign_in_with_otp({
        "phone": phone,
        "options": {
            "should_create_user": True,
            "channel": "sms",
        },
    })


def verify_phone_otp(phone_number, otp):

    phone = normalize_phone(phone_number)

    if not re.fullmatch(r"[0-9]{6}", otp):
        raise ValueError("Enter a valid six-digit OTP.")

    supabase = get_supabase_client()

    return supabase.auth.verify_otp({
        "phone": phone,
        "token": otp,
        "type": "sms",
    })
