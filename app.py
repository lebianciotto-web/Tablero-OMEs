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
    html, body, [class*="css"] { font-family: 'Segoe UI', 'Inter', sans-serif; }
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
        padding: 10px 22px; border-radius: 10px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 2px 8px rgba(27,73,101,0.18);
        margin-bottom: 10px; color: white;
    }
    .header-title { font-size: 18px; font-weight: 700; letter-spacing: 1.2px; color: white; }
    .header-sub   { font-size: 11px; color: #BEE9E8; letter-spacing: 0.5px; text-transform: uppercase; }
    .header-right { text-align: right; font-size: 11px; color: #BEE9E8; letter-spacing: 0.5px; }
    .header-right b { color: white; font-size: 13px; letter-spacing: 1px; }

    .kpi-card {
        background: white; padding: 10px 14px; border-radius: 10px;
        box-shadow: 0 1px 4px rgba(27,73,101,0.08);
        border-left: 4px solid #5FA8D3; height: 70px;
        display: flex; flex-direction: column; justify-content: center;
    }
    .kpi-card.alert  { border-left-color: #E29578; }
    .kpi-card.ok     { border-left-color: #86C6A4; }
    .kpi-card.warn   { border-left-color: #F1B963; }
    .kpi-title { font-size: 10px; color: #6B7C93; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }
    .kpi-value { font-size: 26px; font-weight: 700; color: #1B4965; line-height: 1.1; margin-top: 2px; }
    .kpi-value.alert { color: #C75D44; }
    .kpi-value.ok    { color: #4F9D75; }

    .panel-title {
        font-size: 11px; font-weight: 700; color: #1B4965; letter-spacing: 1.2px;
        text-transform: uppercase; border-bottom: 1px solid #EDF2F4;
        padding-bottom: 4px; margin-bottom: 6px; margin-top: 8px;
    }

    section[data-testid="stSidebar"] { background: #1B4965; }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {
        color: #BEE9E8 !important;
        font-size: 12px !important;
        letter-spacing: 1.2px;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {
        background-color: white !important;
        border: 1px solid #5FA8D3 !important;
        border-radius: 6px !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-baseweb="select"] input {
        color: #1B4965 !important;
        font-weight: 600 !important;
    }
    section[data-testid="stSidebar"] div[data-baseweb="select"] svg {
        fill: #1B4965 !important;
    }
    section[data-testid="stSidebar"] [data-testid="stTickBar"] * { color: #BEE9E8 !important; }

    [data-testid="stDataFrame"] { border-radius: 8px; overflow: hidden; }
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

    if df.shape[1] > 6:
        nombre_col_g = df.columns[6]
        df.rename(columns={nombre_col_g: 'Cuatrimestre'}, inplace=True)
    else:
        df['Cuatrimestre'] = ''

    if df.shape[1] > 11:
        nombre_col_l = df.columns[11]
        df.rename(columns={nombre_col_l: 'Link_Ariba'}, inplace=True)
    else:
        df['Link_Ariba'] = ''

    df['Link_Ariba'] = (
        df['Link_Ariba'].astype(str).str.strip()
        .replace({'nan': '', 'None': '', 'NaT': ''})
    )
    df['Cuatrimestre'] = (
        df['Cuatrimestre'].astype(str).str.strip()
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

# ============================================================
# 3. DEFINICIÓN DE ETAPAS — MATCHING POR KEYWORDS
# ============================================================
# Cada etapa se identifica por keywords flexibles en el nombre.
# Esto resuelve casos como "Aprobación ORSNA", "Presentación a ORSNA",
# "Rev. DOM", "Revisión por DOM", "Documentación papel", etc.
# ============================================================
etapas_def = [
    # (clave_interna, etiqueta_corta, lista_de_keywords_que_deben_estar_todos)
    ('Pliego',                 'PLIEGO',       [['pliego']]),
    ('Revisión DOM',           'REV. DOM',     [['revisi', 'dom'], ['rev', 'dom']]),
    ('Presupuesto',            'PRESUPUESTO',  [['presup']]),
    ('Documentación en papel', 'DOC. PAPEL',   [['document', 'papel'], ['doc', 'papel']]),
    ('ORSNA',                  'ORSNA',        [['orsna']]),
    ('Adjudicación',           'ADJUDIC.',     [['adjudic']]),
    ('Ejecución',              'EJECUCIÓN',    [['ejecuc']]),
    ('CAO presentado',         'CAO',          [['cao']]),
]

orden_etapas = [e[0] for e in etapas_def]
etapas_upper = [e[1] for e in etapas_def]
mapa_upper   = dict(zip(orden_etapas, etapas_upper))

colores_etapas = {
    'PLIEGO':       '#BEE9E8',
    'REV. DOM':     '#A8DADC',
    'PRESUPUESTO':  '#F6E7CB',
    'DOC. PAPEL':   '#F1B963',
    'ORSNA':        '#E29578',
    'ADJUDIC.':     '#B6A8D3',
    'EJECUCIÓN':    '#86C6A4',
    'CAO':          '#5FA8D3',
    'FINALIZADAS':  '#1B4965',
    'SIN INICIAR':  '#D3D9DE',
}

def matchea_etapa(nombre_norm, sets_keywords):
    """Devuelve True si el nombre normalizado matchea alguno de los sets de keywords."""
    for kw_set in sets_keywords:
        if all(kw in nombre_norm for kw in kw_set):
            return True
    return False

# ============================================================
# 4. CÁLCULO DE INSTANCIA POR OBRA
#  Regla: PRIMERA etapa con pct < 100% (estricto, sin tolerancia de negocio)
# ============================================================
TOL = 1e-6   # solo para imprecisiones de float

resultados = []
debug_rows = []  # 👁️ para panel diagnóstico

for obra_id, grupo in df.groupby('Obra_ID'):
    fila = grupo[grupo['Es_Principal']].iloc[0]
    nombre = fila['Nombre']
    aero   = fila.get('Aero', '')
    n_ome  = fila.get('N° OME', '')
    avance = fila.get('% completado', 0)
    inicio = fila.get('Comienzo', pd.NaT)
    fin    = fila.get('Finalización', pd.NaT)
    cuatri = str(fila.get('Cuatrimestre', '')).strip()
    link_ariba = str(fila.get('Link_Ariba', '')).strip()

    if not cuatri:
        c_sub = grupo['Cuatrimestre'].astype(str).str.strip()
        c_sub = c_sub[c_sub != '']
        if not c_sub.empty:
            cuatri = c_sub.iloc[0]

    if not link_ariba:
        links_sub = grupo['Link_Ariba'].dropna().astype(str).str.strip()
        links_sub = links_sub[links_sub != '']
        if not links_sub.empty:
            link_ariba = links_sub.iloc[0]
    if link_ariba and not link_ariba.lower().startswith(('http://', 'https://')):
        link_ariba = ''

    # Sub-tareas
    sub = grupo[~grupo['Es_Principal']].copy()
    sub['Nombre_norm'] = sub['Nombre'].astype(str).str.strip().str.lower()

    # ---------- MATCH POR KEYWORDS ----------
    etapas_pct = []
    for etapa_clave, _, kw_sets in etapas_def:
        # Buscamos cualquier sub-tarea que matchee los keywords
        mask = sub['Nombre_norm'].apply(lambda s: matchea_etapa(s, kw_sets))
        m = sub[mask]
        if not m.empty:
            # Si hay varias coincidencias tomamos la de MAYOR % completado
            pct = float(m['% completado'].max())
            etapas_pct.append((etapa_clave, pct))

    # ---------- Métricas individuales ----------
    pct_ejecucion = next((p for e, p in etapas_pct if e == 'Ejecución'), 0)
    pct_cao       = next((p for e, p in etapas_pct if e == 'CAO presentado'), 0)
    ejecucion_full = pct_ejecucion >= 1.0 - TOL
    cao_full       = pct_cao       >= 1.0 - TOL

    # ---------- Determinar instancia ----------
    instancia = "SIN INICIAR"
    if etapas_pct:
        if cao_full:
            instancia = "FINALIZADAS"
        elif all(p <= TOL for _, p in etapas_pct):
            instancia = "SIN INICIAR"
        else:
            primera_incompleta = next(
                (e for e, p in etapas_pct if p < 1.0 - TOL),
                None
            )
            if primera_incompleta:
                instancia = mapa_upper[primera_incompleta]
            else:
                instancia = "FINALIZADAS"

    # ---------- Estado ----------
    hoy = pd.Timestamp(datetime.now().date())
    if instancia == "FINALIZADAS":
        estado = "Completada"
    elif pd.notna(fin) and fin < hoy and avance < 1.0 - TOL:
        estado = "Crítica"
    else:
        estado = "En Curso"

    # ---------- Cuatrimestre ----------
    if cuatri in ('1', '2', '3'):
        cuatri_fmt = f"C{cuatri}"
    elif cuatri:
        cuatri_fmt = cuatri
    else:
        cuatri_fmt = "Sin dato"

    resultados.append({
        'ID': n_ome,
        'OBRA': nombre,
        'AERO': aero,
        'INSTANCIA': instancia,
        'CUATRIMESTRE': cuatri_fmt,
        '% AVANCE': round(avance * 100, 0),
        'ESTADO': estado,
        'INICIO': inicio,
        'VENC.': fin,
        'SAP ARIBA': link_ariba,
        '_EJECUCION_FULL': ejecucion_full,
        '_CAO_FULL': cao_full,
    })

    # ---------- Diagnóstico ----------
    debug_rows.append({
        'OBRA': nombre,
        'AERO': aero,
        'Sub-tareas en CSV': " | ".join(sub['Nombre'].astype(str).tolist()),
        'Etapas detectadas (pct)': " | ".join([f"{e}={p*100:.0f}%" for e, p in etapas_pct]),
        'Instancia asignada': instancia,
    })

df_inst = pd.DataFrame(resultados)
df_debug = pd.DataFrame(debug_rows)

# ============================================================
# 5. SIDEBAR — FILTROS
# ============================================================
st.sidebar.markdown("### FILTROS")

aeros = sorted([a for a in df_inst['AERO'].dropna().unique() if str(a).strip()])
sel_aero = st.sidebar.selectbox("Aeropuerto", ["Todos"] + aeros, index=0)

instancias_disp = etapas_upper + ['FINALIZADAS', 'SIN INICIAR']
instancias_existentes = [i for i in instancias_disp if i in df_inst['INSTANCIA'].unique()]
sel_inst = st.sidebar.selectbox("Instancia", ["Todas"] + instancias_existentes, index=0)

def sort_key_cuatri(c):
    if c == "Sin dato": return 99
    if c.startswith("C") and len(c) >= 2 and c[1].isdigit(): return int(c[1])
    return 50

cuatris = sorted(df_inst['CUATRIMESTRE'].unique(), key=sort_key_cuatri)
sel_cuatri = st.sidebar.selectbox("Cuatrimestre", ["Todos"] + list(cuatris), index=0)

st.sidebar.markdown("---")
META_FINALIZADAS = st.sidebar.slider("Meta % finalizadas", 0, 100, 85)
META_EJECUTADAS  = st.sidebar.slider("Meta % ejecutadas", 0, 100, 80)

st.sidebar.markdown("---")
modo_debug = st.sidebar.checkbox("🔍 Mostrar diagnóstico", value=False)

df_f = df_inst.copy()
if sel_aero   != "Todos": df_f = df_f[df_f['AERO'] == sel_aero]
if sel_inst   != "Todas": df_f = df_f[df_f['INSTANCIA'] == sel_inst]
if sel_cuatri != "Todos": df_f = df_f[df_f['CUATRIMESTRE'] == sel_cuatri]

# ============================================================
# 6. HEADER
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
# 7. KPIs
# ============================================================
total = len(df_f)
activas = int((df_f['ESTADO'] == 'En Curso').sum())
atrasadas = int((df_f['ESTADO'] == 'Crítica').sum())
finalizadas = int(df_f['_CAO_FULL'].sum())
ejecutadas  = int(df_f['_EJECUCION_FULL'].sum())
pct_finalizadas = (finalizadas / total * 100) if total else 0
pct_ejecutadas  = (ejecutadas  / total * 100) if total else 0

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
    <div class="kpi-title">Ejecutadas</div>
    <div class="kpi-value ok">{ejecutadas}</div></div>""", unsafe_allow_html=True)
with k4:
    st.markdown(f"""<div class="kpi-card ok">
    <div class="kpi-title">Finalizadas</div>
    <div class="kpi-value ok">{finalizadas}</div></div>""", unsafe_allow_html=True)
with k5:
    st.markdown(f"""<div class="kpi-card alert">
    <div class="kpi-title">Críticas</div>
    <div class="kpi-value alert">{atrasadas}</div></div>""", unsafe_allow_html=True)

st.write("")

# ============================================================
# 8. GRÁFICOS — 2 DONUTS + BARRAS
# ============================================================
g1, g2, g3 = st.columns([1, 1, 2.5])

def donut(pct, label, meta, color):
    fig = go.Figure(go.Pie(
        values=[pct, max(0, 100 - pct)],
        hole=0.78,
        marker=dict(colors=[color, '#EDF2F4'], line=dict(color='white', width=2)),
        textinfo='none', sort=False,
    ))
    fig.update_layout(
        showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
        height=210, paper_bgcolor='white',
        annotations=[
            dict(text=f"<b style='font-size:26px;color:#1B4965'>{pct:.0f}%</b>"
                      f"<br><span style='font-size:9px;color:#6B7C93;letter-spacing:1.5px'>{label}</span>"
                      f"<br><span style='font-size:9px;color:#86C6A4'>Meta {meta}%</span>",
                 x=0.5, y=0.5, showarrow=False),
        ],
    )
    return fig

with g1:
    st.markdown('<div class="panel-title">Finalizadas (CAO 100%)</div>', unsafe_allow_html=True)
    st.plotly_chart(donut(pct_finalizadas, 'FINALIZADAS', META_FINALIZADAS, '#1B4965'),
                    use_container_width=True, config={'displayModeBar': False})

with g2:
    st.markdown('<div class="panel-title">Ejecutadas (Ejecución 100%)</div>', unsafe_allow_html=True)
    st.plotly_chart(donut(pct_ejecutadas, 'EJECUTADAS', META_EJECUTADAS, '#86C6A4'),
                    use_container_width=True, config={'displayModeBar': False})

with g3:
    st.markdown('<div class="panel-title">Obras por Instancia</div>', unsafe_allow_html=True)
    conteo_dict = df_f['INSTANCIA'].value_counts().to_dict()
    conteo_dict['FINALIZADAS'] = int(df_f['_CAO_FULL'].sum())
    etapas_para_grafico = etapas_upper + ['FINALIZADAS']
    conteo = pd.DataFrame({
        'Etapa': etapas_para_grafico,
        'Cantidad': [conteo_dict.get(e, 0) for e in etapas_para_grafico]
    })
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
        showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
        height=210, plot_bgcolor='white', paper_bgcolor='white',
        yaxis=dict(title=None, gridcolor='#EDF2F4', tickfont=dict(color='#6B7C93', size=10)),
        xaxis=dict(title=None, tickfont=dict(color='#1B4965', size=10), tickangle=-15),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ============================================================
# 9. LISTADO DETALLADO
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
    df_show, use_container_width=True, hide_index=True, height=230,
    column_config={
        "% AVANCE": st.column_config.ProgressColumn("% AVANCE", format="%d%%", min_value=0, max_value=100),
        "ID": st.column_config.TextColumn(width="small"),
        "OBRA": st.column_config.TextColumn(width="large"),
        "AERO": st.column_config.TextColumn(width="small"),
        "INSTANCIA": st.column_config.TextColumn(width="medium"),
        "CUATRIMESTRE": st.column_config.TextColumn(width="small"),
        "ESTADO": st.column_config.TextColumn(width="small"),
        "INICIO": st.column_config.TextColumn(width="small"),
        "VENC.": st.column_config.TextColumn(width="small"),
        "SAP ARIBA": st.column_config.LinkColumn(
            "SAP ARIBA", help="Abrir la obra en SAP Ariba",
            display_text="Abrir ›", width="small",
        ),
    },
)

# ============================================================
# 10. PANEL DE DIAGNÓSTICO (sólo si está activado)
# ============================================================
if modo_debug:
    st.markdown('<div class="panel-title">🔍 Diagnóstico de detección de etapas</div>', unsafe_allow_html=True)
    st.caption("Cómo está leyendo el código las sub-tareas de cada obra. "
               "Si una etapa no aparece en 'Etapas detectadas', hay que ajustar el keyword en el código.")
    st.dataframe(df_debug, use_container_width=True, hide_index=True, height=320)
