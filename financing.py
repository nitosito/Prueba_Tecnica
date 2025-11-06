"""Financial planning utilities for the Gerpro technical test.

This module provides a function that receives the commercial and
construction cash movements for the sub-stages of a project and
produces the schedule of credit disbursements and contributions
required to keep the leveraged cash flow non-negative.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple


@dataclass(frozen=True)
class Movement:
    """Normalized representation of a monthly movement."""

    subetapa: str
    valor: float
    periodo: int
    concepto: str

    @classmethod
    def from_raw(cls, raw: Dict) -> "Movement":
        """Build a movement instance from a dictionary, performing validation."""
        try:
            subetapa = str(raw["subetapa"])
            valor = float(raw["valor"])
            periodo = int(raw["periodo"])
            concepto = str(raw["concepto"]).lower()
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"Movimiento invalido: {raw!r}") from exc

        if periodo < 1:
            raise ValueError(f"El periodo debe ser mayor o igual a 1: {raw!r}")

        if concepto not in {"ingresos", "costos"}:
            raise ValueError(f"Concepto desconocido: {concepto!r}")

        return cls(subetapa=subetapa, valor=valor, periodo=periodo, concepto=concepto)


def calculate_financing_plan(
    movements: Iterable[Dict],
    credit_limit: float,
    max_monthly_draw_percentage: float,
    credit_start_period: int,
    credit_end_period: int,
    annual_interest_rate: float,
) -> Tuple[List[Dict[str, float]], List[Dict[str, float]]]:
    """Compute the credit disbursement plan and equity contributions.

    Args:
        movements: Iterable of dictionaries that describe the monthly movements.
        credit_limit: Maximum credit amount available for the project.
        max_monthly_draw_percentage: Upper bound (0-1) of the credit that can be
            disbursed in a single period.
        credit_start_period: First period in which the credit is available.
        credit_end_period: Last period in which the credit can be disbursed.
        annual_interest_rate: Annual nominal interest rate expressed as a decimal.

    Returns:
        Tuple made of:
            - List of dictionaries representing the credit disbursements per period.
            - List of dictionaries representing the equity contributions per period.
    """
    if credit_limit < 0:
        raise ValueError("El cupo del credito no puede ser negativo.")

    if not 0 <= max_monthly_draw_percentage <= 1:
        raise ValueError("El porcentaje maximo por mes debe estar entre 0 y 1.")

    if credit_start_period < 1 or credit_end_period < credit_start_period:
        raise ValueError("El rango de periodos de credito es invalido.")

    monthly_draw_cap = credit_limit * max_monthly_draw_percentage
    monthly_interest_rate = annual_interest_rate / 12

    normalized: List[Movement] = [Movement.from_raw(item) for item in movements]
    if not normalized:
        raise ValueError("Se requiere al menos un movimiento para calcular la financiacion.")

    income_by_period: Dict[int, float] = {}
    cost_by_period: Dict[int, float] = {}

    for movement in normalized:
        target = income_by_period if movement.concepto == "ingresos" else cost_by_period
        target[movement.periodo] = target.get(movement.periodo, 0.0) + movement.valor

    if not income_by_period:
        raise ValueError("No se encontraron ingresos en los movimientos proporcionados.")

    last_movement_period = max(max(income_by_period), max(cost_by_period or {1}))
    last_income_period = max(income_by_period)

    # Extend the timeline by one additional period to allow paying the final interest.
    timeline_end = max(last_movement_period, credit_end_period, last_income_period + 1)

    credit_remaining = credit_limit
    outstanding_principal = 0.0
    interest_to_pay = 0.0  # Interest due in the current period (generated previously).

    disbursements: List[Dict[str, float]] = []
    contributions: List[Dict[str, float]] = []

    repayment_periods = [p for p in (last_income_period - 1, last_income_period) if p >= 1]

    for period in range(1, timeline_end + 1):
        incomes = income_by_period.get(period, 0.0)
        costs = cost_by_period.get(period, 0.0)
        fco = incomes - costs

        credit_draw = 0.0
        if credit_start_period <= period <= credit_end_period:
            cash_need = max(0.0, -fco)
            if cash_need > 0 and credit_remaining > 0:
                available_draw = min(cash_need, credit_remaining, monthly_draw_cap)
                credit_draw = available_draw
                credit_remaining -= credit_draw
                outstanding_principal += credit_draw
                disbursements.append({"periodo": period, "valor": round(credit_draw, 2)})

        interest_payment = 0.0
        if interest_to_pay > 0:
            interest_payment = interest_to_pay

        principal_payment = 0.0
        if outstanding_principal > 0 and period in repayment_periods:
            periods_left = len([p for p in repayment_periods if p >= period])
            principal_payment = round(outstanding_principal / periods_left, 2)
            outstanding_principal -= principal_payment
            if outstanding_principal < 0:
                outstanding_principal = 0.0

        net_cash_before_contribution = fco + credit_draw - interest_payment - principal_payment
        contribution = 0.0
        if net_cash_before_contribution < 0:
            contribution = round(-net_cash_before_contribution, 2)
            contributions.append({"periodo": period, "valor": contribution})
            net_cash_before_contribution = 0.0

        # Generate interest for the next period based on the remaining outstanding balance.
        interest_to_pay = round(outstanding_principal * monthly_interest_rate, 2)

    return disbursements, contributions


__all__ = ["calculate_financing_plan"]
