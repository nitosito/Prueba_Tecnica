"""URL configuration for the Gerpro technical test project."""

from __future__ import annotations

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("finance.urls", namespace="finance")),
]
