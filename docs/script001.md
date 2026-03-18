# Script de Análisis de Pull Requests con Sharding

Documentación completa del script `script001.py` - Analizador de Pull Requests en organizaciones GitHub con soporte para procesamiento distribuido mediante sharding.

## Tabla de Contenidos

- [Descripción General](#descripción-general)
- [Tutorial: Primer Uso](#tutorial-primer-uso)
- [Guía Práctica: Casos de Uso](#guía-práctica-casos-de-uso)
- [Referencia Técnica](#referencia-técnica)
- [Explicación: Conceptos Clave](#explicación-conceptos-clave)

---

## Descripción General

Este script analiza el flujo de commits a través de Pull Requests en múltiples ramas de repositorios GitHub, siguiendo el patrón de deployment:

````
feature branch → develop → qa → main
````

**Problema que resuelve:** Rastrear el ciclo de vida completo de commits desde su creación hasta producción, identificando PRs intermedios y fechas de merge en cada etapa.

**Capacidades principales:**
- Filtrado de repositorios por topics
- Sharding para procesamiento paralelo de grandes organizaciones
- Manejo automático de rate limits de la API de GitHub
- Exportación a CSV para análisis posterior

---

## Tutorial: Primer Uso

### Prerequisitos

1. **Python 3.6+** instalado
2. **Token de GitHub** con permisos:
   - `repo` (acceso a repositorios)
   - `read:org` (lectura de organizaciones)

### Paso 1: Instalar Dependencias

````bash
pip install requests pandas
````

### Paso 2: Configurar el Script

Abre `script/script001.py` y modifica las siguientes variables:

````python
# Línea 6: Organización objetivo
ORG = "TU-ORGANIZACION"

# Línea 7: Topic para filtrar repositorios
TOPIC = "tu-topic"

# Línea 10-11: Configuración de sharding
SHARDS = 20          # Total de shards
SHARD_ID = 1         # ID del shard actual (1 a 20)

# Línea 15: Token de autenticación
TOKEN = "ghp_TuTokenAqui123456789"
````

### Paso 3: Ejecutar

````bash
python script/script001.py
````

### Paso 4: Verificar Resultados

El script generará un archivo CSV:

````
prs_merged_main_shard_1_of_20_PBI_110326.csv
````

Con columnas:
- `repo_name` - Nombre del repositorio
- `commit_sha` - Hash del commit
- `commit_date` - Fecha de creación
- `pr_id` - PR a develop
- `merged_at` - Fecha de merge a develop
- `source_branch` - Rama origen
- `pr_dev_qa_id` - PR de develop → qa
- `merge_to_qa_date` - Fecha de merge a qa
- `pr_qa_main_id` - PR de qa → main
- `merge_to_main_date` - Fecha de merge a main

---

## Guía Práctica: Casos de Uso

### Procesar Organización Completa con Múltiples Instancias

Para organizaciones grandes, divide el trabajo en múltiples ejecuciones paralelas:

````bash
# Terminal 1
SHARD_ID=1 python script/script001.py

# Terminal 2
SHARD_ID=2 python script/script001.py

# Terminal 3
SHARD_ID=3 python script/script001.py
````

### Cambiar Número de Shards

Para ajustar la división del trabajo:

````python
# Para organizaciones pequeñas (< 50 repos)
SHARDS = 5
SHARD_ID = 1

# Para organizaciones medianas (50-200 repos)
SHARDS = 10
SHARD_ID = 1

# Para organizaciones grandes (200+ repos)
SHARDS = 20
SHARD_ID = 1
````

### Filtrar por Topic Diferente

````python
# Ejemplo: Filtrar por equipo
TOPIC = "team-backend"

# Ejemplo: Filtrar por proyecto
TOPIC = "project-alpha"
````

### Consolidar Resultados de Múltiples Shards

````python
import pandas as pd
import glob

# Leer todos los archivos CSV
files = glob.glob("prs_merged_main_shard_*_of_20_*.csv")
dfs = [pd.read_csv(f) for f in files]

# Consolidar
consolidated = pd.concat(dfs, ignore_index=True)

# Guardar resultado consolidado
consolidated.to_csv("prs_merged_consolidated.csv", index=False)
````

---

## Referencia Técnica

### Variables de Configuración

| Variable | Tipo | Descripción | Valor por Defecto |
|----------|------|-------------|-------------------|
| `ORG` | `str` | Nombre de la organización GitHub | `"CCAPITAL-APPS"` |
| `TOPIC` | `str` | Topic para filtrar repositorios | `"tribu-canal-digital"` |
| `SHARDS` | `int` | Número total de shards | `20` |
| `SHARD_ID` | `int` | ID del shard actual (1 a SHARDS) | `1` |
| `OUT_FILE` | `str` | Nombre del archivo de salida | Auto-generado |
| `TOKEN` | `str` | Token de autenticación GitHub | `"token_github"` |
| `HEADERS` | `dict` | Headers HTTP con autenticación | Auto-generado |

### Funciones Principales

#### `get(url)`

Realiza peticiones GET con manejo de rate limits.

**Parámetros:**
- `url` (str): URL de la API de GitHub

**Retorna:**
- `dict | None`: JSON parseado o None en caso de error

**Comportamiento:**
- Detecta límite de rate (HTTP 403)
- Espera automáticamente hasta reset del límite
- Reintenta la petición después de la espera

**Ejemplo:**

````python
response = get("https://api.github.com/orgs/myorg/repos")
if response:
    repos = response
````

#### `get_repos_by_topic(org, topic)`

Obtiene repositorios de una organización filtrados por topic.

**Parámetros:**
- `org` (str): Nombre de la organización
- `topic` (str): Topic para filtrar

**Retorna:**
- `list[dict]`: Lista de repositorios que contienen el topic

**Paginación:**
- 100 repositorios por página
- Itera automáticamente todas las páginas

**Ejemplo:**

````python
repos = get_repos_by_topic("myorg", "backend")
print(f"Encontrados {len(repos)} repositorios")
````

#### `get_all_prs(repo_owner, repo_name, base_branch, head_branch)`

Obtiene Pull Requests cerrados entre ramas.

**Parámetros:**
- `repo_owner` (str): Propietario del repositorio
- `repo_name` (str): Nombre del repositorio
- `base_branch` (str): Rama destino del PR
- `head_branch` (str): Rama origen del PR (vacío para todos)

**Retorna:**
- `list[dict]`: Lista de Pull Requests

**Filtros aplicados:**
- Estado: `closed` (incluye merged)
- Base: rama destino especificada
- Head: rama origen especificada (opcional)

**Ejemplo:**

````python
# PRs de develop a qa
prs = get_all_prs("myorg", "myrepo", "qa", "develop")

# Todos los PRs a develop
prs = get_all_prs("myorg", "myrepo", "develop", "")
````

#### `get_commits_from_pull(pr_number, repo_owner, repo_name)`

Obtiene commits de un Pull Request específico.

**Parámetros:**
- `pr_number` (int): Número del PR
- `repo_owner` (str): Propietario del repositorio
- `repo_name` (str): Nombre del repositorio

**Retorna:**
- `list[dict]`: Lista de commits del PR

**Ejemplo:**

````python
commits = get_commits_from_pull(42, "myorg", "myrepo")
for commit in commits:
    print(commit['sha'], commit['commit']['message'])
````

### Estructura de Datos de Salida

Cada fila del CSV representa un commit y contiene:

````python
{
    "repo_name": str,           # Nombre del repositorio
    "commit_sha": str,          # Hash SHA del commit
    "commit_date": str,         # Fecha ISO 8601
    "pr_id": int,               # PR a develop
    "merged_at": str | None,    # Fecha merge a develop
    "source_branch": str,       # Rama feature origen
    "pr_dev_qa_id": int | None, # PR develop → qa
    "merge_to_qa_date": str | None,    # Fecha merge a qa
    "pr_qa_main_id": int | None,       # PR qa → main
    "merge_to_main_date": str | None   # Fecha merge a main
}
````

### Endpoints de API Utilizados

| Endpoint | Propósito | Límite |
|----------|-----------|--------|
| `GET /orgs/{org}/repos` | Listar repositorios | 100/página |
| `GET /repos/{owner}/{repo}/pulls` | Listar PRs | 100/página |
| `GET /repos/{owner}/{repo}/pulls/{number}/commits` | Commits de PR | 250/PR |

**Rate Limits:**
- Autenticado: 5000 requests/hora
- No autenticado: 60 requests/hora

---

## Explicación: Conceptos Clave

### ¿Por Qué Sharding?

Las organizaciones grandes pueden tener cientos de repositorios. Procesar todos secuencialmente puede tomar horas o días. El sharding permite:

1. **Paralelización**: Múltiples instancias procesan diferentes segmentos
2. **Tolerancia a fallos**: Si un shard falla, los demás continúan
3. **Escalabilidad**: Añade más shards según necesidad

**Cómo funciona:**

````python
total_repos = 100
SHARDS = 20          # Dividir en 20 partes
repos_per_shard = 5  # 100 / 20 = 5 repos por shard

# Shard 1 procesa repos 0-4
# Shard 2 procesa repos 5-9
# ...
# Shard 20 procesa repos 95-99
````

### Flujo de Commits en Git Flow

El script asume un flujo de trabajo estándar:

````
1. Desarrollador crea feature branch desde develop
2. Abre PR: feature → develop
3. Merge a develop
4. PR automático/manual: develop → qa (testing)
5. Merge a qa
6. PR automático/manual: qa → main (producción)
7. Merge a main
````

**Por qué rastrear esto:**
- Auditoría de cambios en producción
- Métricas de lead time (desarrollo → producción)
- Identificar commits atascados en qa
- Reportes de compliance

### Rate Limiting en GitHub API

GitHub limita el número de requests por hora. El script maneja esto:

1. **Detección**: Lee headers `X-RateLimit-Remaining` y `X-RateLimit-Reset`
2. **Espera**: Pausa ejecución hasta reset del límite
3. **Reintento**: Automáticamente reintenta después de espera

**Ejemplo de salida:**

````
Límite de tasa alcanzado. Esperando hasta 2026-03-18 14:30:00...
[Pausa de ~30 minutos]
Continuando...
````

**Mejores prácticas:**
- Usa token autenticado (5000 vs 60 requests/hora)
- Ejecuta en horas de baja actividad
- Monitorea logs para estimar tiempo total

### Topics en GitHub

Los topics son etiquetas que categorizan repositorios:

````
Ejemplo: repositorio con topics ["python", "api", "backend", "team-alpha"]
````

**Ventajas de filtrar por topic:**
- Procesar solo repos relevantes
- Agrupar por equipo, proyecto o tecnología
- Reducir tiempo de procesamiento

**Configuración de topics:**
- Se asignan en GitHub UI: Repo → About → Topics
- Máximo 20 topics por repositorio
- Case-insensitive

### Estructura del DataFrame Resultante

El script construye gradualmente información de cada commit:

**Fase 1 - PRs a develop:**
````python
# Información inicial
commit → pr_id, merged_at, source_branch
````

**Fase 2 - PRs develop → qa:**
````python
# Añade información de qa
commit → pr_dev_qa_id, merge_to_qa_date
````

**Fase 3 - PRs qa → main:**
````python
# Añade información de producción
commit → pr_qa_main_id, merge_to_main_date
````

**Resultado final:**
- Vista completa del ciclo de vida del commit
- Permite calcular métricas como cycle time, deployment frequency
- Identifica commits que no llegaron a producción

---

## Limitaciones Conocidas

1. **Solo soporta flujo de 3 ramas** (develop, qa, main)
2. **No detecta cherry-picks**: Commits aplicados manualmente
3. **Asume nombres de rama estándar**: No configurable
4. **Sin caché**: Re-procesa todo en cada ejecución
5. **CSV sin compresión**: Archivos grandes para orgs extensas

## Mejoras Futuras

- [ ] Soporte para flujos de rama personalizados
- [ ] Caché de datos de API para re-ejecuciones
- [ ] Exportación a múltiples formatos (JSON, Parquet)
- [ ] Dashboard web para visualización
- [ ] Métricas DORA automáticas

## Solución de Problemas

### Error: "401 Unauthorized"

**Causa:** Token inválido o sin permisos

**Solución:**
````python
# Verifica tu token
TOKEN = "ghp_..." # Debe empezar con ghp_

# Verifica permisos en GitHub:
# Settings → Developer settings → Personal access tokens
# Debe tener: repo, read:org
````

### Error: "404 Not Found"

**Causa:** Organización o repositorio no existe o no tienes acceso

**Solución:**
````python
# Verifica el nombre
ORG = "nombre-exacto-org"  # Case-sensitive

# Verifica membresía en la org
````

### Proceso Muy Lento

**Causa:** Muchos repositorios o PRs

**Solución:**
````python
# Aumenta sharding
SHARDS = 50

# O filtra por topic más específico
TOPIC = "specific-team"
````

### DataFrame Vacío

**Causa:** No hay repositorios con el topic especificado

**Solución:**
````python
# Verifica topics disponibles manualmente en GitHub UI
# O ejecuta sin filtro de topic (modificando get_repos_by_topic)
````

---

## Referencias

- [GitHub REST API - Pulls](https://docs.github.com/en/rest/pulls/pulls)
- [GitHub REST API - Rate Limiting](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)
- [GitHub Topics Documentation](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/classifying-your-repository-with-topics)
- [Pandas DataFrame Documentation](https://pandas.pydata.org/docs/reference/api/pandas.DataFrame.html)

---

## Changelog

### v1.0.0 (2024)
- ✨ Implementación inicial
- ✨ Soporte para sharding
- ✨ Manejo de rate limits
- ✨ Exportación a CSV
