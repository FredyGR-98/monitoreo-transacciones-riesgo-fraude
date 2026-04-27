"""Vista de monitoreo antifraude conectada a FastAPI."""

from __future__ import annotations

import json
from pathlib import Path
import platform
import shutil
import subprocess
from typing import Any

import pandas as pd
import streamlit as st

try:
    from dashboard.components.ui import (
        render_metric_card,
        render_section_header,
        render_subsection_header,
        render_text_block,
        section_card,
    )
    from dashboard.services.api_client import ApiClientError
    from dashboard.services.monitoring import (
        ACTION_OPTIONS,
        REQUIRED_FILE_FIELDS,
        SUPPORTED_FILE_COLUMNS,
        build_results_dataframe,
        build_transactions_from_records,
        generate_transaction_batch,
        persist_monitoring_history,
        score_transactions_with_api,
        summarize_monitoring,
        validate_uploaded_columns,
    )
    from dashboard.services.story_data import get_overview_metrics
except ModuleNotFoundError:  # pragma: no cover - fallback para streamlit desde dashboard/
    from components.ui import (
        render_metric_card,
        render_section_header,
        render_subsection_header,
        render_text_block,
        section_card,
    )
    from services.api_client import ApiClientError
    from services.monitoring import (
        ACTION_OPTIONS,
        REQUIRED_FILE_FIELDS,
        SUPPORTED_FILE_COLUMNS,
        build_results_dataframe,
        build_transactions_from_records,
        generate_transaction_batch,
        persist_monitoring_history,
        score_transactions_with_api,
        summarize_monitoring,
        validate_uploaded_columns,
    )
    from services.story_data import get_overview_metrics


DEFAULT_BATCH_SIZE = 150
DEFAULT_SUSPICIOUS_RATE = 0.30
RISK_FILTER_OPTIONS = ["Todos", "Alto", "Medio", "Bajo"]
TYPE_FILTER_OPTIONS = ["Todos", "TRANSFER", "CASH_OUT", "PAYMENT"]
POWER_BI_REPORT_DIR = Path(__file__).resolve().parents[1]


def render(api_client) -> None:
    """Renderiza el panel de monitoreo antifraude con origen simulado o archivo."""
    overview = get_overview_metrics()
    _initialize_state()

    render_section_header(
        "Monitoreo de transacciones",
        (
            "La misma cola de monitoreo puede alimentarse con datos simulados o con "
            "un archivo cargado por el usuario. En ambos casos se construye el mismo "
            "payload, se consulta el mismo endpoint /predict y se priorizan alertas "
            "de forma uniforme."
        ),
        eyebrow="Operacion antifraude",
    )

    _render_monitoring_panel(api_client, overview)


def _render_monitoring_panel(api_client, overview: dict[str, Any]) -> None:
    """Renderiza el modo principal de monitoreo de transacciones."""
    uploaded_file = None

    with section_card():
        render_subsection_header("Panel de control")
        render_text_block(
            "Selecciona el origen del lote. El motor de monitoreo es el mismo; solo "
            "cambia la fuente de datos que alimenta la cola."
        )

        source_mode = st.radio(
            "Origen del lote",
            options=["Simulado", "Archivo"],
            key="monitor_source_mode",
            horizontal=True,
        )

        if source_mode == "Simulado":
            control_cols = st.columns([1, 1, 1.2])
            with control_cols[0]:
                batch_size = st.slider(
                    "Transacciones por lote",
                    min_value=5,
                    max_value=150,
                    value=st.session_state.monitor_batch_size,
                    key="monitor_batch_size_slider",
                )
            with control_cols[1]:
                suspicious_rate = st.slider(
                    "Probabilidad de caso sospechoso",
                    min_value=0.05,
                    max_value=0.50,
                    value=st.session_state.monitor_suspicious_rate,
                    step=0.05,
                    key="monitor_suspicious_rate_slider",
                )
            with control_cols[2]:
                st.markdown("##### Flujo")
                st.caption(
                    "La simulacion mezcla tipologias como vaciamiento, cash-out inusual, "
                    "partner externo, monto redondo y actividad nocturna."
                )

            st.session_state.monitor_batch_size = batch_size
            st.session_state.monitor_suspicious_rate = suspicious_rate
            button_label = "Generar y monitorear lote simulado"
        else:
            uploaded_file = st.file_uploader(
                "Cargar archivo de transacciones",
                type=["csv", "xlsx", "xls"],
                key="monitor_uploaded_file",
                help=(
                    "Acepta CSV o Excel con el layout operativo definido para monitoreo."
                ),
            )
            st.caption(_build_file_help_text())
            button_label = "Procesar archivo y monitorear"

        execute_clicked = st.button(
            button_label,
            type="primary",
            use_container_width=True,
        )

    if execute_clicked:
        _run_monitoring(api_client, overview, source_mode, uploaded_file)

    _render_input_preview()

    if not st.session_state.monitor_transactions:
        with section_card():
            st.info(
                "Genera un lote simulado o carga un archivo para comenzar el monitoreo. "
                "La API debe estar activa para evaluar las transacciones."
            )
        return

    summary = summarize_monitoring(st.session_state.monitor_transactions)
    _render_summary_panel(summary)
    _render_storage_actions()
    filtered_transactions = _apply_monitoring_filters(st.session_state.monitor_transactions)
    _render_monitoring_table(filtered_transactions)
    _render_analyst_console(filtered_transactions)


