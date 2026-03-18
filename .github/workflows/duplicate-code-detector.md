---
name: Duplicate Code Detector
description: Identifica patrones de código duplicado en la base de código y sugiere oportunidades de refactorización
on:
  workflow_dispatch:
permissions:
  contents: read
  issues: read
  pull-requests: read
safe-outputs:
  create-issue:
    expires: 2d
    title-prefix: "[duplicate-code] "
    labels: [code-quality, automated-analysis]
    assignees: copilot
    group: true
    max: 3
timeout-minutes: 60
strict: true
---

# Detección de Código Duplicado

Analiza el código para identificar patrones duplicados usando análisis semántico. Reporta hallazgos significativos que requieran refactorización.

## Idioma Obligatorio de Respuesta

- La respuesta final debe estar sí o sí en español.
- Todos los comentarios, issues, resúmenes y recomendaciones deben escribirse en español.
- Puedes conservar términos técnicos en inglés cuando no exista una traducción precisa.

## Tarea

Detecta y reporta duplicación de código mediante:

1. **Analizar Commits Recientes**: Revisa cambios en los commits más recientes
2. **Detectar Código Duplicado**: Identifica patrones similares o duplicados usando análisis semántico
3. **Reportar Hallazgos**: Crea un issue detallado si se detecta duplicación significativa (umbral: >10 líneas o 3+ patrones similares)

## Contexto

- **Repository**: ${{ github.repository }}
- **Commit ID**: ${{ github.event.head_commit.id }}
- **Triggered by**: @${{ github.actor }}

## Flujo de Análisis

### 1. Análisis de Archivos Modificados

Identifica y analiza archivos modificados:
- Determina los archivos cambiados en commits recientes usando `git log` y `git diff`
- Enfócate en archivos de código fuente (archivos de lenguajes de programación)
- **Excluye archivos de pruebas** del análisis (patrones: `*_test.*`, `*.test.*`, `*.spec.*`, `test_*.*`, o ubicados en directorios `test`, `tests`, `__tests__` o `spec`)
- **Excluye archivos generados** y artefactos de build
- **Excluye archivos de workflows** del análisis (archivos bajo `.github/workflows/*`)
- Usa herramientas de exploración de código para entender la estructura
- Lee el contenido de archivos modificados para examinar cambios

### 2. Detección de Duplicados

Aplica análisis para encontrar duplicados:

**Búsqueda de Patrones**:
- Busca indicadores de duplicación usando grep y búsqueda de código:
  - Firmas de función similares
  - Bloques de lógica repetidos
  - Patrones de nombrado de variables similares
  - Bloques de código casi idénticos
- Busca funciones con nombres similares en distintos archivos
- Identifica similitudes estructurales en la organización del código

**Análisis Semántico**:
- Compara bloques de código por similitud lógica más allá de coincidencias textuales
- Identifica implementaciones distintas de la misma funcionalidad
- Busca patrones de copy-paste con variaciones menores

### 3. Evaluación de Duplicación

Evalúa hallazgos para identificar duplicación real:

**Tipos de Duplicación**:
- **Duplicación Exacta**: Bloques de código idénticos en múltiples ubicaciones
- **Duplicación Estructural**: Misma lógica con variaciones menores (nombres de variables distintos, etc.)
- **Duplicación Funcional**: Implementaciones diferentes de la misma funcionalidad
- **Programación por Copy-Paste**: Bloques similares que podrían extraerse a utilidades compartidas

**Criterios de Evaluación**:
- **Severidad**: Cantidad de código duplicado (líneas y número de ocurrencias)
- **Impacto**: Dónde ocurre la duplicación (rutas críticas, código frecuentemente invocado)
- **Mantenibilidad**: Cómo afecta la duplicación al mantenimiento del código
- **Oportunidad de Refactorización**: Si la duplicación puede refactorizarse fácilmente

### 4. Reporte de Issues

Crea issues separados para cada patrón de duplicación distinto detectado (máximo 3 patrones por ejecución). Cada patrón debe tener su propio issue para permitir una remediación enfocada.

**Cuándo Crear Issues**:
- Crea issues solo si se encuentra duplicación significativa (umbral: >10 líneas duplicadas O 3+ instancias de patrones similares)
- **Crea un issue por cada patrón de duplicación distinto**; NO agrupes múltiples patrones en un solo issue
- Limita el reporte a los 3 patrones más significativos si hay más
- Usa la herramienta `create_issue` de safe-outputs MCP **una vez por cada patrón**

**Contenido del Issue por Cada Patrón**:
- **Resumen Ejecutivo**: Descripción breve de este patrón específico
- **Detalles de Duplicación**: Ubicaciones y bloques de código concretos solo para este patrón
- **Evaluación de Severidad**: Impacto y preocupaciones de mantenibilidad para este patrón
- **Recomendaciones de Refactorización**: Enfoques sugeridos para eliminar este patrón
- **Ejemplos de Código**: Ejemplos concretos con rutas de archivo y números de línea para este patrón

