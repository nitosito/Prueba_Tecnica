from __future__ import annotations

import json

from django.contrib import messages
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from .forms import FinancingPlanForm
from .services import persist_financing_plan


def financing_plan_view(request: HttpRequest) -> HttpResponse:
    """Handle the financing plan form and persist results."""

    context: dict = {}
    if request.method == "POST":
        form = FinancingPlanForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                dataset = json.loads(form.cleaned_data["movements_file"].read().decode("utf-8"))
            except json.JSONDecodeError as exc:
                form.add_error("movements_file", f"Archivo JSON inválido: {exc}")
            else:
                project_name = form.cleaned_data["project_name"]
                project_slug = form.cleaned_data["project_slug"]
                credit_limit = form.cleaned_data["credit_limit"]
                max_draw = form.cleaned_data["max_monthly_draw"]
                credit_start = form.cleaned_data["credit_start"]
                credit_end = form.cleaned_data["credit_end"]
                annual_rate = form.cleaned_data["annual_rate"]

                try:
                    disbursements, contributions = persist_financing_plan(
                        dataset,
                        project_name=project_name,
                        project_slug=project_slug,
                        credit_limit=credit_limit,
                        max_monthly_draw=max_draw,
                        credit_start=credit_start,
                        credit_end=credit_end,
                        annual_rate=annual_rate,
                    )
                except ValueError as exc:
                    form.add_error(None, str(exc))
                else:
                    messages.success(request, "Plan financiero generado exitosamente.")
                    context.update(
                        {
                            "disbursements": disbursements,
                            "contributions": contributions,
                            "total_disbursement": round(
                                sum(item["valor"] for item in disbursements), 2
                            ),
                            "total_contribution": round(
                                sum(item["valor"] for item in contributions), 2
                            ),
                            "project_name": project_name,
                        }
                    )
                    form = FinancingPlanForm()  # reset for new submissions
        context["form"] = form
    else:
        context["form"] = FinancingPlanForm()

    return render(request, "finance/plan_form.html", context)
