from __future__ import annotations

from django.urls import path

from . import views

app_name = "finance"

urlpatterns = [
    path("", views.financing_plan_view, name="plan"),
]

