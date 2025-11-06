from __future__ import annotations

from decimal import Decimal
from typing import Iterable

from django.db import transaction

from financing import calculate_financing_plan

from .models import (
    CapitalContribution,
    CashFlowEntry,
    ConstructionCredit,
    CreditDraw,
    Project,
    SubStage,
)


def persist_financing_plan(
    dataset: Iterable[dict],
    *,
    project_name: str,
    project_slug: str,
    credit_limit: float,
    max_monthly_draw: float,
    credit_start: int,
    credit_end: int,
    annual_rate: float,
) -> tuple[list[dict], list[dict]]:
    """Store movements, credit config and resulting schedules in the database."""

    dataset = list(dataset)
    if not dataset:
        raise ValueError("El archivo no contiene movimientos.")

    with transaction.atomic():
        project, created = Project.objects.get_or_create(
            slug=project_slug,
            defaults={"name": project_name},
        )
        if not created and project.name != project_name:
            project.name = project_name
            project.save(update_fields=["name"])

        # Remove previous data linked to the project.
        CapitalContribution.objects.filter(project=project).delete()
        project.sub_stages.all().delete()

        credit = getattr(project, "construction_credit", None)
        if credit:
            credit.credit_draws.all().delete()
            credit.delete()

        sub_stage_map: dict[str, SubStage] = {}
        valid_concepts = {"ingresos": CashFlowEntry.Concept.INCOME, "costos": CashFlowEntry.Concept.COST}

        for movement in dataset:
            try:
                substage_name = movement["subetapa"]
                value = Decimal(str(movement["valor"]))
                period = int(movement["periodo"])
                concept_key = str(movement["concepto"]).lower()
            except (KeyError, TypeError, ValueError) as exc:
                raise ValueError(f"Movimiento inválido: {movement}") from exc

            if concept_key not in valid_concepts:
                raise ValueError(f"Concepto desconocido: {concept_key}")
            if period < 1:
                raise ValueError(f"Periodo inválido en movimiento: {movement}")

            sub_stage = sub_stage_map.get(substage_name)
            if not sub_stage:
                sub_stage = SubStage.objects.create(project=project, name=substage_name)
                sub_stage_map[substage_name] = sub_stage

            CashFlowEntry.objects.create(
                sub_stage=sub_stage,
                period=period,
                concept=valid_concepts[concept_key],
                amount=value,
            )

        credit = ConstructionCredit.objects.create(
            project=project,
            total_limit=Decimal(str(credit_limit)),
            max_monthly_draw_rate=Decimal(str(max_monthly_draw)),
            start_period=credit_start,
            end_period=credit_end,
            annual_interest_rate=Decimal(str(annual_rate)),
        )

        disbursements, contributions = calculate_financing_plan(
            dataset,
            credit_limit=credit_limit,
            max_monthly_draw_percentage=max_monthly_draw,
            credit_start_period=credit_start,
            credit_end_period=credit_end,
            annual_interest_rate=annual_rate,
        )

        CreditDraw.objects.bulk_create(
            [
                CreditDraw(
                    credit=credit,
                    period=item["periodo"],
                    amount=Decimal(str(item["valor"])),
                )
                for item in disbursements
            ]
        )

        CapitalContribution.objects.bulk_create(
            [
                CapitalContribution(
                    project=project,
                    period=item["periodo"],
                    amount=Decimal(str(item["valor"])),
                )
                for item in contributions
            ]
        )

    return disbursements, contributions

