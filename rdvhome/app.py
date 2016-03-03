# -*- coding: utf-8 -*-

from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django import forms

from rdvhome.gpio import PINS, get_input, set_output

SwitchForm = type(
    "SwitchForm", 
    (forms.Form, ), {
        str(n): forms.BooleanField(required = False)
        for n in PINS.keys()
    }
)

def home(request):
    form = SwitchForm(
        request.POST or None,
        initial = request.POST or {
            str(n): get_input(n)
            for n in PINS.keys()
            }
        )

    if form.is_valid():
        for n, value in form.cleaned_data.items():
            set_output(int(n), value)

        return HttpResponseRedirect("/")

    return TemplateResponse(request, "index.html", {"form": form})