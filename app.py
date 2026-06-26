import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Tablero de Control - OMEs",
    page_icon="📊",
)

st.markdown("""
<style>
    .main { background-color: #F4F8FC; }
    .block-container { padding-top: 1rem; padding-bottom: 1rem; }
    h1, h2, h3 { color: #0B3D91; }
    .kpi-card {
        background: white; padding: 18px 20px; border-radius: 14px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08); text-align: left; height: 110px;
    }
    .kpi-title { font-size: 13px; color: #6B7280; font-weight: 600; letter-spacing: .5px;}
    .kpi-value { font-size: 32px; font-weight: 800; color: #0B5FA5; margin-top: 4px;}
    .kpi-value.red { color: #DC2626; }
    .header-bar {
        background: linear-gradient(90deg,#E8F1FB,#FFFFFF);
        padding: 14px 20px; border-radius: 14px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 6px rgba(0,0,0,0.05); margin-bottom: 14px;
    }
    .header-title { font-size: 26px; font-weight: 800; color: #0B3D91; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 1. CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    df = pd.read_csv(
        "PR. OMES UNE.csv",
        sep=';',
        skiprows=8,
        decimal=',',
        encoding='utf-8'
    )
    df.columns = df.columns.str.strip()

    # ---------- Columna L (índice 11) = link SAP Ariba ----------
    if df.shape[1] > 11:
        nombre_col_l = df.columns[11]
        df.rename(columns={nombre_col_l: 'Link_Ariba'}, inplace=True)
    else:
        df['Link_Ariba'] = ''

    # Limpieza del link
    df['Link_Ariba'] = (
        df['Link_Ariba']
        .astype(str)
        .str.strip()
        .replace({'nan': '', 'None': '', 'NaT': ''})
    )

    # ---------- Número de esquema como texto ----------
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()

    # ---------- % completado a numérico ----------
    df['% completado'] = (
        df['% completado']
        .astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    if df['% completado'].max() > 1.5:
        df['% completado'] = df['% completado'] / 100.0

    # ---------- Fechas ----------
    for col in ['Comienzo', 'Finalización']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

    return df

df = cargar_datos()

# ============================================================
# 2. TAREAS PRINCIPALES Y SUB-TAREAS
# ============================================================
df['Es_Principal'] = ~df['Número de esquema'].str.contains(r'\.', regex=True, na=False)
df['Obra_ID'] = df['Es_Principal'].cumsum()

orden_etapas = [
    'Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel',
    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado',
]
etapas_upper = [
    'PLIEGO', 'REVISIÓN DOM', 'PRESUPUESTO', 'DOC. EN PAPEL',
    'ORSNA', 'ADJUDICACIÓN', 'EJECUCIÓN', 'CAO PRESENTADO'
]
mapa_upper = dict(zip(orden_etapas, etapas_upper))

colores_etapas = {
    'PLIEGO': '#A8D8F0',
    'REVISIÓN DOM': '#F39C58',
    'PRESUPUESTO': '#A8D26F',
    'DOC. EN PAPEL': '#E15A5A',
    'ORSNA': '#E76FA1',
    'ADJUDICACIÓN': '#9B59B6',
    'EJECUCIÓN': '#1F8A4C',
    'CAO PRESENTADO': '#3FA9B5',
    'FINALIZADA': '#2E86C1',
    'SIN INICIAR': '#BDC3C7',
}

# ============================================================
# 3. INSTANCIA ACTUAL POR OBRA
# ============================================================
TOL = 1e-6
resultados = []

for obra_id, grupo in df.groupby('Obra_ID'):
    fila = grupo[grupo['Es_Principal']].iloc[0]
    nombre = fila['Nombre']
    aero   = fila.get('Aero', '')
    n_ome  = fila.get('N° OME', '')
    avance = fila.get('% completado', 0)
    inicio = fila.get('Comienzo', pd.NaT)
    fin    = fila.get('Finalización', pd.NaT)
    link_ariba = str(fila.get('Link_Ariba', '')).strip()

    # Fallback: buscar link en sub-tareas si la principal no lo tiene
    if not link_ariba:
        links_sub = grupo['Link_Ariba'].dropna().astype(str).str.strip()
        links_sub = links_sub[links_sub != '']
        if not links_sub.empty:
            link_ariba = links_sub.iloc[0]

    # Validamos que sea un URL aparente
    if link_ariba and not link_ariba.lower().startswith(('http://', 'https://')):
        link_ariba = ''

    sub = grupo[~grupo['Es_Principal']].copy()
    sub['Nombre_norm'] = sub['Nombre'].astype(str).str.strip().str.lower()

    etapas_pct = []
    for etapa in orden_etapas:
        m = sub[sub['Nombre_norm'] == etapa.lower()]
        if not m.empty:
            etapas_pct.append((etapa, float(m['% completado'].iloc[0])))

    instancia = "SIN INICIAR"
    if etapas_pct:
        en_curso = next(((e, p) for e, p in etapas_pct if TOL < p < 1.0 - TOL), None)
        if en_curso:
            instancia = mapa_upper[en_curso[0]]
        elif all(p >= 1.0 - TOL for _, p in etapas_pct):
            instancia = "FINALIZADA"
        elif all(p <= TOL for _, p in etapas_pct):
            instancia = "SIN INICIAR"
        else:
            pend = next((e for e, p in etapas_pct if p <= TOL), None)
            if pend:
                instancia = mapa_upper[pend]

    # Estado: Completada / En Curso / Crítica
    hoy = pd.Timestamp(datetime.now().date())
    if instancia == "FINALIZADA":
        estado = "Completada"
    elif pd.notna(fin) and fin < hoy and avance < 1.0:
        estado = "Crítica"
    else:
        estado = "En Curso"

    resultados.append({
        'ID': n_ome,
        'NOMBRE DE OBRA': nombre,
        'AEROPUERTO': aero,
        'INSTANCIA': instancia,
        '% AVANCE': round(avance * 100, 0),
        'ESTADO': estado,
        'FECHA INICIO': inicio,
        'VENCIMIENTO': fin,
        'SAP ARIBA': link_ariba,
    })

df_inst = pd.DataFrame(resultados)

# ============================================================
# 4. HEADER
# ============================================================
fecha_actual = datetime.now().strftime("%d/%m/%Y")
st.markdown(f"""
<div class="header-bar">
    <div class="header-title">📊 TABLERO DE CONTROL - GESTIÓN DE OMEs (PLANNERS)</div>
    <div style="text-align:right;">
        <div style="font-weight:700; color:#0B3D91;">GESTOR DE PROYECTOS</div>
        <div style="font-size:12px; color:#6B7280;">Actualizado: {fecha_actual}</div>
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 5. FILTROS LATERALES
# ============================================================
st.sidebar.markdown("## 🔎 FILTROS")

aeros = sorted([a for a in df_inst['AEROPUERTO'].dropna().unique() if str(a).strip()])
sel_aero = st.sidebar.multiselect("Aeropuerto", aeros, default=aeros)

estados = ['Completada', 'En Curso', 'Crítica']
sel_estado = st.sidebar.multiselect("Estado", estados, default=estados)

instancias_disp = etapas_upper + ['FINALIZADA', 'SIN INICIAR']
sel_inst = st.sidebar.multiselect("Instancia", instancias_disp, default=instancias_disp)

META_FINALIZADAS = st.sidebar.slider("Meta % obras finalizadas", 0, 100, 85)

solo_con_link = st.sidebar.checkbox("Mostrar solo obras con link SAP Ariba", value=False)

df_f = df_inst[
    df_inst['AEROPUERTO'].isin(sel_aero) &
    df_inst['ESTADO'].isin(sel_estado) &
    df_inst['INSTANCIA'].isin(sel_inst)
]

if solo_con_link:
    df_f = df_f[df_f['SAP ARIBA'].str.len() > 0]

# ============================================================
# 6. KPIs + DONUT + BARRAS
# ============================================================
total = len(df_f)
activas = (df_f['ESTADO'] == 'En Curso').sum()
atrasadas = (df_f['ESTADO'] == 'Crítica').sum()
finalizadas = (df_f['ESTADO'] == 'Completada').sum()
pct_finalizadas = (finalizadas / total * 100) if total else 0

col_kpi, col_donut, col_bar = st.columns([1.1, 1.2, 2.7])

with col_kpi:
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-title">📁 TOTAL OMEs</div>
    <div class="kpi-value">{total:,}</div></div>
    """, unsafe_allow_html=True)
    st.write("")
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-title">📈 TAREAS ACTIVAS</div>
    <div class="kpi-value">{activas:,}</div></div>
    """, unsafe_allow_html=True)
    st.write("")
    st.markdown(f"""
    <div class="kpi-card"><div class="kpi-title">⚠️ ATRASADAS</div>
    <div class="kpi-value red">{atrasadas:,}</div></div>
    """, unsafe_allow_html=True)

