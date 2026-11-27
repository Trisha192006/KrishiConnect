
import re

from django.shortcuts import render, redirect
from django.views.decorators.http import require_POST
from django.views.decorators.cache import never_cache
from django.db import IntegrityError, transaction

from supabase_auth.errors import(
    AuthApiError,
    AuthRetryableError,
)
from httpx import RequestError

from .models import Profile
from .forms import RegistrationForm

from .auth_service import (
    send_otp,
    verify_phone_otp,
)

from .auth_session import (
    save_auth_session,
    clear_auth_session,
    get_authenticated_client,
)


# =========================
# LOGIN AND SEND OTP
# =========================

@never_cache
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

        try:

            send_otp(phone_number)

        except (AuthApiError, AuthRetryableError, RequestError, ValueError):

            return render(
                request,
                "accounts/login.html",
                {
                    "error": (
                        "Unable to send OTP. "
                        "Please wait and try again."
                    )
                }
            )

        request.session.cycle_key()

        clear_auth_session(request)

        request.session.pop("verified_phone", None)
        request.session.pop("verified_at", None)

        request.session["otp_phone"] = phone_number
        request.session["selected_role"] = role

        return redirect("accounts:verify_otp")

    return render(request, "accounts/login.html")


# =========================
# VERIFY OTP
# =========================

@never_cache
def verify_otp_view(request):

    phone_number = request.session.get("otp_phone")

    if not phone_number:
        return redirect("accounts:login")

    context = {
        "phone_number": phone_number,
    }

    if request.method == "POST":

        entered_otp = request.POST.get(
            "otp", ""
        ).strip()

        if not re.fullmatch(r"[0-9]{6}", entered_otp):

            context["error"] = (
                "Enter a valid six-digit OTP."
            )

            return render(
                request,
                "accounts/verify_otp.html",
                context
            )

        try:

            response = verify_phone_otp(
                phone_number,
                entered_otp
            )

        except (AuthApiError, AuthRetryableError, RequestError, ValueError):

            context["error"] = (
                "Invalid or expired OTP. "
                "Please try again."
            )

            return render(
                request,
                "accounts/verify_otp.html",
                context
            )

        if not response.user or not response.session:

            context["error"] = (
                "Authentication could not be completed."
            )

            return render(
                request,
                "accounts/verify_otp.html",
                context
            )

        request.session.cycle_key()

        save_auth_session(
            request,
            response.session
        )

        request.session.pop("otp_phone", None)

        # Check application profile, not legacy User

        profile_exists = Profile.objects.filter(
            id=response.user.id
        ).exists()

        if profile_exists:

            request.session.pop("selected_role", None)

            return redirect("accounts:dashboard")

        return redirect("accounts:signup")

    return render(
        request,
        "accounts/verify_otp.html",
        context
    )


# =========================
# RESEND OTP
# =========================

@require_POST
@never_cache
def resend_otp_view(request):

    phone_number = request.session.get("otp_phone")

    if not phone_number:
        return redirect("accounts:login")

    context = {
        "phone_number": phone_number,
    }

    try:

        send_otp(phone_number)

        context["success"] = (
            "OTP requested successfully."
        )

    except (AuthApiError, AuthRetryableError, RequestError, ValueError):

        context["error"] = (
            "Unable to resend OTP. "
            "Please wait and try again."
        )

    return render(
        request,
        "accounts/verify_otp.html",
        context
    )


# =========================
# COMPLETE PROFILE
# =========================

@never_cache
def signup_view(request):

    supabase, auth_user = (
        get_authenticated_client(request)
    )

    if not auth_user:
        return redirect("accounts:login")

    if Profile.objects.filter(id=auth_user.id).exists():
        return redirect("accounts:dashboard")

    phone_number = (
        auth_user.phone or ""
    ).lstrip("+")

    if phone_number.startswith("91"):
        phone_number = phone_number[2:]

    context = {
        "phone_number": phone_number,
    }

    if request.method == "POST":

        form = RegistrationForm(request.POST)

        if form.is_valid():

            try:

                with transaction.atomic():

                    profile = form.save(commit=False)

                    # UUID comes from verified Supabase identity

                    profile.id = auth_user.id

                    profile.save(force_insert=True)

            except IntegrityError:

                context["form"] = form

                context["error"] = (
                    "Profile could not be created. "
                    "Please try again."
                )

                return render(
                    request,
                    "accounts/signup.html",
                    context
                )

            request.session.pop("selected_role", None)

            return redirect("accounts:dashboard")

    else:

        form = RegistrationForm()

    context["form"] = form

    return render(
        request,
        "accounts/signup.html",
        context
    )


# =========================
# PROTECTED DASHBOARD
# =========================

@never_cache
def dashboard_view(request):

    supabase, auth_user = (
        get_authenticated_client(request)
    )

    if not auth_user:
        return redirect("accounts:login")

    profile = Profile.objects.filter(
        id=auth_user.id
    ).first()

    if not profile:
        return redirect("accounts:signup")

    phone_number = (
        auth_user.phone or ""
    ).lstrip("+")

    return render(
        request,
        "accounts/dashboard.html",
        {
            "profile": profile,
            "phone_number": "+" + phone_number,
        }
    )


# =========================
# LOGOUT
# =========================

@require_POST
@never_cache
def logout_view(request):

    supabase, auth_user = (
        get_authenticated_client(request)
    )

    if supabase and auth_user:

        try:

            supabase.auth.sign_out({
                "scope": "local"
            })

        except (AuthApiError,AuthRetryableError, RequestError):

            return render(
                request,
                "accounts/dashboard.html",
                {
                    "profile": Profile.objects.filter(
                        id=auth_user.id
                    ).first(),
                    "phone_number": auth_user.phone,
                    "error": (
                        "Logout could not be completed. "
                        "Please try again."
                    ),
                },
                status=503
            )

    elif request.session.get("supabase_refresh_token"):

        return render(
            request,
            "accounts/login.html",
            {
                "error": (
                    "Unable to contact authentication service. "
                    "Please retry logout."
                )
            },
            status=503
        )

    clear_auth_session(request)

    request.session.pop("otp_phone", None)
    request.session.pop("selected_role", None)
    request.session.cycle_key()

    return redirect("accounts:login")
