
from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path
import os
import shutil

import pandas as pd
import streamlit as st

from modules.database import DATA_DIR, DB_PATH, init_db, seed_efemerides, table_count, query_df
from modules.excel_loader import import_excel_folder, import_excel_file, analyze_folder
from modules.curriculum import get_curriculum, filter_curriculum, unique_values
from modules.efemerides import list_efemerides, save_efemeride, remove_efemeride
from modules.eventos import list_eventos, save_evento, remove_evento
from modules.recursos import list_recursos, save_recurso, remove_recurso, recursos_por_estado
from modules.exportador import df_to_excel_bytes, df_to_csv_bytes, agenda_to_pdf_bytes

PROJECT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = PROJECT_DIR / "assets"
LOGO_PATH = ASSETS_DIR / "logo.png"

st.set_page_config(
    page_title="Fundación Philia Sophia",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
:root { --philia:#704023; --soft:#f7efe5; --gold:#c49353; --ink:#2f241f; }
.block-container { padding-top: 1.5rem; }
.main-title {background: linear-gradient(90deg, #f7efe5, #fffaf3); padding: 1.2rem 1.4rem; border-radius: 22px; border:1px solid #ead8c6; margin-bottom:1rem;}
.main-title h1 {color:#3f2b1f; margin-bottom:0.1rem; font-size:2rem;}
.main-title p {color:#704023; font-size:1rem; margin:0;}
.metric-card {border: 1px solid #ead8c6; border-radius: 18px; padding: 1rem; background:#fffaf3;}
.small-note {color:#6b5b51; font-size:0.9rem;}
.status {padding:0.25rem 0.55rem; border-radius:999px; background:#f2e7d8; color:#704023;}
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)


def bootstrap():
    init_db()
    seed_efemerides()
    if table_count("curriculum") == 0:
        import_excel_folder(DATA_DIR)


def header():
    c_logo, c_title = st.columns([1, 5], vertical_alignment="center")
    with c_logo:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown("### 📚")
    with c_title:
        st.markdown(
            """
            <div class="main-title">
                <h1>Fundación Philia Sophia</h1>
                <p>Calendario pedagógico y planificación de recursos</p>
            </div>
            """,
            unsafe_allow_html=True,
        )


def as_date(value):
    if not value:
        return None
    try:
        return pd.to_datetime(value).date()
    except Exception:
        return None


def week_of_month(d: date) -> int:
    return ((d.day - 1) // 7) + 1


def semana_label_to_int(value) -> int | None:
    """Convierte valores como 3, "3" o "Semana 3" en entero 3."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() in {"nan", "none"}:
        return None
    import re
    match = re.search(r"\d+", text)
    return int(match.group(0)) if match else None


def current_month_name() -> str:
    meses = ["Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]
    return meses[date.today().month - 1]


def select_filters(df, key_prefix="f"):
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        nivel = st.selectbox("Nivel", ["Todos"] + unique_values(df, "nivel"), key=f"{key_prefix}_nivel")
    with c2:
        unidad = st.selectbox("Sala / grado / año", ["Todos"] + unique_values(df, "unidad"), key=f"{key_prefix}_unidad")
    with c3:
        area = st.selectbox("Área", ["Todos"] + unique_values(df, "area"), key=f"{key_prefix}_area")
    with c4:
        mes = st.selectbox("Mes", ["Todos"] + unique_values(df, "mes"), key=f"{key_prefix}_mes")
    with c5:
        semana = st.selectbox("Semana lectiva", ["Todos"] + unique_values(df, "semana_lectiva"), key=f"{key_prefix}_sem")
    return nivel, unidad, area, mes, semana


def display_df(df, cols=None, height=420):
    if df is None or df.empty:
        st.info("No hay registros para mostrar con esos filtros.")
        return
    if cols:
        existing = [c for c in cols if c in df.columns]
        df = df[existing]
    st.dataframe(df, use_container_width=True, height=height)


def page_dashboard():
    header()
    curr = get_curriculum()
    efem = list_efemerides()
    eventos = list_eventos()
    recursos = list_recursos()

    hoy = date.today()
    mes_actual = current_month_name()
    semana_mes_actual = week_of_month(hoy)
    semana_df = curr[(curr["mes"].astype(str).str.lower() == mes_actual.lower())].copy()
    if "semana_mes" in semana_df.columns:
        semana_df["_semana_mes_num"] = semana_df["semana_mes"].apply(semana_label_to_int)
        semana_df = semana_df[semana_df["_semana_mes_num"] == semana_mes_actual].drop(columns=["_semana_mes_num"], errors="ignore")

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("Contenidos curriculares", len(curr))
    m2.metric("Efemérides", len(efem))
    m3.metric("Eventos", len(eventos))
    pendientes = recursos[recursos.get("estado", pd.Series(dtype=str)).astype(str).str.contains("Idea|Pendiente|elaboración|revisión|Listo", case=False, na=False)] if not recursos.empty else recursos
    m4.metric("Recursos pendientes", len(pendientes))
    publicados = recursos[recursos.get("estado", pd.Series(dtype=str)).astype(str).str.contains("Publicado", case=False, na=False)] if not recursos.empty else recursos
    m5.metric("Publicados", len(publicados))

    st.subheader(f"Semana actual aproximada: {mes_actual}, semana {semana_mes_actual}")
    st.caption("La semana actual se calcula por fecha del sistema. También podés usar la consulta semanal para seleccionar cualquier semana lectiva.")
    display_df(semana_df, ["nivel", "unidad", "area", "mes", "semana_lectiva", "eje", "contenido", "momento2"], 340)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Próximas efemérides")
        if not efem.empty:
            efem["fecha_dt"] = pd.to_datetime(efem["fecha"], errors="coerce")
            proximas = efem[efem["fecha_dt"].dt.date >= hoy].sort_values("fecha_dt").head(8)
            display_df(proximas, ["fecha", "nombre", "nivel_sugerido", "area", "prioridad", "estado"], 280)
        else:
            st.info("Todavía no hay efemérides cargadas.")
    with c2:
        st.subheader("Recursos por estado")
        estados = recursos_por_estado()
        if not estados.empty:
            st.bar_chart(estados.set_index("estado"))
        else:
            st.info("Todavía no hay recursos cargados.")


def page_curriculum():
    header()
    st.subheader("Consulta curricular semanal")
    curr = get_curriculum()
    nivel, unidad, area, mes, semana = select_filters(curr, "curr")
    result = filter_curriculum(nivel, unidad, area, mes, semana)
    display_df(result, ["id", "nivel", "unidad", "area", "mes", "semana_mes", "semana_lectiva", "estado_calendario", "eje", "contenido", "foco", "contexto", "momento1", "momento2", "momento3", "momento4", "observaciones"], 520)

    st.markdown("### Crear recurso desde esta consulta")
    if not result.empty:
        ids = result["id"].astype(int).tolist()
        selected_id = st.selectbox("Seleccionar contenido curricular de base", ids, format_func=lambda x: f"#{x} - {result.loc[result['id']==x, 'unidad'].iloc[0]} | {result.loc[result['id']==x, 'area'].iloc[0]} | {str(result.loc[result['id']==x, 'contenido'].iloc[0])[:85]}")
        row = result[result["id"] == selected_id].iloc[0].to_dict()
        with st.form("crear_recurso_desde_curriculum"):
            titulo = st.text_input("Título del recurso", f"Recurso: {row.get('contenido','')[:65]}")
            tipo = st.selectbox("Tipo de recurso", ["Imagen", "Carrusel", "PDF", "Actividad imprimible", "Historieta", "Video", "Guía docente", "Publicación de Instagram"])
            estado = st.selectbox("Estado", ["Idea", "Pendiente", "En elaboración", "En revisión", "Listo para publicar", "Publicado", "Archivado"])
            responsable = st.text_input("Responsable")
            fecha_pub = st.date_input("Fecha estimada de publicación", value=date.today())
            obs = st.text_area("Observaciones / idea pedagógica", f"Articular con el eje: {row.get('eje','')}")
            submitted = st.form_submit_button("Guardar recurso")
            if submitted:
                save_recurso({
                    "titulo": titulo, "nivel": row.get("nivel", ""), "unidad": row.get("unidad", ""),
                    "area": row.get("area", ""), "mes": row.get("mes", ""), "semana_lectiva": row.get("semana_lectiva", ""),
                    "semana_calendario": row.get("semana_calendario", ""), "tipo_recurso": tipo,
                    "estado": estado, "responsable": responsable, "fecha_publicacion": fecha_pub.isoformat(),
                    "observaciones": obs, "curriculum_id": selected_id, "efemeride": "",
                })
                st.success("Recurso guardado.")
                st.rerun()


def page_calendar():
    header()
    st.subheader("Calendario pedagógico")
    curr = get_curriculum()
    nivel, unidad, area, mes, semana = select_filters(curr, "cal")
    result = filter_curriculum(nivel, unidad, area, mes, semana)

    recursos = list_recursos()
    efem = list_efemerides()
    eventos = list_eventos()

    tab1, tab2, tab3, tab4 = st.tabs(["Contenidos", "Recursos", "Efemérides", "Eventos"])
    with tab1:
        display_df(result, ["nivel", "unidad", "area", "mes", "semana_lectiva", "eje", "contenido", "momento2"], 520)
    with tab2:
        display_df(recursos, ["id", "fecha_publicacion", "titulo", "nivel", "unidad", "area", "semana_lectiva", "tipo_recurso", "estado", "responsable"], 520)
    with tab3:
        display_df(efem, ["fecha", "nombre", "nivel_sugerido", "area", "ideas_recursos", "prioridad", "estado"], 520)
    with tab4:
        display_df(eventos, ["fecha", "nombre", "tipo", "responsables", "lugar", "nivel", "estado"], 520)


def crud_page(title, table_name, list_func, save_func, remove_func, fields, select_label):
    header()
    st.subheader(title)
    df = list_func()
    display_df(df, height=360)

    mode = st.radio("Acción", ["Agregar", "Editar", "Eliminar"], horizontal=True, key=f"mode_{table_name}")
    if mode == "Agregar":
        selected = None
        record_id = None
    elif df.empty:
        st.info("No hay registros disponibles para editar o eliminar.")
        return
    else:
        record_id = st.selectbox(select_label, df["id"].astype(int).tolist(), format_func=lambda x: f"#{x} - {df.loc[df['id']==x].iloc[0].get('nombre', df.loc[df['id']==x].iloc[0].get('titulo', ''))}")
        selected = df[df["id"] == record_id].iloc[0].to_dict()

    if mode == "Eliminar" and record_id:
        if st.button("Eliminar registro", type="primary"):
            remove_func(int(record_id))
            st.success("Registro eliminado.")
            st.rerun()
        return

    with st.form(f"form_{table_name}_{mode}"):
        data = {}
        for field in fields:
            name, label, kind, options = field
            default = selected.get(name, "") if selected else ""
            if kind == "date":
                default_date = as_date(default) or date.today()
                data[name] = st.date_input(label, value=default_date).isoformat()
            elif kind == "select":
                opts = options or [""]
                idx = opts.index(default) if default in opts else 0
                data[name] = st.selectbox(label, opts, index=idx)
            elif kind == "textarea":
                data[name] = st.text_area(label, value=default)
            else:
                data[name] = st.text_input(label, value=default)
        submitted = st.form_submit_button("Guardar")
        if submitted:
            save_func(data, int(record_id) if record_id else None)
            st.success("Registro guardado.")
            st.rerun()


def page_efemerides():
    fields = [
        ("fecha", "Fecha", "date", None),
        ("nombre", "Nombre de la efeméride", "text", None),
        ("descripcion", "Descripción breve", "textarea", None),
        ("nivel_sugerido", "Nivel sugerido", "text", None),
        ("area", "Área posible de articulación", "text", None),
        ("ideas_recursos", "Ideas de recursos", "textarea", None),
        ("prioridad", "Prioridad", "select", ["Alta", "Media", "Baja"]),
        ("estado", "Estado", "select", ["Pendiente", "En preparación", "Publicado", "Descartado"]),
    ]
    crud_page("Gestión de efemérides", "efemerides", list_efemerides, save_efemeride, remove_efemeride, fields, "Seleccionar efeméride")


def page_eventos():
    fields = [
        ("fecha", "Fecha", "date", None),
        ("nombre", "Nombre del evento", "text", None),
        ("tipo", "Tipo de evento", "select", ["Lanzamiento", "Capacitación", "Reunión", "Publicación especial", "Campaña educativa", "Entrega interna", "Otro"]),
        ("descripcion", "Descripción", "textarea", None),
        ("responsables", "Responsables", "text", None),
        ("lugar", "Lugar", "text", None),
        ("nivel", "Nivel educativo vinculado", "text", None),
        ("estado", "Estado", "select", ["Pendiente", "En preparación", "Realizado", "Reprogramado", "Cancelado"]),
        ("observaciones", "Observaciones", "textarea", None),
    ]
    crud_page("Gestión de eventos institucionales", "eventos", list_eventos, save_evento, remove_evento, fields, "Seleccionar evento")


def page_recursos():
    fields = [
        ("titulo", "Título", "text", None),
        ("nivel", "Nivel", "text", None),
        ("unidad", "Sala / grado / año", "text", None),
        ("area", "Área", "text", None),
        ("mes", "Mes", "text", None),
        ("semana_lectiva", "Semana lectiva", "text", None),
        ("semana_calendario", "Semana calendario", "text", None),
        ("efemeride", "Efeméride vinculada", "text", None),
        ("tipo_recurso", "Tipo de recurso", "select", ["Imagen", "Carrusel", "PDF", "Actividad imprimible", "Historieta", "Video", "Guía docente", "Publicación de Instagram", "Otro"]),
        ("estado", "Estado", "select", ["Idea", "Pendiente", "En elaboración", "En revisión", "Listo para publicar", "Publicado", "Archivado"]),
        ("responsable", "Responsable", "text", None),
        ("fecha_publicacion", "Fecha estimada de publicación", "date", None),
        ("observaciones", "Observaciones", "textarea", None),
    ]
    crud_page("Gestión de recursos pedagógicos", "recursos", list_recursos, save_recurso, remove_recurso, fields, "Seleccionar recurso")


def page_agenda():
    header()
    st.subheader("Generador de agenda semanal")
    curr = get_curriculum()
    c1, c2 = st.columns(2)
    with c1:
        mes = st.selectbox("Mes", unique_values(curr, "mes"), index=unique_values(curr, "mes").index(current_month_name()) if current_month_name() in unique_values(curr, "mes") else 0)
    with c2:
        semana = st.selectbox("Semana lectiva", unique_values(curr, "semana_lectiva"))

    contenidos = filter_curriculum(mes=mes, semana_lectiva=semana)
    efem = list_efemerides()
    eventos = list_eventos()
    recursos = list_recursos()
    if not efem.empty and not contenidos.empty and contenidos["mes_numero"].dropna().shape[0]:
        mes_numero = int(contenidos["mes_numero"].dropna().iloc[0])
        fechas_efem = pd.to_datetime(efem["fecha"], errors="coerce")
        efem_mes = efem[fechas_efem.dt.month == mes_numero]
    else:
        efem_mes = efem.head(0) if not efem.empty else efem
    recursos_sem = recursos[(recursos.get("mes", pd.Series(dtype=str)).astype(str) == str(mes)) | (recursos.get("semana_lectiva", pd.Series(dtype=str)).astype(str) == str(semana))] if not recursos.empty else recursos

    st.markdown("### Contenidos de la semana")
    display_df(contenidos, ["nivel", "unidad", "area", "semana_lectiva", "eje", "contenido", "momento2"], 280)
    st.markdown("### Efemérides del mes")
    display_df(efem_mes, ["fecha", "nombre", "nivel_sugerido", "area", "ideas_recursos", "prioridad", "estado"], 240)
    st.markdown("### Recursos vinculados")
    display_df(recursos_sem, ["fecha_publicacion", "titulo", "nivel", "unidad", "area", "tipo_recurso", "estado", "responsable"], 240)
    st.markdown("### Eventos institucionales")
    display_df(eventos, ["fecha", "nombre", "tipo", "responsables", "estado"], 180)

    sheets = {"Contenidos": contenidos, "Efemerides": efem_mes, "Recursos": recursos_sem, "Eventos": eventos}
    excel_bytes = df_to_excel_bytes(sheets)
    st.download_button("Descargar agenda semanal en Excel", excel_bytes, file_name=f"agenda_{mes}_semana_{semana}.xlsx")
    pdf_bytes = agenda_to_pdf_bytes(f"Agenda semanal - {mes} - Semana {semana}", sheets)
    if pdf_bytes:
        st.download_button("Descargar agenda semanal en PDF", pdf_bytes, file_name=f"agenda_{mes}_semana_{semana}.pdf", mime="application/pdf")


def page_import():
    header()
    st.subheader("Importar o reimportar Excel curriculares")
    st.markdown("Los archivos cargados se normalizan a una estructura común sin modificar los Excel originales.")
    st.caption(f"Base de datos actual: {DB_PATH}")

    if st.button("Importar todos los Excel de la carpeta data/"):
        results = import_excel_folder(DATA_DIR)
        st.success("Importación finalizada. Los registros repetidos se ignoran por hash curricular.")
        st.json(results)

    uploaded = st.file_uploader("Cargar nuevo Excel curricular", type=["xlsx", "xlsm"])
    if uploaded is not None:
        target = DATA_DIR / uploaded.name
        with open(target, "wb") as f:
            f.write(uploaded.getbuffer())
        if st.button("Importar archivo cargado"):
            count = import_excel_file(target)
            st.success(f"Se importaron {count} registros nuevos desde {uploaded.name}.")

    st.markdown("### Diagnóstico de estructura de Excel")
    if st.button("Analizar estructura de archivos"):
        info = pd.DataFrame(analyze_folder(DATA_DIR))
        display_df(info, height=520)


def page_exports():
    header()
    st.subheader("Exportaciones")
    tables = {
        "curriculum": get_curriculum(),
        "efemerides": list_efemerides(),
        "eventos": list_eventos(),
        "recursos": list_recursos(),
    }
    selection = st.multiselect("Seleccionar tablas para exportar", list(tables.keys()), default=list(tables.keys()))
    selected = {k: v for k, v in tables.items() if k in selection}
    if selected:
        st.download_button("Descargar Excel consolidado", df_to_excel_bytes(selected), file_name="philia_sophia_exportacion.xlsx")
        for name, df in selected.items():
            st.download_button(f"Descargar {name}.csv", df_to_csv_bytes(df), file_name=f"{name}.csv", mime="text/csv")


def page_diagnostico():
    header()
    st.subheader("Estructura detectada en los Excel")
    info = pd.DataFrame(analyze_folder(DATA_DIR))
    display_df(info, height=620)


def main():
    bootstrap()
    with st.sidebar:
        if LOGO_PATH.exists():
            st.image(str(LOGO_PATH), use_container_width=True)
        else:
            st.markdown("### 📚 Fundación Philia Sophia")
        st.markdown("### Menú")
        page = st.radio(
            "Sección",
            [
                "Panel principal", "Consulta curricular semanal", "Calendario pedagógico",
                "Efemérides", "Eventos", "Recursos", "Agenda semanal", "Importar Excel",
                "Exportaciones", "Diagnóstico Excel",
            ],
            label_visibility="collapsed",
        )
        st.markdown("---")
        st.caption("Herramienta local. Los cambios se guardan en SQLite.")

    if page == "Panel principal":
        page_dashboard()
    elif page == "Consulta curricular semanal":
        page_curriculum()
    elif page == "Calendario pedagógico":
        page_calendar()
    elif page == "Efemérides":
        page_efemerides()
    elif page == "Eventos":
        page_eventos()
    elif page == "Recursos":
        page_recursos()
    elif page == "Agenda semanal":
        page_agenda()
    elif page == "Importar Excel":
        page_import()
    elif page == "Exportaciones":
        page_exports()
    elif page == "Diagnóstico Excel":
        page_diagnostico()


if __name__ == "__main__":
    main()
