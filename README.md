# Monitoreo de Transacciones y Riesgo de Fraude

![Python](https://img.shields.io/badge/Python-3.x-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-API-009688?style=flat-square&logo=fastapi&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-Dashboard-FF4B4B?style=flat-square&logo=streamlit&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-Contenedores-2496ED?style=flat-square&logo=docker&logoColor=white)

Detector automático de fraude transaccional basado en **PaySim**, con visualización y proyección operativa de datos mediante un dashboard de escritorio orientado a contexto bancario.

La solución integra:

- análisis exploratorio y reglas de riesgo;
- modelo supervisado listo para inferencia;
- API en **FastAPI** para scoring individual y por lotes;
- dashboard en **Streamlit** orientado a contexto bancario, monitoreo operativo y lectura ejecutiva.

En términos simples, este proyecto parte de un problema real: **cómo detectar transacciones sospechosas sin saturar la operación con alertas innecesarias**. A partir de ese contexto, combina análisis, reglas operativas, modelo predictivo, API y dashboard para traducir datos transaccionales en decisiones accionables. No busca solo predecir fraude, sino **apoyar revisiones, priorizar casos críticos y simular un flujo de monitoreo cercano a un entorno bancario real**.

## Problema de negocio

En un entorno financiero, el desafío no es solo detectar fraude, sino hacerlo con suficiente anticipación para **priorizar revisiones, reducir falsas alertas y apoyar la toma de decisiones del equipo operativo**.

Los casos de fraude suelen representar una **fracción muy pequeña** del total de transacciones. Por eso, una métrica global como accuracy no basta para evaluar si un sistema realmente aporta valor.

El reto real consiste en distinguir **señales de riesgo útiles** y convertirlas en decisiones accionables: **qué revisar, cuándo y por qué**.

## Solución implementada

El proyecto combina una capa analítica y una capa operativa para detectar fraude, exponer predicciones y traducirlas en una vista de escritorio útil para seguimiento y toma de decisiones:

1. 🔎 **EDA y reglas de riesgo** para entender cómo se comporta el fraude en los datos.
2. 🤖 **Modelo de machine learning** entrenado con variables viables en tiempo real.
3. ⚙️ **API en FastAPI** que valida entradas y expone inferencia reproducible.
4. 📊 **Dashboard en Streamlit** para explorar métricas, monitorear lotes y simular decisiones.

El foco del sistema no está en mostrar un modelo aislado, sino en representar un flujo completo de monitoreo de fraude orientado a negocio.

## Dataset

Se utiliza **PaySim**, un dataset sintético que emula transacciones financieras móviles y permite estudiar escenarios típicos de fraude como transferencias riesgosas, retiros sospechosos y vaciamiento de cuentas.

## 🧠 Enfoque del proyecto

Este proyecto **no se plantea solo como un modelo de clasificación**, sino como una herramienta de apoyo operativo para monitoreo de fraude.

La solución busca **priorizar decisiones**, traduciendo patrones analíticos en alertas comprensibles y útiles para revisión. En ese sentido, el dashboard, la API y la lógica de riesgo trabajan juntos para simular un **contexto bancario real**, donde importa tanto detectar como decidir con criterio operativo.

## Arquitectura del sistema

### Flujo principal

```text
EDA → reglas operativas → modelo → API → dashboard
```

### Flujo resumido

1. Los notebooks preparan variables y reglas de riesgo.
2. El entrenamiento exporta:
   - `fraude_api_pipeline.joblib`
   - `fraude_api_features.json`
   - `fraude_api_metadata.json`
3. La API carga esos artefactos y expone endpoints de inferencia.
4. El dashboard consume la API y presenta resultados en lenguaje operativo.

## Métricas del modelo desplegado

Según `artifacts/fraude_api_metadata.json`, el modelo operativo registra:

| Métrica | Valor |
|---|---:|
| Precisión | `1.000` |
| Recall | `0.875` |
| F1 Score | `0.933` |
| PR AUC | `0.880` |

### ¿Qué significa esto en negocio?

- **Precisión → confianza:** cuando el modelo genera una alerta, es muy probable que corresponda a un fraude real.
- **Recall → cobertura:** el sistema logra capturar la mayor parte de los eventos críticos.
- **Balance → operación:** el equilibrio entre precisión y recall permite revisar más inteligentemente sin saturar al equipo con ruido innecesario.

## 💼 Valor para negocio

- Reduce carga operativa al priorizar revisiones sobre transacciones con mayor probabilidad de fraude.
- Mejora el foco del análisis al concentrar la atención en casos realmente críticos.
- Evita falsas alertas innecesarias, favoreciendo una operación más eficiente y sostenible.

## Estructura del repositorio

```text
.
├── app.py                          # ▶️ Punto de entrada raíz para Streamlit
├── artifacts/                      # 📦 Pipeline, metadata y archivos exportados
├── dashboard/                      # 📊 Interfaz de monitoreo y análisis
│   ├── app.py
│   ├── components/
│   ├── powerbi_data/
│   ├── services/
│   └── views/
├── data/                           # 🗂️ Estructura de datos del proyecto
│   ├── processed/
│   └── raw/
├── docs/                           # 🖼️ Recursos de apoyo y capturas
│   └── capturas/                   # Espacio reservado para screenshots del dashboard
├── notebooks/                      # 📓 EDA, análisis de riesgo y modelado
├── src/                            # 🧠 Código fuente principal
│   ├── analysis/
│   ├── api/
│   ├── data/
│   ├── features/
│   ├── utils/
│   └── visualization/
├── docker/                         # 🐳 Archivos de contenedorización
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   └── docker-compose.yml
├── requirements.txt                # 📌 Dependencias del proyecto
└── README.md                       # 📘 Documentación principal
```

## Endpoints principales de la API

### `GET /health`

Verifica que la API esté disponible y que el pipeline de inferencia pueda cargarse correctamente.

### `GET /model/info`

Expone información del modelo desplegado, incluyendo nombre, features esperadas, threshold operativo y métricas registradas.

### `POST /predict`

Calcula la probabilidad de fraude para una transacción individual y devuelve su evaluación de riesgo.

### `POST /predict/batch`

Procesa un lote de transacciones en una sola llamada, útil para simulaciones o monitoreo por volumen.

### `GET /monitoring/powerbi`

Entrega el dataset plano de monitoreo para integración con Power BI y análisis complementario en entorno de escritorio.

## Ejecución local

### Guía rápida

#### 1. Crear entorno virtual

```bash
python -m venv .venv
```

#### 2. Activar entorno

**PowerShell**

```powershell
.venv\Scripts\Activate.ps1
```

**CMD**

```cmd
.venv\Scripts\activate.bat
```

#### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

#### 4. Levantar la API

```bash
uvicorn src.api.main:app --reload
```

Disponible en:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

#### 5. Levantar el dashboard

Desde la raíz del proyecto:

```bash
streamlit run app.py
```

Disponible en:

- `http://127.0.0.1:8501`

## Ejecución con Docker

### Levantar API y dashboard

```bash
docker compose -f docker/docker-compose.yml up --build
```

### Servicios disponibles

- **API:** `http://localhost:8000`
- **Dashboard:** `http://localhost:8501`

### Configuración de comunicación entre servicios

El dashboard utiliza la variable de entorno `API_BASE_URL`. En `docker-compose.yml` se configura automáticamente como:

```text
http://api:8000
```

## Limitaciones conocidas

- La **API de inferencia** y el **dashboard** funcionan en entorno local y en Docker para predicción, monitoreo y visualización.
- La automatización experimental de **Power BI Desktop** depende de un entorno **Windows** con **Power BI Desktop** y **PowerShell** instalados.
- Esa automatización **no está pensada para ejecutarse dentro de contenedores Docker** ni en sistemas sin interfaz de escritorio compatible.
- En esos casos, el sistema sigue funcionando con normalidad para scoring y monitoreo; simplemente **se desactiva la automatización de Power BI**.

## Capturas del dashboard

El repositorio deja preparado el directorio `docs/capturas/` para incluir imágenes del dashboard al publicar en GitHub. Sugerencias de capturas:

- `docs/capturas/contexto.png`
- `docs/capturas/analisis.png`
- `docs/capturas/modelo.png`
- `docs/capturas/simulacion.png`

## Compatibilidad y reproducibilidad

El proyecto está preparado para ejecutarse tanto en entorno local como en contenedores Docker, manteniendo:

- API y dashboard desacoplados;
- artefactos serializados reutilizables;
- validación de payloads alineada con las features exportadas;
- una ruta clara desde análisis hasta operación.

## Conclusión

Esta solución muestra cómo convertir datos transaccionales en una herramienta de apoyo operativo para fraude. Su valor no está solo en predecir, sino en **priorizar casos críticos, reducir alertas innecesarias y hacer más eficiente la revisión de transacciones en un contexto cercano al real**.

Como proyecto de portafolio, refleja una propuesta completa: análisis, reglas, modelo, API y dashboard trabajando de forma integrada para representar un caso de uso de negocio claro, profesional y aplicable.
