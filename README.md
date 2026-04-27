# Monitoreo de Transacciones y Riesgo de Fraude

Solución integral para monitoreo de fraude transaccional basada en **PaySim**, con:

- análisis exploratorio y reglas de riesgo;
- modelo supervisado listo para inferencia;
- API en **FastAPI** para scoring individual y por lotes;
- dashboard en **Streamlit** orientado a contexto bancario y decisiones operativas.

## Problema de negocio

En un entorno financiero, el desafío no es solo detectar fraude, sino hacerlo con suficiente anticipación para priorizar revisiones, reducir falsas alertas y apoyar la toma de decisiones del equipo operativo.

Los casos de fraude suelen representar una fracción muy pequeña del total de transacciones, por lo que una métrica global como accuracy no basta. El sistema debe distinguir señales de riesgo útiles y convertirlas en decisiones accionables: **qué revisar, cuándo y por qué**.

## Solución implementada

El proyecto combina una capa analítica y una capa operativa:

1. **EDA y reglas de riesgo** para entender patrones del fraude.
2. **Modelo de machine learning** entrenado con variables viables en tiempo real.
3. **API FastAPI** que valida entradas y expone inferencia reproducible.
4. **Dashboard Streamlit** para explorar métricas, monitorear lotes y simular decisiones.

El foco del sistema no está en mostrar un modelo aislado, sino en representar un flujo completo de monitoreo de fraude orientado a negocio.

## Dataset

Se utiliza **PaySim**, un dataset sintético que emula transacciones financieras móviles y permite estudiar escenarios típicos de fraude como transferencias riesgosas, retiros sospechosos y vaciamiento de cuentas.

## Arquitectura del sistema

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

- **Precisión:** `1.000`
- **Recall:** `0.875`
- **F1 Score:** `0.933`
- **PR AUC:** `0.880`

Interpretación de negocio:

- la precisión perfecta indica que las alertas emitidas por el modelo son altamente confiables;
- el recall muestra que la mayor parte de los fraudes críticos es detectada;
- el equilibrio entre ambas métricas permite priorizar revisiones sin saturar la operación con ruido innecesario.

## Estructura del repositorio

```text
.
├── app.py                          # Punto de entrada raíz para Streamlit
├── artifacts/                      # Pipeline, metadata y archivos exportados
├── dashboard/                      # Interfaz de monitoreo y análisis
│   ├── app.py
│   ├── components/
│   ├── powerbi_data/
│   ├── services/
│   └── views/
├── data/
│   ├── processed/
│   └── raw/
├── docs/
│   └── capturas/                   # Espacio reservado para screenshots del dashboard
├── notebooks/                      # EDA, análisis de riesgo y modelado
├── src/
│   ├── analysis/
│   ├── api/
│   ├── data/
│   ├── features/
│   ├── utils/
│   └── visualization/
├── docker/
│   ├── Dockerfile.api
│   ├── Dockerfile.dashboard
│   └── docker-compose.yml
├── requirements.txt
└── README.md
```

## Endpoints principales de la API

### `GET /health`

Verifica que la API y el pipeline estén disponibles.

### `GET /model/info`

Expone nombre del modelo, features esperadas, threshold y métricas registradas.

### `POST /predict`

Calcula la probabilidad de fraude para una transacción individual.

### `POST /predict/batch`

Procesa un lote de transacciones en una sola llamada.

### `GET /monitoring/powerbi`

Entrega el dataset plano de monitoreo para integración con Power BI.

## Ejecución local

### 1. Crear entorno virtual

```bash
python -m venv .venv
```

### 2. Activar entorno

#### PowerShell

```powershell
.venv\Scripts\Activate.ps1
```

#### CMD

```cmd
.venv\Scripts\activate.bat
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Levantar la API

```bash
uvicorn src.api.main:app --reload
```

Disponible en:

- `http://127.0.0.1:8000`
- `http://127.0.0.1:8000/docs`
- `http://127.0.0.1:8000/redoc`

### 5. Levantar el dashboard

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

Servicios disponibles:

- API: `http://localhost:8000`
- Dashboard: `http://localhost:8501`

### Configuración de comunicación entre servicios

El dashboard usa la variable de entorno `API_BASE_URL`. En `docker-compose.yml` se configura automáticamente como:

```text
http://api:8000
```

## Limitaciones conocidas

- La **API de inferencia** y el **dashboard** funcionan en entorno local y en Docker para predicción, monitoreo y visualización.
- La automatización experimental de **Power BI Desktop** disponible desde el dashboard depende de un entorno **Windows** con **Power BI Desktop** y **PowerShell** instalados.
- Esa automatización no está pensada para ejecutarse dentro de contenedores Docker ni en sistemas sin interfaz de escritorio compatible.
- En esos casos, el sistema sigue funcionando con normalidad para scoring y monitoreo; simplemente se desactiva la automatización de Power BI.

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

Esta solución muestra cómo convertir datos transaccionales en una herramienta de apoyo operativo para fraude. El valor no está solo en predecir, sino en **priorizar casos críticos, reducir alertas innecesarias y hacer más eficiente la revisión de transacciones en un contexto cercano al real**.