with col_donut:
    st.markdown("#### OBRAS FINALIZADAS")
    fig_donut = go.Figure(go.Pie(
        values=[pct_finalizadas, 100 - pct_finalizadas],
        labels=['Finalizadas', 'Pendientes'],
        hole=0.72,
        marker_colors=['#0B5FA5', '#E5EEF7'],
        textinfo='none',
        sort=False,
    ))
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=10, b=10),
        height=280,
        annotations=[dict(
            text=f"<b>{pct_finalizadas:.0f}%</b><br><span style='font-size:12px'>FINALIZADAS</span>",
            x=0.5, y=0.5, font_size=28, showarrow=False
        )],
    )
    st.plotly_chart(fig_donut, use_container_width=True)
    st.caption(f"🎯 META: {META_FINALIZADAS}%  ·  Actual: {pct_finalizadas:.1f}%")

with col_bar:
    st.markdown("#### OBRAS POR INSTANCIA")
    conteo = (
        df_f['INSTANCIA'].value_counts()
        .reindex(etapas_upper, fill_value=0)
        .reset_index()
    )
    conteo.columns = ['Etapa', 'Cantidad']
    fig_bar = px.bar(
        conteo, x='Etapa', y='Cantidad', text='Cantidad',
        color='Etapa', color_discrete_map=colores_etapas,
    )
    fig_bar.update_traces(textposition='outside')
    fig_bar.update_layout(
        showlegend=False, xaxis_tickangle=-25,
        margin=dict(l=10, r=10, t=10, b=10), height=300,
        yaxis_title=None, xaxis_title=None, plot_bgcolor='white',
    )
    st.plotly_chart(fig_bar, use_container_width=True)