def _render_input_preview() -> None:
    """Muestra los datos originales antes del scoring."""
    preview = st.session_state.monitor_input_preview
    if preview is None or preview.empty:
        return

    with section_card():
        render_subsection_header("Datos de entrada")
        st.caption(
            f"Origen actual: {st.session_state.monitor_source}. "
            "La vista previa muestra los datos antes del scoring."
        )
        with st.expander("Ver datos de entrada"):
            st.dataframe(preview.head(100), use_container_width=True, hide_index=True)
            if len(preview) > 100:
                st.caption(
                    f"Se muestran las primeras 100 filas de {len(preview)} registros cargados."
                )


def _render_summary_panel(summary: dict[str, int]) -> None:
    """Renderiza el resumen de alertas del lote actual."""
    render_subsection_header("Panel de resumen")
    metrics = st.columns(5)
    with metrics[0]:
        render_metric_card("Origen", st.session_state.monitor_source, tone="positive")
    with metrics[1]:
        render_metric_card("Transacciones", str(summary["total"]))
    with metrics[2]:
        render_metric_card("Alertas detectadas", str(summary["alerts"]), tone="emphasis")
    with metrics[3]:
        render_metric_card("Riesgo alto", str(summary["high_risk"]), tone="positive")
    with metrics[4]:
        render_metric_card("Riesgo medio", str(summary["medium_risk"]), tone="positive")

    action_metrics = st.columns(2)
    with action_metrics[0]:
        render_metric_card("Marcadas fraude", str(summary["marked"]), tone="positive")
    with action_metrics[1]:
        render_metric_card("Bloqueadas", str(summary["blocked"]), tone="positive")

    with section_card():
        if summary["alerts"] > 0:
            st.warning(
                f"{summary['alerts']} transacciones sospechosas detectadas. "
                "La cola combina score del modelo, senales operativas y contexto del canal."
            )
        else:
            st.success("No se detectaron alertas en el lote actual.")


def _render_storage_actions() -> None:
    """Muestra confirmaciones efimeras para el flujo de Power BI."""
    history_df = st.session_state.monitor_history_dataframe
    message = st.session_state.monitor_save_message

    if history_df is None or history_df.empty:
        return

    if message:
        st.toast(message, icon=":material/check_circle:")
        st.session_state.monitor_save_message = ""


def _resolve_power_bi_report_path() -> Path | None:
    """Encuentra el PBIX del proyecto sin depender de un nombre fijo."""
    report_paths = sorted(POWER_BI_REPORT_DIR.glob("*.pbix"))
    if not report_paths:
        return None
    return report_paths[0]


