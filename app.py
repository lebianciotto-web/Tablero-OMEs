import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime

# ============================================================
# CONFIGURACIÓN 16:9 COMPACTA
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Tablero OMEs · Aeropuertos Argentina",
    page_icon="✈",
)

# ============================================================
# ESTILOS — AVIATION PASTEL
# ============================================================
st.markdown("""
<style>
    html, body, [class*="css"] {
        font-family: 'Segoe UI', 'Inter', sans-serif;
    }
    .main { background-color: #EDF2F4; }
    .block-container {
        padding-top: 0.8rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }
    header[data-testid="stHeader"] { background: transparent; height: 0; }
    #MainMenu, footer { visibility: hidden; }

    .header-bar {
        background: linear-gradient(100deg, #1B4965 0%, #3A7CA5 100%);
        padding: 10px 22px;
        border-radius: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 2px 8px rgba(27,73,101,0.18);
        margin-bottom: 10px;
        color: white;
    }
    .header-title {
        font-size: 18px; font-weight: 700;
        letter-spacing: 1.2px; color: white;
    }
    .header-sub {
        font-size: 11px; color: #BEE9E8;
        letter-spacing: 0.5px; text-transform: uppercase;
    }
    .header-right {
        text-align: right; font-size: 11px;
        color: #BEE9E8; letter-spacing: 0.5px;
    }
    .header-right b { color: white; font-size: 13px; letter-spacing: 1px; }

    .kpi-card {
        background: white;
        padding: 10px 14px;
        border-radius: 10px;
        box-shadow: 0 1px 4px rgba(27,73,101,0.08);
        border-left: 4px solid #5FA8D3;
        height: 70px;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }
    .kpi-card.alert  { border-left-color: #E29578; }
    .kpi-card.ok     { border-left-color: #86C6A4; }
    .kpi-card.warn   { border-left-color: #F1B963; }
    .kpi-title {
        font-size: 10px; color: #6B7C93;
        font-weight: 600; letter-spacing: 1px;
        text-transform: uppercase;
    }
    .kpi-value {
        font-size: 26px; font-weight: 700;
        color: #1B4965; line-height: 1.1; margin-top: 2px;
    }
    .kpi-value.alert { color: #C75D44; }
    .kpi-value.ok    { color: #4F9D75; }

    .panel-title {
        font-size: 11px; font-weight: 700;
        color: #1B4965; letter-spacing: 1.2px;
        text-transform: uppercase;
        border-bottom: 1px solid #EDF2F4;
        padding-bottom: 4px; margin-bottom: 6px;
        margin-top: 8px;
    }

    section[data-testid="stSidebar"] { background: #1B4965; }
    section[data-testid="stSidebar"] * { color: #E8F1F8 !important; }
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
        color: #BEE9E8 !important;
        font-size: 12px !important;
        letter-spacing: 1.5px;
        text-transform: uppercase;
    }

    [data-testid="stDataFrame"] {
        border-radius: 8px;
        overflow: hidden;
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# 1. CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    df = pd.read_csv(
        "PR. OMES UNE.csv",
        sep=';', skiprows=8, decimal=',', encoding='utf-8'
    )
    df.columns = df.columns.str.strip()

    # Columna L (índice 11) = link SAP Ariba
    if df.shape[1] > 11:
        nombre_col_l = df.columns[11]
        df.rename(columns={nombre_col_l: 'Link_Ariba'}, inplace=True)
    else:
        df['Link_Ariba'] = ''

    df['Link_Ariba'] = (
        df['Link_Ariba'].astype(str).str.strip()
        .replace({'nan': '', 'None': '', 'NaT': ''})
    )
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()

    df['% completado'] = (
        df['% completado'].astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    if df['% completado'].max() > 1.5:
        df['% completado'] = df['% completado'] / 100.0

    for col in ['Comienzo', 'Finalización']:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors='coerce', dayfirst=True)

    return df

df = cargar_datos()

# ============================================================
# 2. TAREAS Y SUB-TAREAS
# ============================================================
df['Es_Principal'] = ~df['Número de esquema'].str.contains(r'\.', regex=True, na=False)
df['Obra_ID'] = df['Es_Principal'].cumsum()

orden_etapas = [
    'Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel',
    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado',
]
etapas_upper = [
    'PLIEGO', 'REV. DOM', 'PRESUPUESTO', 'DOC. PAPEL',
    'ORSNA', 'ADJUDIC.', 'EJECUCIÓN', 'CAO'
]
mapa_upper = dict(zip(orden_etapas, etapas_upper))

colores_etapas = {
    'PLIEGO':       '#BEE9E8',
    'REV. DOM':     '#A8DADC',
    'PRESUPUESTO':  '#F6E7CB',
    'DOC. PAPEL':   '#F1B963',
    'ORSNA':        '#E29578',
    'ADJUDIC.':     '#B6A8D3',
    'EJECUCIÓN':    '#86C6A4',
    'CAO':          '#5FA8D3',
    'FINALIZADA':   '#1B4965',
    'SIN INICIAR':  '#D3D9DE',
}

# ============================================================
# 3. INSTANCIA POR OBRA
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

    if not link_ariba:
        links_sub = grupo['Link_Ariba'].dropna().astype(str).str.strip()
        links_sub = links_sub[links_sub != '']
        if not links_sub.empty:
            link_ariba = links_sub.iloc[0]

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

    hoy = pd.Timestamp(datetime.now().date())
    if instancia == "FINALIZADA":
        estado = "Completada"
    elif pd.notna(fin) and fin < hoy and avance < 1.0:
        estado = "Crítica"
    else:
        estado = "En Curso"

    resultados.append({
        'ID': n_ome,
        'OBRA': nombre,
        'AERO': aero,
        'INSTANCIA': instancia,
        '% AVANCE': round(avance * 100, 0),
        'ESTADO': estado,
        'INICIO': inicio,
        'VENC.': fin,
        'SAP ARIBA': link_ariba,
    })

df_inst = pd.DataFrame(resultados)

# ============================================================
# 3.5  CUATRIMESTRE (sobre fecha de inicio)
# C1: Ene-Abr · C2: May-Ago · C3: Sep-Dic
# ============================================================
def calcular_cuatrimestre(fecha):
    if pd.isna(fecha):
        return "Sin fecha"
    mes = fecha.month
    if mes <= 4:
        c = "C1"
    elif mes <= 8:
        c = "C2"
    else:
        c = "C3"
    return f"{c} {fecha.year}"

df_inst['CUATRIMESTRE'] = df_inst['INICIO'].apply(calcular_cuatrimestre)

# ============================================================
# 4. SIDEBAR — FILTROS DESPLEGABLES
# ============================================================
st.sidebar.markdown("### FILTROS")

# ---------- AEROPUERTO ----------
aeros = sorted([a for a in df_inst['AERO'].dropna().unique() if str(a).strip()])
opciones_aero = ["Todos"] + aeros
sel_aero = st.sidebar.selectbox("Aeropuerto", opciones_aero, index=0)

# ---------- INSTANCIA ----------
instancias_disp = etapas_upper + ['FINALIZADA', 'SIN INICIAR']
instancias_existentes = [i for i in instancias_disp if i in df_inst['INSTANCIA'].unique()]
opciones_inst = ["Todas"] + instancias_existentes
sel_inst = st.sidebar.selectbox("Instancia", opciones_inst, index=0)

# ---------- CUATRIMESTRE ----------
def sort_key_cuatri(c):
    if c == "Sin fecha":
        return (9999, 9)
    partes = c.split()
    return (int(partes[1]), int(partes[0][1]))

cuatris = sorted(df_inst['CUATRIMESTRE'].unique(), key=sort_key_cuatri)
opciones_cuatri = ["Todos"] + cuatris
sel_cuatri = st.sidebar.selectbox("Cuatrimestre", opciones_cuatri, index=0)

# ---------- EXTRAS ----------
st.sidebar.markdown("---")
META_FINALIZADAS = st.sidebar.slider("Meta % finalizadas", 0, 100, 85)
solo_con_link = st.sidebar.checkbox("Solo obras con SAP Ariba", value=False)

# ---------- APLICAMOS FILTROS ----------
df_f = df_inst.copy()

if sel_aero != "Todos":
    df_f = df_f[df_f['AERO'] == sel_aero]
if sel_inst != "Todas":
    df_f = df_f[df_f['INSTANCIA'] == sel_inst]
if sel_cuatri != "Todos":
    df_f = df_f[df_f['CUATRIMESTRE'] == sel_cuatri]
if solo_con_link:
    df_f = df_f[df_f['SAP ARIBA'].str.len() > 0]

# ============================================================
# 5. HEADER
# ============================================================
fecha_actual = datetime.now().strftime("%d/%m/%Y · %H:%M")
st.markdown(f"""
<div class="header-bar">
    <div>
        <div class="header-title">✈ TABLERO DE CONTROL · OBRAS MENORES (OMEs)</div>
        <div class="header-sub">Gerencia de Mantenimiento · Aeropuertos Argentina</div>
    </div>
    <div class="header-right">
        <b>GESTOR DE PROYECTOS</b><br>
        Actualizado: {fecha_actual}
    </div>
</div>
""", unsafe_allow_html=True)

# ============================================================
# 6. KPIs COMPACTOS
# ============================================================
total = len(df_f)
activas = int((df_f['ESTADO'] == 'En Curso').sum())
atrasadas = int((df_f['ESTADO'] == 'Crítica').sum())
finalizadas = int((df_f['ESTADO'] == 'Completada').sum())
pct_finalizadas = (finalizadas / total * 100) if total else 0
con_link = int((df_f['SAP ARIBA'].str.len() > 0).sum())

k1, k2, k3, k4, k5 = st.columns(5)
with k1:
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-title">Total OMEs</div>
    <div class="kpi-value">{total}</div></div>""", unsafe_allow_html=True)