# ============================================================
# 7. LISTADO DETALLADO
# ============================================================
st.markdown("### 📋 LISTADO DE OMEs DETALLADO")

def fmt_estado(s):
    if s == "Completada":
        return "🔵 Completada"
    if s == "En Curso":
        return "🟢 En Curso"
    if s == "Crítica":
        return "🔴 Crítica"
    return s

df_show = df_f.copy()
df_show['ESTADO'] = df_show['ESTADO'].map(fmt_estado)
df_show['FECHA INICIO'] = df_show['FECHA INICIO'].dt.strftime('%d/%m/%Y').fillna('-')
df_show['VENCIMIENTO']  = df_show['VENCIMIENTO'].dt.strftime('%d/%m/%Y').fillna('-')

cols_order = [
    'ID', 'NOMBRE DE OBRA', 'AEROPUERTO', 'INSTANCIA',
    '% AVANCE', 'ESTADO', 'FECHA INICIO', 'VENCIMIENTO', 'SAP ARIBA'
]
df_show = df_show[cols_order]

st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True,
    column_config={
        "% AVANCE": st.column_config.ProgressColumn(
            "% AVANCE", format="%d%%", min_value=0, max_value=100,
        ),
        "ID": st.column_config.TextColumn(width="small"),
        "NOMBRE DE OBRA": st.column_config.TextColumn(width="large"),
        "SAP ARIBA": st.column_config.LinkColumn(
            "SAP ARIBA",
            help="Abrir la obra en SAP Ariba",
            display_text="🔗 Abrir",
            width="small",
        ),
    },
)

# ============================================================
# 8. DATOS CRUDOS
# ============================================================
with st.expander("🔍 Ver todas las tareas y sub-tareas (datos crudos)"):
    st.dataframe(
        df[['Número de esquema', 'Nombre', 'Aero', 'N° OME',
            '% completado', 'Link_Ariba', 'Es_Principal', 'Obra_ID']],
        use_container_width=True,
        hide_index=True,
    )
