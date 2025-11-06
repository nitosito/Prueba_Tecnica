from __future__ import annotations

from django.contrib import admin

from . import models


@admin.register(models.Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "created_at", "updated_at")
    search_fields = ("name", "slug")


@admin.register(models.SubStage)
class SubStageAdmin(admin.ModelAdmin):
    list_display = ("name", "project", "code", "created_at")
    list_filter = ("project",)
    search_fields = ("name", "code")


@admin.register(models.CashFlowEntry)
class CashFlowEntryAdmin(admin.ModelAdmin):
    list_display = ("sub_stage", "period", "concept", "amount")
    list_filter = ("concept", "sub_stage__project")
    search_fields = ("sub_stage__name",)


@admin.register(models.ConstructionCredit)
class ConstructionCreditAdmin(admin.ModelAdmin):
    list_display = ("project", "total_limit", "max_monthly_draw_rate", "start_period", "end_period")
    search_fields = ("project__name",)


@admin.register(models.CreditDraw)
class CreditDrawAdmin(admin.ModelAdmin):
    list_display = ("credit", "period", "amount")
    list_filter = ("credit__project",)


@admin.register(models.CapitalContribution)
class CapitalContributionAdmin(admin.ModelAdmin):
    list_display = ("project", "period", "amount")
    list_filter = ("project",)