def _get_power_bi_automation_command() -> list[str] | None:
    """Devuelve el ejecutable disponible para automatizar Power BI en Windows.

    Retorna:
        list[str] | None: Prefijo de comando para PowerShell o `None` si no aplica.
    """
    if platform.system() != "Windows":
        return None

    for candidate in ("powershell.exe", "powershell", "pwsh.exe", "pwsh"):
        executable = shutil.which(candidate)
        if executable:
            return [executable, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command"]

    return None


def _supports_power_bi_automation() -> bool:
    """Indica si el entorno actual puede intentar automatizar Power BI Desktop.

    Retorna:
        bool: `True` si existe un ejecutable compatible de PowerShell en Windows.
    """
    return _get_power_bi_automation_command() is not None


def _run_power_bi_automation(report_path: Path) -> dict[str, Any]:
    """Abre o reactiva Power BI e intenta refrescar el reporte de forma experimental."""
    command_prefix = _get_power_bi_automation_command()
    if command_prefix is None:
        raise RuntimeError(
            "La automatización de Power BI solo está disponible en Windows con "
            "PowerShell y Power BI Desktop instalados."
        )

    escaped_path = str(report_path).replace("'", "''")
    report_title_fragment = report_path.stem.replace("'", "''")
    powershell_script = f"""
$ErrorActionPreference = 'Stop'

Add-Type @"
using System;
using System.Runtime.InteropServices;
public static class Win32 {{
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);

    [DllImport("user32.dll")]
    public static extern bool ShowWindowAsync(IntPtr hWnd, int nCmdShow);
}}
"@

$reportPath = '{escaped_path}'
$reportTitleFragment = '{report_title_fragment}'
$openedNew = $false
$attemptedRefresh = $false

$visibleWindows = Get-Process PBIDesktop -ErrorAction SilentlyContinue |
    Where-Object {{ $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle }} |
    Sort-Object StartTime -Descending

if (-not $visibleWindows) {{
    Start-Process -FilePath $reportPath
    $openedNew = $true
    $deadline = (Get-Date).AddSeconds(30)
    do {{
        Start-Sleep -Milliseconds 1000
        $visibleWindows = Get-Process PBIDesktop -ErrorAction SilentlyContinue |
            Where-Object {{ $_.MainWindowHandle -ne 0 -and $_.MainWindowTitle }} |
            Sort-Object StartTime -Descending
    }} until ($visibleWindows -or (Get-Date) -gt $deadline)
}}

if (-not $visibleWindows) {{
    throw 'No se encontro una ventana visible de Power BI Desktop para automatizar.'
}}

$matchingWindow = $visibleWindows |
    Where-Object {{ $_.MainWindowTitle -like "*$reportTitleFragment*" }} |
    Select-Object -First 1

$target = if ($matchingWindow) {{ $matchingWindow }} else {{ $visibleWindows | Select-Object -First 1 }}

[Win32]::ShowWindowAsync($target.MainWindowHandle, 9) | Out-Null
Start-Sleep -Milliseconds 400
[Win32]::ShowWindowAsync($target.MainWindowHandle, 3) | Out-Null
Start-Sleep -Milliseconds 400
[Win32]::SetForegroundWindow($target.MainWindowHandle) | Out-Null

$shell = New-Object -ComObject WScript.Shell
$null = $shell.AppActivate([int]$target.Id)
Start-Sleep -Milliseconds 900
[Win32]::SetForegroundWindow($target.MainWindowHandle) | Out-Null

if ($openedNew) {{
    Start-Sleep -Milliseconds 2500
}} else {{
    Start-Sleep -Milliseconds 700
}}

# Experimento best effort: usa la secuencia validada en Power BI ES.
$shell.SendKeys('{{ESC}}')
Start-Sleep -Milliseconds 250
$shell.SendKeys('%')
Start-Sleep -Milliseconds 500
$shell.SendKeys('h')
Start-Sleep -Milliseconds 450
$shell.SendKeys('r')
Start-Sleep -Milliseconds 500
$shell.SendKeys('{{DOWN}}')
Start-Sleep -Milliseconds 450
$shell.SendKeys('{{ENTER}}')
$attemptedRefresh = $true

[pscustomobject]@{{
    opened_new = $openedNew
    attempted_refresh = $attemptedRefresh
    process_id = [int]$target.Id
    window_title = [string]$target.MainWindowTitle
}} | ConvertTo-Json -Compress
"""
    completed = subprocess.run(
        [*command_prefix, powershell_script],
        capture_output=True,
        text=True,
        check=True,
        timeout=35,
    )
    output = completed.stdout.strip()
    if not output:
        raise RuntimeError("La automatizacion de Power BI no devolvio ningun resultado.")
    return json.loads(output)


def _open_power_bi_report() -> None:
    """Abre o reactiva Power BI e intenta un refresh experimental del reporte."""
    report_path = _resolve_power_bi_report_path()
    if report_path is None:
        st.error(f"No se encontro ningun archivo .pbix en {POWER_BI_REPORT_DIR}.")
        return

    try:
        result = _run_power_bi_automation(report_path)
    except (OSError, RuntimeError, subprocess.SubprocessError, json.JSONDecodeError) as error:
        st.error(f"No fue posible automatizar Power BI: {error}")
        return

    if result.get("opened_new"):
        message = "Power BI abierto; refresh experimental enviado al reporte."
    else:
        message = "Power BI detectado; refresh experimental reenviado."
    st.toast(message, icon=":material/bolt:")


def _render_monitoring_table(transactions: list[dict[str, Any]]) -> None:
    """Renderiza la tabla principal de monitoreo con acciones editables."""
    header_columns = st.columns([6, 2])
    with header_columns[0]:
        render_subsection_header("Tabla de monitoreo")
    with header_columns[1]:
        automation_enabled = _supports_power_bi_automation()
        if st.button(
            "Power BI auto",
            key="open_power_bi_table",
            use_container_width=True,
            disabled=not automation_enabled,
            help=(
                None
                if automation_enabled
                else "Disponible solo en Windows con Power BI Desktop y PowerShell."
            ),
        ):
            _open_power_bi_report()
    render_text_block(
        "La cola se prioriza por riesgo y luego por probabilidad descendente. "
        "El tipo de transaccion queda como refinamiento secundario para la investigacion."
    )

    if not transactions:
        with section_card():
            st.info("No hay casos que coincidan con los filtros activos.")
        return

    dataframe = _build_monitoring_dataframe(transactions)

    with section_card():
        st.caption(
            f"Casos visibles: {len(transactions)} de {len(st.session_state.monitor_transactions)}."
        )
        edited = st.data_editor(
            dataframe,
            use_container_width=True,
            hide_index=True,
            key="monitoring_editor",
            column_config={
                "ID": st.column_config.TextColumn("ID"),
                "Origen": st.column_config.TextColumn("Origen"),
                "Tipo": st.column_config.TextColumn("Tipo"),
                "Modalidad": st.column_config.TextColumn("Modalidad"),
                "Contexto": st.column_config.TextColumn("Contexto"),
                "Monto": st.column_config.NumberColumn("Monto", format="$ %.2f"),
                "Probabilidad": st.column_config.ProgressColumn(
                    "Probabilidad",
                    min_value=0.0,
                    max_value=1.0,
                    format="%.2f",
                ),
                "Caso": st.column_config.TextColumn("Caso"),
                "Riesgo": st.column_config.TextColumn("Riesgo"),
                "Alerta": st.column_config.TextColumn("Alerta"),
                "Escenario": st.column_config.TextColumn("Escenario"),
                "Accion analista": st.column_config.SelectboxColumn(
                    "Accion analista",
                    options=ACTION_OPTIONS,
                    required=True,
                ),
            },
            disabled=[
                "ID",
                "Origen",
                "Tipo",
                "Modalidad",
                "Contexto",
                "Monto",
                "Probabilidad",
                "Caso",
                "Riesgo",
                "Alerta",
                "Escenario",
            ],
        )

        _sync_actions_from_editor(edited)


def _render_analyst_console(transactions: list[dict[str, Any]]) -> None:
    """Renderiza una consola simple para revisar y accionar una transaccion."""
    render_subsection_header("Consola del analista")
    render_text_block(
        "Prioriza primero por riesgo y usa el tipo de transaccion solo como apoyo. "
        "Luego selecciona un caso y toma una decision operativa."
    )

    with section_card():
        selector_cols = st.columns([1.0, 1.0, 1.7, 0.8])
        with selector_cols[0]:
            st.selectbox(
                "Riesgo",
                options=RISK_FILTER_OPTIONS,
                key="monitor_risk_filter",
            )
        with selector_cols[1]:
            st.selectbox(
                "Tipo de transaccion",
                options=TYPE_FILTER_OPTIONS,
                key="monitor_type_filter",
            )

        if not transactions:
            st.info("No hay casos disponibles para el tipo seleccionado.")
            return

        transaction_map = {
            item["transaction_id"]: item for item in transactions
        }
        selected_options = list(transaction_map)
        current_selection = st.session_state.get("selected_monitor_transaction")
        if current_selection not in transaction_map:
            st.session_state.selected_monitor_transaction = selected_options[0]

        selected = transaction_map[st.session_state.selected_monitor_transaction]

        with selector_cols[2]:
            st.selectbox(
                "Caso seleccionado",
                options=selected_options,
                key="selected_monitor_transaction",
            )
        with selector_cols[3]:
            st.text_input("Origen", value=selected["input_source"], disabled=True)

        selected = transaction_map[st.session_state.selected_monitor_transaction]

        st.caption(
            f"Tipo: {selected['type']} | Canal: {selected['channel']} | Franja: {selected['time_window']}"
        )

        first_row = st.columns(4)
        with first_row[0]:
            render_metric_card("Canal", selected["channel"], tone="positive")
        with first_row[1]:
            render_metric_card("Franja", selected["time_window"], tone="positive")
        with first_row[2]:
            render_metric_card("Segmento", selected["customer_segment"], tone="positive")
        with first_row[3]:
            render_metric_card("Estado saldo", selected["balance_status"], tone="positive")

        second_row = st.columns(4)
        with second_row[0]:
            render_metric_card("Caso", selected["case_title"], tone="positive")
        with second_row[1]:
            render_metric_card(
                "Probabilidad monitoreo",
                f"{float(selected['probabilidad_monitoreo']):.2%}",
                tone="emphasis",
            )
        with second_row[2]:
            render_metric_card(
                "Probabilidad modelo",
                f"{float(selected['probabilidad']):.2%}",
                tone="positive",
            )
        with second_row[3]:
            render_metric_card("Riesgo", selected["risk_indicator"], tone="emphasis")

        action_cols = st.columns(3)
        if action_cols[0].button("Revisar", use_container_width=True):
            _set_transaction_action(selected["transaction_id"], "Revisar")
            st.rerun()
        if action_cols[1].button("Marcar fraude", use_container_width=True):
            _set_transaction_action(selected["transaction_id"], "Marcar como fraude")
            st.rerun()
        if action_cols[2].button("Bloquear", use_container_width=True):
            _set_transaction_action(selected["transaction_id"], "Bloquear")
            st.rerun()

        st.caption(f"Accion actual: {selected['analyst_action']}")
        with st.expander("Ver detalle del caso"):
            st.markdown(f"**Lectura operativa:** {selected['modality_context']}")
            st.markdown(f"**Motivo principal:** {selected['case_reason']}")
            st.markdown(f"**Sugerencia de revision:** {selected['review_hint']}")


def _apply_monitoring_filters(
    transactions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Aplica filtros de riesgo y tipo sobre el lote ya evaluado."""
    risk_filter = st.session_state.get("monitor_risk_filter", "Todos")
    type_filter = st.session_state.get("monitor_type_filter", "Todos")

    filtered_transactions = transactions

    if risk_filter != "Todos":
        risk_mapping = {
            "Alto": "alto",
            "Medio": "medio",
            "Bajo": "bajo",
        }
        filtered_transactions = [
            item
            for item in filtered_transactions
            if item["risk_level"] == risk_mapping[risk_filter]
        ]

    if type_filter != "Todos":
        filtered_transactions = [
            item for item in filtered_transactions if item["type"] == type_filter
        ]

    risk_priority = {"alto": 0, "medio": 1, "bajo": 2}
    return sorted(
        filtered_transactions,
        key=lambda item: (
            risk_priority.get(item["risk_level"], 3),
            -float(item["probabilidad_monitoreo"]),
        ),
    )


def _run_monitoring(
    api_client,
    overview: dict[str, Any],
    source_mode: str,
    uploaded_file,
) -> None:
    """Ejecuta el monitoreo usando simulacion o archivo como fuente."""
    if api_client is None:
        st.error("La API no esta disponible para evaluar el lote.")
        return

    threshold = float(overview["umbral_monto_alto_transfer"])

    with st.spinner("Construyendo y evaluando lote de monitoreo..."):
        try:
            if source_mode == "Simulado":
                transactions = generate_transaction_batch(
                    batch_size=st.session_state.monitor_batch_size,
                    suspicious_rate=st.session_state.monitor_suspicious_rate,
                    high_amount_threshold=threshold,
                )
                preview = pd.DataFrame(
                    [
                        {
                            "step": item["step"],
                            "type": item["type"],
                            "amount": item["amount"],
                            "oldbalanceOrg": item["oldbalanceOrg"],
                            "oldbalanceDest": item["oldbalanceDest"],
                            "channel": item["channel"],
                            "customer_segment": item["customer_segment"],
                        }
                        for item in transactions
                    ]
                )
            else:
                if uploaded_file is None:
                    st.error("Carga un archivo CSV o Excel antes de ejecutar el monitoreo.")
                    return
                preview = _read_uploaded_dataframe(uploaded_file)
                transactions = build_transactions_from_records(
                    preview.to_dict(orient="records"),
                    high_amount_threshold=threshold,
                )

            scored = score_transactions_with_api(transactions, api_client)
            results_df = build_results_dataframe(scored)
            history_df = persist_monitoring_history(results_df)
        except (ApiClientError, OSError, ValueError) as error:
            st.error(f"No fue posible ejecutar el monitoreo: {error}")
            return

    st.session_state.monitor_transactions = scored
    st.session_state.monitor_results_dataframe = results_df
    st.session_state.monitor_history_dataframe = history_df
    st.session_state.monitor_input_preview = preview
    st.session_state.monitor_source = source_mode
    st.session_state.monitor_save_message = "Dataset listo para Power BI."
    st.session_state.selected_monitor_transaction = scored[0]["transaction_id"]
    st.session_state.pop("monitoring_editor", None)


def _read_uploaded_dataframe(uploaded_file) -> pd.DataFrame:
    """Lee archivos CSV o Excel para alimentar el monitoreo."""
    filename = uploaded_file.name.lower()
    if filename.endswith(".csv"):
        dataframe = pd.read_csv(uploaded_file)
    elif filename.endswith((".xlsx", ".xls")):
        dataframe = pd.read_excel(uploaded_file)
    else:
        raise ValueError("Formato no soportado. Usa CSV o Excel.")

    if dataframe.empty:
        raise ValueError("El archivo cargado no contiene filas para procesar.")

    validate_uploaded_columns(list(dataframe.columns))
    return dataframe


def _build_monitoring_dataframe(transactions: list[dict[str, Any]]) -> pd.DataFrame:
    """Construye el DataFrame que se muestra en la tabla editable."""
    results_df = st.session_state.monitor_results_dataframe
    transaction_ids = [item["transaction_id"] for item in transactions]

    if results_df is not None and not results_df.empty:
        filtered_df = results_df.loc[
            results_df["transaction_id"].isin(transaction_ids)
        ].copy()
        order_map = {transaction_id: index for index, transaction_id in enumerate(transaction_ids)}
        filtered_df["_order"] = filtered_df["transaction_id"].map(order_map)
        filtered_df = filtered_df.sort_values("_order").drop(columns="_order")

        return filtered_df.rename(
            columns={
                "transaction_id": "ID",
                "origen": "Origen",
                "type": "Tipo",
                "modalidad": "Modalidad",
                "contexto": "Contexto",
                "amount": "Monto",
                "probabilidad_monitoreo": "Probabilidad",
                "caso": "Caso",
                "riesgo_badge": "Riesgo",
                "alerta": "Alerta",
                "escenario": "Escenario",
                "accion_analista": "Accion analista",
            }
        )[
            [
                "ID",
                "Origen",
                "Tipo",
                "Modalidad",
                "Contexto",
                "Monto",
                "Probabilidad",
                "Caso",
                "Riesgo",
                "Alerta",
                "Escenario",
                "Accion analista",
            ]
        ]

    rows = []
    for item in transactions:
        rows.append(
            {
                "ID": item["transaction_id"],
                "Origen": item["input_source"],
                "Tipo": item["type"],
                "Modalidad": item["modality_label"],
                "Contexto": f"{item['customer_segment']} | {item['balance_status']}",
                "Monto": float(item["amount"]),
                "Probabilidad": float(item["probabilidad_monitoreo"]),
                "Caso": item["case_title"],
                "Riesgo": item["risk_indicator"],
                "Alerta": "Si" if item["alert"] else "No",
                "Escenario": item["scenario"],
                "Accion analista": item["analyst_action"],
            }
        )

    return pd.DataFrame(rows)


def _sync_actions_from_editor(edited: pd.DataFrame) -> None:
    """Sincroniza la columna editable de acciones con session state."""
    action_map = dict(zip(edited["ID"], edited["Accion analista"]))
    updated_transactions = []
    for item in st.session_state.monitor_transactions:
        updated_transactions.append(
            {
                **item,
                "analyst_action": action_map.get(item["transaction_id"], item["analyst_action"]),
            }
        )
    st.session_state.monitor_transactions = updated_transactions


def _set_transaction_action(transaction_id: str, action: str) -> None:
    """Actualiza la accion del analista para una transaccion concreta."""
    updated_transactions = []
    for item in st.session_state.monitor_transactions:
        if item["transaction_id"] == transaction_id:
            updated_transactions.append({**item, "analyst_action": action})
        else:
            updated_transactions.append(item)
    st.session_state.monitor_transactions = updated_transactions


def _build_file_help_text() -> str:
    """Resume las columnas aceptadas para archivos."""
    required = ", ".join(REQUIRED_FILE_FIELDS)
    optional = ", ".join(["timestamp", "channel", "customer_segment", "step"])
    alias_note = (
        f"Aliases soportados: {SUPPORTED_FILE_COLUMNS['type'][1]}, "
        f"{SUPPORTED_FILE_COLUMNS['amount'][1]}, {SUPPORTED_FILE_COLUMNS['channel'][1]}, "
        f"{SUPPORTED_FILE_COLUMNS['timestamp'][1]}."
    )
    return (
        f"Columnas requeridas: {required}. "
        f"Columnas opcionales: {optional}. "
        f"{alias_note}"
    )


def _initialize_state() -> None:
    """Inicializa el estado global usado por la simulacion."""
    if "monitor_transactions" not in st.session_state:
        st.session_state.monitor_transactions = []
    if "monitor_batch_size" not in st.session_state:
        st.session_state.monitor_batch_size = DEFAULT_BATCH_SIZE
    if "monitor_suspicious_rate" not in st.session_state:
        st.session_state.monitor_suspicious_rate = DEFAULT_SUSPICIOUS_RATE
    if "monitor_source_mode" not in st.session_state:
        st.session_state.monitor_source_mode = "Simulado"
    if "monitor_input_preview" not in st.session_state:
        st.session_state.monitor_input_preview = None
    if "monitor_results_dataframe" not in st.session_state:
        st.session_state.monitor_results_dataframe = None
    if "monitor_history_dataframe" not in st.session_state:
        st.session_state.monitor_history_dataframe = None
    if "monitor_save_message" not in st.session_state:
        st.session_state.monitor_save_message = ""
    if "monitor_source" not in st.session_state:
        st.session_state.monitor_source = "Simulado"
    if "monitor_risk_filter" not in st.session_state:
        st.session_state.monitor_risk_filter = "Todos"
    if "monitor_type_filter" not in st.session_state:
        st.session_state.monitor_type_filter = "Todos"
