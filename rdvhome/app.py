# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function, unicode_literals

from django import forms
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

from rdvhome.gpio import get_input, RASPBERRY, set_output

SwitchForm = type(
    "SwitchForm",
    (forms.Form, ), {
        str(n): forms.BooleanField(
            required = False,
            **data
            )
        for n, data in RASPBERRY.gpio.items()
    }
)

def home(request):
    if request.method == "POST":
        form = SwitchForm(request.POST)
    else:
        form = SwitchForm(
            initial = {
                str(n): get_input(n)
                for n in RASPBERRY.gpio.keys()
                }
            )

    if form.is_valid():
        for n, value in form.cleaned_data.items():
            set_output(int(n), value)

        return HttpResponseRedirect("/")

    return TemplateResponse(request, "index.html", {"form": form})