with k2:
    st.markdown(f"""<div class="kpi-card">
    <div class="kpi-title">En Curso</div>
    <div class="kpi-value">{activas}</div></div>""", unsafe_allow_html=True)
with k3:
    st.markdown(f"""<div class="kpi-card ok">
    <div class="kpi-title">Finalizadas</div>
    <div class="kpi-value ok">{finalizadas}</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card alert">
    <div class="kpi-title">Críticas</div>
    <div class="kpi-value alert">{atrasadas}</div></div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card warn">
    <div class="kpi-title">Con SAP Ariba</div>
    <div class="kpi-value">{con_link}</div></div>""", unsafe_allow_html=True)

st.write("")

# ============================================================
# 7. GRÁFICOS (donut + barras)
# ============================================================
g1, g2 = st.columns([1, 2.5])

with g1:
    st.markdown('<div class="panel-title">Cumplimiento de Meta</div>', unsafe_allow_html=True)
    fig_donut = go.Figure(go.Pie(
        values=[pct_finalizadas, max(0, 100 - pct_finalizadas)],
        hole=0.78,
        marker=dict(colors=['#5FA8D3', '#EDF2F4'], line=dict(color='white', width=2)),
        textinfo='none', sort=False,
    ))
    fig_donut.update_layout(
        showlegend=False,
        margin=dict(l=0, r=0, t=0, b=0),
        height=210,
        paper_bgcolor='white',
        annotations=[
            dict(text=f"<b style='font-size:26px;color:#1B4965'>{pct_finalizadas:.0f}%</b>"
                      f"<br><span style='font-size:9px;color:#6B7C93;letter-spacing:1.5px'>FINALIZADAS</span>"
                      f"<br><span style='font-size:9px;color:#86C6A4'>Meta {META_FINALIZADAS}%</span>",
                 x=0.5, y=0.5, showarrow=False),
        ],
    )
    st.plotly_chart(fig_donut, use_container_width=True, config={'displayModeBar': False})

