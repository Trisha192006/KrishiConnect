
import secrets
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.hashers import (
    make_password,
    check_password,
)
from django.db import transaction
from django.utils import timezone

from .models import OTPVerification


def generate_otp(phone_number):

    if not settings.DEBUG or not settings.OTP_DEVELOPMENT_MODE:
        return False, "OTP delivery service is not configured."

    with transaction.atomic():

        record, created = (
            OTPVerification.objects.select_for_update()
            .get_or_create(
                phone_number=phone_number,
                defaults={
                    "otp_hash": "",
                    "expires_at": timezone.now(),
                },
            )
        )

        now = timezone.now()

        if not created:

            elapsed = (
                now - record.created_at
            ).total_seconds()

            if elapsed < settings.OTP_RESEND_SECONDS:
                remaining = int(
                    settings.OTP_RESEND_SECONDS - elapsed
                ) + 1

                return False, (
                    f"Please wait {remaining} seconds."
                )

        otp = f"{secrets.randbelow(1000000):06d}"

        record.otp_hash = make_password(otp)
        record.created_at = now

        record.expires_at = now + timedelta(
            seconds=settings.OTP_EXPIRY_SECONDS
        )

        record.attempts = 0
        record.is_used = False
        record.save()

    # Local development only
    print(f"\n[DEVELOPMENT OTP]: {otp}\n")

    return True, "OTP generated successfully."


def verify_otp(phone_number, entered_otp):

    with transaction.atomic():

        record = (
            OTPVerification.objects.select_for_update()
            .filter(phone_number=phone_number)
            .first()
        )

        if record is None:
            return False, "Please request an OTP first."

        if record.is_used:
            return False, "This OTP has already been used."

        if timezone.now() >= record.expires_at:
            return False, "OTP expired. Request a new OTP."

        if record.attempts >= settings.OTP_MAX_ATTEMPTS:
            return False, "Too many attempts. Request a new OTP."

        if not check_password(entered_otp, record.otp_hash):

            record.attempts += 1
            record.save(update_fields=["attempts"])

            return False, "Incorrect OTP."

        record.is_used = True
        record.save(update_fields=["is_used"])

        return True, "OTP verified successfully."
