

from __future__ import annotations

from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class TimeStampedModel(models.Model):
    """Abstract base that captures creation and update timestamps."""

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Project(TimeStampedModel):
    """High level real estate project."""

    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class SubStage(TimeStampedModel):
    """Individual tower or construction phase inside a project."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="sub_stages")
    name = models.CharField(max_length=120)
    code = models.CharField(max_length=30, blank=True)

    class Meta:
        unique_together = ("project", "name")
        ordering = ("project__name", "name")

    def __str__(self) -> str:
        return f"{self.project.name} - {self.name}"


class CashFlowEntry(TimeStampedModel):
    """Monthly income or cost per sub-stage."""

    class Concept(models.TextChoices):
        INCOME = "income", "Income"
        COST = "cost", "Cost"

    sub_stage = models.ForeignKey(SubStage, on_delete=models.CASCADE, related_name="cash_flow_entries")
    period = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    concept = models.CharField(max_length=10, choices=Concept.choices)
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ("period", "sub_stage__name")
        unique_together = ("sub_stage", "period", "concept")

    def __str__(self) -> str:
        return f"{self.sub_stage} periodo {self.period} ({self.get_concept_display()}): {self.amount}"


class ConstructionCredit(TimeStampedModel):
    """Configuration for the constructor credit that finances the project."""

    project = models.OneToOneField(Project, on_delete=models.CASCADE, related_name="construction_credit")
    total_limit = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
        help_text="Maximum amount that can be disbursed.",
    )
    max_monthly_draw_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0000"))],
        help_text="Monthly draw cap expressed as a fraction of the total limit (e.g. 0.08).",
    )
    start_period = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    end_period = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    annual_interest_rate = models.DecimalField(
        max_digits=5,
        decimal_places=4,
        validators=[MinValueValidator(Decimal("0.0000"))],
        help_text="Annual nominal rate expressed as a fraction (e.g. 0.12).",
    )

    class Meta:
        ordering = ("project__name",)

    def __str__(self) -> str:
        return f"Credito {self.project.name}"


class CreditDraw(TimeStampedModel):
    """Stores the disbursements calculated for a given credit configuration."""

    credit = models.ForeignKey(ConstructionCredit, on_delete=models.CASCADE, related_name="credit_draws")
    period = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )

    class Meta:
        ordering = ("period",)
        unique_together = ("credit", "period")

    def __str__(self) -> str:
        return f"{self.credit.project.name} periodo {self.period}: {self.amount}"


class CapitalContribution(TimeStampedModel):
    """Records months where equity contributions were required."""

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="capital_contributions")
    period = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    amount = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        validators=[MinValueValidator(Decimal("0.00"))],
    )
    note = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ("period",)
        unique_together = ("project", "period")

    def __str__(self) -> str:
        return f"{self.project.name} periodo {self.period}: {self.amount}"

