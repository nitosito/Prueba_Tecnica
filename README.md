# Sistema de Planificación Financiera - Gerpro

Sistema de gestión y planificación financiera para proyectos inmobiliarios desarrollado con Django. Permite calcular desembolsos de crédito constructor y aportes de capital necesarios para mantener un flujo de caja positivo.

## 📋 Descripción

Este proyecto implementa una solución para la planificación financiera de proyectos inmobiliarios con múltiples sub-etapas (torres). El sistema:

- **Calcula automáticamente** los desembolsos de crédito y aportes de capital necesarios
- **Gestiona flujos de caja** mensuales (ingresos y costos) por sub-etapa
- **Controla límites de crédito** y tasas de desembolso mensuales
- **Aplica tasas de interés** sobre saldos de crédito pendientes
- **Persiste datos** en base de datos SQLite con modelos Django

## 🏗️ Arquitectura del Proyecto

```
Prueba Tecnica/
├── config/                 # Configuración principal de Django
│   ├── settings.py        # Configuración del proyecto
│   ├── urls.py           # URLs principales
│   └── wsgi.py           # Entry point WSGI
├── finance/               # Aplicación principal de finanzas
│   ├── models.py         # Modelos de datos (Project, SubStage, CashFlowEntry, etc.)
│   ├── views.py          # Vistas web
│   ├── forms.py          # Formularios
│   ├── services.py       # Lógica de negocio y persistencia
│   ├── urls.py           # URLs de la app
│   ├── admin.py          # Configuración del admin de Django
│   ├── management/       # Comandos personalizados de Django
│   │   └── commands/
│   │       └── calculate_financing.py
│   ├── migrations/       # Migraciones de base de datos
│   └── tests/           # Tests unitarios
│       └── test_financing.py
├── templates/            # Templates HTML
│   ├── base.html
│   └── finance/
│       └── plan_form.html
├── financing.py          # Algoritmo core de cálculo financiero
├── Prueba_logica.py      # CLI interactivo para pruebas
├── datos_gerpro_prueba.json  # Datos de ejemplo
├── db.sqlite3           # Base de datos SQLite
└── manage.py            # Utilidad de gestión de Django