## Alcance de Detección

### Reporta Estos Casos

- Funciones idénticas o casi idénticas en archivos distintos
- Bloques de código repetidos que podrían extraerse a utilidades
- Clases o módulos similares con funcionalidad superpuesta
- Código copy-paste con modificaciones menores
- Lógica de negocio duplicada entre componentes

### Omite Estos Patrones

- Código boilerplate estándar (imports, exports, declaraciones de paquete)
- Código de setup/teardown de pruebas (duplicación aceptable en tests)
- **Todos los archivos de pruebas** (patrones: `*_test.*`, `*.test.*`, `*.spec.*`, `test_*.*`, o en directorios `test/`, `tests/`, `__tests__/`, `spec/`)
- **Todos los archivos de workflows** (archivos bajo `.github/workflows/*`)
- Archivos de configuración con estructura similar
- Patrones específicos del lenguaje (constructores, getters/setters)
- Fragmentos pequeños de código (<5 líneas) salvo que sean muy repetitivos
- Código generado o dependencias vendorizadas

### Profundidad del Análisis

- **Enfoque Primario**: Archivos cambiados en commits recientes (excluyendo tests y workflows)
- **Análisis Secundario**: Verifica duplicación contra el código existente
- **Referencia Cruzada**: Busca patrones a través del repositorio
- **Contexto Histórico**: Considera si la duplicación es nueva o preexistente

## Plantilla de Issue

Para cada patrón de duplicación distinto detectado, crea un issue separado usando esta estructura:

````markdown
# 🔍 Código Duplicado Detectado: [Nombre del Patrón]

*Análisis del commit ${{ github.event.head_commit.id }}*

**Asignado a**: @copilot

## Resumen

[Breve descripción de este patrón específico de duplicación]

## Detalles de Duplicación

### Patrón: [Descripción]
- **Severidad**: Alta/Media/Baja
- **Ocurrencias**: [Número de instancias]
- **Ubicaciones**:
  - `path/to/file1.ext` (lines X-Y)
  - `path/to/file2.ext` (lines A-B)
- **Ejemplo de Código**:
  ````[language]
  [Ejemplo de código duplicado]
  ````

## Análisis de Impacto

- **Mantenibilidad**: [Cómo afecta el mantenimiento del código]
- **Riesgo de Bugs**: [Potencial de correcciones inconsistentes]
- **Crecimiento de Código**: [Impacto en el tamaño de la base de código]

## Recomendaciones de Refactorización

1. **[Recomendación 1]**
   - Extraer funcionalidad común a: `suggested/path/utility.ext`
   - Esfuerzo estimado: [horas/complejidad]
   - Beneficios: [mejoras específicas]

2. **[Recomendación 2]**
   [... recomendaciones adicionales ...]

## Checklist de Implementación

- [ ] Revisar hallazgos de duplicación
- [ ] Priorizar tareas de refactorización
- [ ] Crear plan de refactorización
- [ ] Implementar cambios
- [ ] Actualizar pruebas
- [ ] Verificar que no se rompa funcionalidad

## Metadatos del Análisis

- **Archivos Analizados**: [cantidad]
- **Método de Detección**: Análisis semántico de código
- **Commit**: ${{ github.event.head_commit.id }}
- **Fecha de Análisis**: [timestamp]
````

## Guías Operativas

### Seguridad
- Nunca ejecutes código o comandos no confiables
- Usa solo herramientas de análisis de solo lectura
- No modifiques archivos durante el análisis

### Eficiencia
- Enfócate primero en archivos cambiados recientemente
- Usa análisis semántico para duplicación significativa, no coincidencias superficiales
- Respeta los límites de timeout (equilibra profundidad y tiempo de ejecución)

### Precisión
- Verifica hallazgos antes de reportar
- Distingue entre patrones aceptables y duplicación real
- Considera modismos del lenguaje y buenas prácticas
- Proporciona recomendaciones específicas y accionables

### Creación de Issues
- Crea **un issue por cada patrón de duplicación distinto**; NO agrupes múltiples patrones en un solo issue
- Limita el reporte a los 3 patrones más significativos si hay más
- Crea issues solo cuando la duplicación sea significativa
- Incluye detalle suficiente para que agentes de código entiendan y actúen
- Proporciona ejemplos concretos con rutas de archivo y números de línea
- Sugiere enfoques de refactorización prácticos
- Asigna el issue a @copilot para remediación automatizada
- Usa títulos descriptivos que identifiquen claramente el patrón específico (ejemplo: "Código Duplicado: Patrón de Manejo de Errores en Módulo Parser")

**Objetivo**: Mejorar la calidad del código identificando y reportando duplicación significativa que impacte la mantenibilidad. Enfócate en hallazgos accionables que habiliten refactorización automatizada o manual.