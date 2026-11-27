
import re
import time

from django.db import IntegrityError, transaction
from .forms import RegistrationForm
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST

from .models import User
from .otp_service import generate_otp, verify_otp


def login_view(request):

    if request.method == "POST":

        phone_number = request.POST.get(
            "phone_number", ""
        ).strip()

        role = request.POST.get("role", "farmer")

        if not re.fullmatch(r"[6-9][0-9]{9}", phone_number):

            return render(
                request,
                "accounts/login.html",
                {"error": "Enter a valid mobile number."}
            )

        if role not in ["farmer", "vendor"]:
            role = "farmer"

        success, message = generate_otp(phone_number)

        if not success:

            return render(
                request,
                "accounts/login.html",
                {"error": message}
            )

        request.session.cycle_key()

        request.session.pop("verified_phone", None)
        request.session["otp_phone"] = phone_number
        request.session["selected_role"] = role

        return redirect("accounts:verify_otp")

    return render(request, "accounts/login.html")


def verify_otp_view(request):

    phone_number = request.session.get("otp_phone")

    if not phone_number:
        return redirect("accounts:login")

    context = {
        "phone_number": phone_number,
        "development_mode": (
            settings.DEBUG and settings.OTP_DEVELOPMENT_MODE
        ),
    }

    if request.method == "POST":

        entered_otp = request.POST.get("otp", "").strip()

        if not re.fullmatch(r"[0-9]{6}", entered_otp):

            context["error"] = "Enter a valid six-digit OTP."

            return render(
                request,
                "accounts/verify_otp.html",
                context
            )

        success, message = verify_otp(
            phone_number,
            entered_otp
        )

        if not success:

            context["error"] = message

            return render(
                request,
                "accounts/verify_otp.html",
                context
            )

        request.session.pop("otp_phone", None)
        request.session.cycle_key()

        user = User.objects.filter(
            phone_number=phone_number
        ).first()

        if user:

            # Keep administrator authentication separate
            if user.is_staff or user.is_superuser:
                context["error"] = (
                    "Administrator accounts must use the admin login."
                )
                return render(
                    request,
                    "accounts/verify_otp.html",
                    context
                )

            if not user.is_active:
                context["error"] = "This account is inactive."
                return render(
                    request,
                    "accounts/verify_otp.html",
                    context
                )

            user.is_phone_verified = True
            user.save(update_fields=["is_phone_verified"])

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend"
            )

            return redirect("accounts:dashboard")

        request.session["verified_phone"] = phone_number
        request.session["verified_at"] = int(time.time())

        return redirect("accounts:signup")

    return render(
        request,
        "accounts/verify_otp.html",
        context
    )


@require_POST
def resend_otp_view(request):

    phone_number = request.session.get("otp_phone")

    if not phone_number:
        return redirect("accounts:login")

    success, message = generate_otp(phone_number)

    return render(
        request,
        "accounts/verify_otp.html",
        {
            "phone_number": phone_number,
            "success": message if success else "",
            "error": message if not success else "",
            "development_mode": (
                settings.DEBUG and settings.OTP_DEVELOPMENT_MODE
            ),
        }
    )



def signup_view(request):

    phone_number = request.session.get("verified_phone")
    verified_at = request.session.get("verified_at", 0)

    # Registration session expires after 15 minutes

    if not phone_number or time.time() - verified_at > 900:

        request.session.pop("verified_phone", None)
        request.session.pop("verified_at", None)

        return redirect("accounts:login")


    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            try:

                with transaction.atomic():

                    user = form.save(commit=False)

                    user.phone_number = phone_number
                    user.is_phone_verified = True
                    user.is_staff = False
                    user.is_superuser = False
                    user.is_active = True

                    user.set_unusable_password()

                    user.save()

            except IntegrityError:

                return render(
                    request,
                    "accounts/signup.html",
                    {
                        "form": form,
                        "phone_number": phone_number,
                        "error": "Registration could not be completed. Please try logging in again.",
                    }
                )

            # Clear temporary verification data

            request.session.pop("verified_phone", None)
            request.session.pop("verified_at", None)
            request.session.pop("selected_role", None)

            # Automatically log in the registered user

            login(
                request,
                user,
                backend="django.contrib.auth.backends.ModelBackend"
            )

            return redirect("accounts:dashboard")

    else:

        form = RegistrationForm()


    return render(
        request,
        "accounts/signup.html",
        {
            "phone_number": phone_number,
            "form": form,
        }
    )



@login_required(login_url="accounts:login")
def dashboard_view(request):
    return render(request, "accounts/dashboard.html")


@require_POST
def logout_view(request):
    logout(request)
    return redirect("accounts:login")