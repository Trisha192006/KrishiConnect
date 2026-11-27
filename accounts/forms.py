
from django import forms
from .models import Profile


class RegistrationForm(forms.ModelForm):

    class Meta:
        model = Profile

        fields = [
            "name",
            "village",
            "district",
            "state",
            "pincode",
        ]

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        for field in self.fields.values():
            field.required = True

    def clean_pincode(self):

        pincode = self.cleaned_data["pincode"].strip()

        if (
            len(pincode) != 6
            or not pincode.isascii()
            or not pincode.isdigit()
            or pincode.startswith("0")
        ):
            raise forms.ValidationError(
                "Enter a valid six-digit pincode."
            )

        return pincode
