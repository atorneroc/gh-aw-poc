# gh-aw-poc

Repositorio de prueba de concepto para GitHub Agentic Workflows.

## Descripción

Este repositorio contiene scripts y herramientas para análisis de Pull Requests en organizaciones de GitHub, con enfoque en flujos de trabajo de deployment entre ramas (`develop` → `qa` → `main`).

## Contenido

### Scripts

- **[script001.py](./script/script001.py)** - Analizador de PRs con sharding para organizaciones GitHub

## Documentación

La documentación detallada está disponible en el directorio [`docs/`](./docs/):

- [Guía del Script de Análisis de PRs](./docs/script001.md) - Tutorial y referencia técnica

## Inicio Rápido

````bash
# Instalar dependencias
pip install requests pandas

# Configurar token de GitHub
export GITHUB_TOKEN="tu_token_aqui"

# Ejecutar script de análisis
python script/script001.py
````

## Requisitos

- Python 3.6+
- Token de GitHub con permisos de lectura para organizaciones y repositorios

## Estructura del Proyecto

````
.
├── script/          # Scripts de análisis
│   └── script001.py # Analizador de PRs con sharding
├── docs/            # Documentación técnica
└── README.md        # Este archivo
````

## Contribuir

Este es un repositorio de prueba de concepto. Para sugerencias o mejoras, abre un issue.

## Licencia

Repositorio de prueba interno.