with g2:
    st.markdown('<div class="panel-title">Obras por Instancia</div>', unsafe_allow_html=True)
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
    fig_bar.update_traces(
        textposition='outside',
        textfont=dict(size=11, color='#1B4965', family='Segoe UI'),
        marker_line_width=0,
    )
    fig_bar.update_layout(
        showlegend=False,
        margin=dict(l=10, r=10, t=10, b=10),
        height=210,
        plot_bgcolor='white',
        paper_bgcolor='white',
        yaxis=dict(title=None, gridcolor='#EDF2F4', tickfont=dict(color='#6B7C93', size=10)),
        xaxis=dict(title=None, tickfont=dict(color='#1B4965', size=10), tickangle=-15),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ============================================================
# 8. LISTADO DETALLADO
# ============================================================
st.markdown('<div class="panel-title">Listado Detallado de OMEs</div>', unsafe_allow_html=True)

def fmt_estado(s):
    if s == "Completada": return "● Completada"
    if s == "En Curso":   return "● En Curso"
    if s == "Crítica":    return "● Crítica"
    return s

df_show = df_f.copy()
df_show['ESTADO'] = df_show['ESTADO'].map(fmt_estado)
df_show['INICIO'] = df_show['INICIO'].dt.strftime('%d/%m/%y').fillna('—')
df_show['VENC.']  = df_show['VENC.'].dt.strftime('%d/%m/%y').fillna('—')

cols_order = ['ID', 'OBRA', 'AERO', 'INSTANCIA', 'CUATRIMESTRE',
              '% AVANCE', 'ESTADO', 'INICIO', 'VENC.', 'SAP ARIBA']
df_show = df_show[cols_order]

st.dataframe(
    df_show,
    use_container_width=True,
    hide_index=True,
    height=230,
    column_config={
        "% AVANCE": st.column_config.ProgressColumn(
            "% AVANCE", format="%d%%", min_value=0, max_value=100,
        ),
        "ID": st.column_config.TextColumn(width="small"),
        "OBRA": st.column_config.TextColumn(width="large"),
        "AERO": st.column_config.TextColumn(width="small"),
        "INSTANCIA": st.column_config.TextColumn(width="medium"),
        "CUATRIMESTRE": st.column_config.TextColumn(width="small"),
        "ESTADO": st.column_config.TextColumn(width="small"),
        "INICIO": st.column_config.TextColumn(width="small"),
        "VENC.": st.column_config.TextColumn(width="small"),
        "SAP ARIBA": st.column_config.LinkColumn(
            "SAP ARIBA",
            help="Abrir la obra en SAP Ariba",
            display_text="Abrir ›",
            width="small",
        ),
    },
)
