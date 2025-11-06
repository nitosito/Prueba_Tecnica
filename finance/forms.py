from __future__ import annotations

from django import forms


class FinancingPlanForm(forms.Form):
    project_name = forms.CharField(label="Nombre del proyecto", max_length=120)
    project_slug = forms.SlugField(label="Slug del proyecto", max_length=150)
    credit_limit = forms.FloatField(label="Cupo del crédito", min_value=0.01)
    max_monthly_draw = forms.FloatField(
        label="Porcentaje máximo de desembolso mensual",
        min_value=0.0,
        max_value=1.0,
        help_text="Expresado como fracción (ej. 0.08).",
    )
    credit_start = forms.IntegerField(label="Periodo inicial de crédito", min_value=1)
    credit_end = forms.IntegerField(label="Periodo final de crédito", min_value=1)
    annual_rate = forms.FloatField(label="Tasa de interés anual", min_value=0.0, max_value=1.0)
    movements_file = forms.FileField(
        label="Archivo JSON de movimientos",
        help_text="Debe coincidir con la estructura definida en la prueba.",
    )

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get("credit_start")
        end = cleaned.get("credit_end")
        if start and end and end < start:
            self.add_error("credit_end", "El periodo final debe ser mayor o igual al inicial.")
        return cleaned

