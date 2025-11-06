"""CLI helper to run the financing plan with user-provided parameters."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from financing import calculate_financing_plan


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Gerpro financing plan.")
    parser.add_argument(
        "--data-file",
        default="datos_gerpro_prueba.json",
        help="Path to the JSON file with the movements (default: %(default)s).",
    )
    return parser.parse_args()


def prompt_positive_float(message: str) -> float:
    """Ask the user for a positive float value."""
    while True:
        raw = input(f"{message}: ").strip().replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            print("Ingresa un numero valido.")
            continue
        if value <= 0:
            print("El valor debe ser mayor que cero.")
            continue
        return value


def prompt_percentage(message: str) -> float:
    """Ask for a percentage (accept 0-1 or 0-100)."""
    while True:
        raw = input(f"{message} (ej. 0.08 o 8): ").strip().replace("%", "").replace(",", "")
        try:
            value = float(raw)
        except ValueError:
            print("Ingresa un numero valido.")
            continue
        if value < 0:
            print("El porcentaje no puede ser negativo.")
            continue
        if value > 1:
            value /= 100
        return value


def prompt_period(message: str) -> int:
    """Ask the user for a period (positive integer)."""
    while True:
        raw = input(f"{message}: ").strip()
        if not raw.isdigit():
            print("Ingresa un numero entero positivo.")
            continue
        value = int(raw)
        if value < 1:
            print("El periodo debe ser mayor o igual a 1.")
            continue
        return value


def main() -> None:
    args = parse_args()
    data_path = Path(args.data_file)
    dataset = json.loads(data_path.read_text(encoding="utf-8"))

    print("Ingresa los parametros del credito:")
    credit_limit = prompt_positive_float("Cupo del credito")
    max_monthly_draw = prompt_percentage("Porcentaje maximo desembolso mensual")
    credit_start = prompt_period("Periodo inicial del credito")
    while True:
        credit_end = prompt_period("Periodo final del credito")
        if credit_end < credit_start:
            print("El periodo final debe ser mayor o igual al periodo inicial.")
            continue
        break
    annual_interest = prompt_percentage("Tasa de interes anual")

    disbursements, contributions = calculate_financing_plan(
        dataset,
        credit_limit=credit_limit,
        max_monthly_draw_percentage=max_monthly_draw,
        credit_start_period=credit_start,
        credit_end_period=credit_end,
        annual_interest_rate=annual_interest,
    )

    print("Desembolsos del credito:")
    for item in disbursements:
        print(f"  Periodo {item['periodo']:>2}: ${item['valor']:,.2f}")

    print("\nAportes de capital requeridos:")
    for item in contributions:
        print(f"  Periodo {item['periodo']:>2}: ${item['valor']:,.2f}")

    total_disbursement = round(sum(item["valor"] for item in disbursements), 2)
    total_contribution = round(sum(item["valor"] for item in contributions), 2)

    print("\nResumen:")
    print(f"  Total desembolsado del credito: ${total_disbursement:,.2f}")
    print(f"  Total aportes de capital:       ${total_contribution:,.2f}")


if __name__ == "__main__":
    main()

