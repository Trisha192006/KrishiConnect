
document.addEventListener("DOMContentLoaded", function () {

    // =========================
    // USER ROLE SELECTION
    // =========================

    const roleButtons = document.querySelectorAll(".role-btn");
    const selectedRole = document.getElementById("selected-role");

    roleButtons.forEach(button => {

        button.addEventListener("click", function () {

            roleButtons.forEach(btn => {
                btn.classList.remove("active");
                btn.setAttribute("aria-pressed", "false");
            });

            this.classList.add("active");
            this.setAttribute("aria-pressed", "true");

            selectedRole.value = this.dataset.role;

        });

    });


    // =========================
    // MOBILE NUMBER VALIDATION
    // =========================

    const phoneInput = document.getElementById("phone-number");

    if (phoneInput) {

        phoneInput.addEventListener("input", function () {

            this.value = this.value
                .replace(/[^0-9]/g, "")
                .slice(0, 10);

        });

    }


    // =========================
    // LANGUAGE SWITCHING
    // =========================

    const translations = {

        en: {
            subtitle: "Secure OTP Login to KrishiConnect",
            farmer: "Farmer / Buyer",
            vendor: "Local Vendor",
            phone: "Mobile Number",
            otp: "Get OTP"
        },

        hi: {
            subtitle: "कृषि कनेक्ट में सुरक्षित ओटीपी लॉगिन",
            farmer: "किसान / खरीदार",
            vendor: "स्थानीय विक्रेता",
            phone: "मोबाइल नंबर",
            otp: "ओटीपी प्राप्त करें"
        }

    };

    document.querySelectorAll("[data-lang]").forEach(button => {

        button.addEventListener("click", function () {

            const lang = this.dataset.lang;
            const text = translations[lang];

            document.documentElement.lang = lang;

            document.getElementById("login-subtitle").textContent =
                text.subtitle;

            document.getElementById("farmer-label").textContent =
                text.farmer;

            document.getElementById("vendor-label").textContent =
                text.vendor;

            document.getElementById("phone-label").textContent =
                text.phone;

            document.getElementById("otp-label").textContent =
                text.otp;

        });

    });


    // =========================
    // OTP INPUT VALIDATION
    // =========================

    const otpInput = document.getElementById("otp-code");

    if (otpInput) {

        otpInput.addEventListener("input", function () {

            this.value = this.value
                .replace(/[^0-9]/g, "")
                .slice(0, 6);

        });

    }


    // =========================
    // RESEND OTP COUNTDOWN
    // =========================

    const resendButton = document.getElementById("resend-otp");

    if (resendButton) {

        let seconds = 60;

        resendButton.disabled = true;

        resendButton.textContent = `Resend OTP (${seconds}s)`;

        const timer = setInterval(function () {

            seconds--;

            resendButton.textContent =
                `Resend OTP (${seconds}s)`;

            if (seconds <= 0) {

                clearInterval(timer);

                resendButton.disabled = false;

                resendButton.textContent = "Resend OTP";

            }

        }, 1000);

    }

});

document.addEventListener("DOMContentLoaded", function () {

    const pincodeInput = document.getElementById("pincode");

    if (pincodeInput) {

        pincodeInput.addEventListener("input", function () {

            this.value = this.value
                .replace(/[^0-9]/g, "")
                .slice(0, 6);

        });

    }

});


/* =========================
   FORM SUBMISSION PROTECTION
========================= */

document.addEventListener("DOMContentLoaded", function () {

    document.querySelectorAll(
        'form[method="POST"], form[method="post"]'
    ).forEach(form => {

        form.addEventListener("submit", function (event) {

            if (form.dataset.submitting === "true") {
                event.preventDefault();
                return;
            }

            form.dataset.submitting = "true";

            const button = event.submitter ||
                form.querySelector('button[type="submit"]');

            if (button) {

                button.disabled = true;
                button.textContent = "Please wait...";

            }

        });

    });

    window.addEventListener("pageshow", function (event) {

        if (event.persisted) {
            window.location.reload();
        }

    });

});
