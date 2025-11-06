from __future__ import annotations

import json
from io import StringIO
from pathlib import Path

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse

from financing import calculate_financing_plan

from finance import services
from finance.models import (
    CapitalContribution,
    CashFlowEntry,
    ConstructionCredit,
    CreditDraw,
    Project,
)


TEST_DATASET = [
    {"subetapa": "Torre 1", "valor": 100, "periodo": 1, "concepto": "ingresos"},
    {"subetapa": "Torre 1", "valor": 150, "periodo": 1, "concepto": "costos"},
    {"subetapa": "Torre 1", "valor": 110, "periodo": 2, "concepto": "ingresos"},
    {"subetapa": "Torre 1", "valor": 160, "periodo": 2, "concepto": "costos"},
    {"subetapa": "Torre 1", "valor": 250, "periodo": 3, "concepto": "ingresos"},
]

PARAMS = dict(
    project_name="Proyecto Test",
    project_slug="proyecto-test",
    credit_limit=100.0,
    max_monthly_draw=0.6,
    credit_start=1,
    credit_end=2,
    annual_rate=0.12,
)


class PersistFinancingPlanTests(TestCase):
    def test_persist_financing_plan_creates_records(self):
        expected_disbursements, expected_contributions = calculate_financing_plan(
            TEST_DATASET,
            credit_limit=PARAMS["credit_limit"],
            max_monthly_draw_percentage=PARAMS["max_monthly_draw"],
            credit_start_period=PARAMS["credit_start"],
            credit_end_period=PARAMS["credit_end"],
            annual_interest_rate=PARAMS["annual_rate"],
        )

        disbursements, contributions = services.persist_financing_plan(
            TEST_DATASET,
            **PARAMS,
        )

        self.assertEqual(disbursements, expected_disbursements)
        self.assertEqual(contributions, expected_contributions)
        self.assertEqual(Project.objects.count(), 1)
        project = Project.objects.get()
        self.assertEqual(project.sub_stages.count(), 1)
        self.assertEqual(CashFlowEntry.objects.count(), len(TEST_DATASET))
        self.assertEqual(CreditDraw.objects.count(), len(disbursements))
        self.assertEqual(CapitalContribution.objects.count(), len(contributions))


class CalculateFinancingCommandTests(TestCase):
    def test_command_generates_financing_plan(self):
        tmp_path = Path(self._create_temp_json(TEST_DATASET))
        out = StringIO()

        call_command(
            "calculate_financing",
            "--data-file",
            str(tmp_path),
            "--project-name",
            PARAMS["project_name"],
            "--project-slug",
            PARAMS["project_slug"],
            "--credit-limit",
            str(PARAMS["credit_limit"]),
            "--max-monthly-draw",
            str(PARAMS["max_monthly_draw"]),
            "--credit-start",
            str(PARAMS["credit_start"]),
            "--credit-end",
            str(PARAMS["credit_end"]),
            "--annual-rate",
            str(PARAMS["annual_rate"]),
            stdout=out,
        )

        self.assertIn("Plan financiero generado correctamente", out.getvalue())
        credit = ConstructionCredit.objects.get(project__slug=PARAMS["project_slug"])
        self.assertEqual(credit.credit_draws.count(), 2)
        self.assertEqual(CapitalContribution.objects.filter(project=credit.project).count(), 1)

    def _create_temp_json(self, dataset) -> str:
        path = Path(self._get_temp_dir()) / "dataset.json"
        path.write_text(json.dumps(dataset), encoding="utf-8")
        return str(path)

    def _get_temp_dir(self) -> Path:
        path = Path(__file__).resolve().parent / "tmp"
        path.mkdir(exist_ok=True)
        return path


class FinancingPlanViewTests(TestCase):
    def test_view_generates_plan_and_shows_results(self):
        url = reverse("finance:plan")
        upload = SimpleUploadedFile(
            "movements.json",
            json.dumps(TEST_DATASET).encode("utf-8"),
            content_type="application/json",
        )

        response = self.client.post(
            url,
            data={
                "project_name": PARAMS["project_name"],
                "project_slug": PARAMS["project_slug"],
                "credit_limit": PARAMS["credit_limit"],
                "max_monthly_draw": PARAMS["max_monthly_draw"],
                "credit_start": PARAMS["credit_start"],
                "credit_end": PARAMS["credit_end"],
                "annual_rate": PARAMS["annual_rate"],
                "movements_file": upload,
            },
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Plan financiero generado exitosamente")
        self.assertEqual(CreditDraw.objects.count(), 2)
        self.assertEqual(CapitalContribution.objects.count(), 1)
        self.assertIn("total_disbursement", response.context)
        self.assertIn("total_contribution", response.context)

