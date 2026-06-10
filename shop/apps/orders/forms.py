from django import forms
from django.urls import reverse_lazy

from .models import Order

_PAYMENT_CHOICES = [
    (Order.PaymentMethod.MONOBANK, "MonoBank (онлайн)"),
    (Order.PaymentMethod.COD, "Накладений платіж"),
]


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "first_name", "last_name", "email", "phone",
            "delivery_method", "delivery_address",
            "nova_poshta_city", "nova_poshta_city_ref",
            "nova_poshta_warehouse", "nova_poshta_warehouse_ref",
            "payment_method", "comment",
        ]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Ім'я"}),
            "last_name": forms.TextInput(attrs={"class": "form-input", "placeholder": "Прізвище"}),
            "email": forms.EmailInput(attrs={"class": "form-input", "placeholder": "Електронна пошта"}),
            "phone": forms.TextInput(attrs={"class": "form-input", "placeholder": "+380..."}),
            "delivery_method": forms.Select(attrs={
                "class": "form-select",
                "id": "id_delivery_method",
            }),
            "delivery_address": forms.Textarea(attrs={"class": "form-input", "rows": 2}),
            # NP city: search input + select list loaded via JS
            "nova_poshta_city": forms.TextInput(attrs={
                "class": "form-input",
                "placeholder": "Почніть вводити назву міста...",
                "autocomplete": "off",
                "id": "id_nova_poshta_city_input",
                "aria-describedby": "np-city-hint",
            }),
            # NP city ref: hidden, populated by JS
            "nova_poshta_city_ref": forms.HiddenInput(attrs={"id": "id_nova_poshta_city_ref"}),
            # NP warehouse: select, populated by HTMX after city selected
            "nova_poshta_warehouse": forms.HiddenInput(attrs={"id": "id_nova_poshta_warehouse"}),
            # NP warehouse ref: hidden, populated by JS
            "nova_poshta_warehouse_ref": forms.HiddenInput(attrs={"id": "id_nova_poshta_warehouse_ref"}),
            "payment_method": forms.RadioSelect(attrs={"class": "payment-radio"}),
            "comment": forms.Textarea(attrs={"class": "form-input", "rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["payment_method"].choices = _PAYMENT_CHOICES
        self.fields["payment_method"].initial = Order.PaymentMethod.MONOBANK
        self.fields["nova_poshta_city_ref"].required = False
        self.fields["nova_poshta_warehouse_ref"].required = False
        self.fields["nova_poshta_city"].required = False
        self.fields["nova_poshta_warehouse"].required = False
        self.fields["delivery_address"].required = False
