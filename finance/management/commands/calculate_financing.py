from __future__ import annotations

import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from finance.services import persist_financing_plan


class Command(BaseCommand):
    help = (
        "Carga movimientos desde un JSON, genera el plan de financiación y "
        "guarda los desembolsos y aportes en la base de datos."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--data-file",
            default="datos_gerpro_prueba.json",
            help="Ruta hacia el archivo con los movimientos (default: %(default)s).",
        )
        parser.add_argument("--project-name", required=True, help="Nombre del proyecto.")
        parser.add_argument("--project-slug", required=True, help="Slug del proyecto.")
        parser.add_argument(
            "--credit-limit",
            type=float,
            required=True,
            help="Cupo total del crédito constructor.",
        )
        parser.add_argument(
            "--max-monthly-draw",
            type=float,
            required=True,
            help="Porcentaje máximo desembolsable cada mes (ej. 0.08).",
        )
        parser.add_argument(
            "--credit-start",
            type=int,
            required=True,
            help="Periodo inicial para desembolsos.",
        )
        parser.add_argument(
            "--credit-end",
            type=int,
            required=True,
            help="Periodo final para desembolsos.",
        )
        parser.add_argument(
            "--annual-rate",
            type=float,
            required=True,
            help="Tasa nominal anual (ej. 0.12).",
        )

    def handle(self, *args, **options):
        data_path = Path(options["data_file"])
        if not data_path.exists():
            raise CommandError(f"Archivo de movimientos no encontrado: {data_path}")

        try:
            dataset = json.loads(data_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise CommandError(f"El archivo JSON es inválido: {exc}")

        disbursements, contributions = persist_financing_plan(
            dataset,
            project_name=options["project_name"],
            project_slug=options["project_slug"],
            credit_limit=options["credit_limit"],
            max_monthly_draw=options["max_monthly_draw"],
            credit_start=options["credit_start"],
            credit_end=options["credit_end"],
            annual_rate=options["annual_rate"],
        )

        total_disbursement = round(sum(item["valor"] for item in disbursements), 2)
        total_contribution = round(sum(item["valor"] for item in contributions), 2)

        self.stdout.write(self.style.SUCCESS("Plan financiero generado correctamente."))
        self.stdout.write(f"Desembolsos totales: ${total_disbursement:,.2f}")
        self.stdout.write(f"Aportes de capital totales: ${total_contribution:,.2f}")

