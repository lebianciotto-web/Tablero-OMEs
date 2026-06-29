import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from io import BytesIO

# ============================================================
# CONFIGURACIÓN
# ============================================================
st.set_page_config(
    layout="wide",
    page_title="Tablero OMEs · Aeropuertos Argentina",
    page_icon="✈",
)

# ============================================================
# QUERY PARAMS (debug)
# ============================================================
try:
    qp = st.query_params
    DEBUG_MODE = qp.get("debug", "0") == "1"
except Exception:
    qp = st.experimental_get_query_params()
    DEBUG_MODE = qp.get("debug", ["0"])[0] == "1"

# ============================================================
# PALETA CORPORATIVA — AEROPUERTOS ARGENTINA
# ============================================================
COLOR_TEAL    = "#2A8C9F"
COLOR_TEAL_D  = "#1E6975"
COLOR_TEAL_L  = "#A6D9E0"
COLOR_GREEN   = "#95C93D"
COLOR_GREEN_D = "#6FA02A"
COLOR_GREEN_L = "#D5EBA8"
COLOR_GRAY    = "#7C8388"
COLOR_GRAY_L  = "#D6D9DB"
COLOR_GRAY_BG = "#F2F4F5"
COLOR_ALERT   = "#E07856"
COLOR_WARN    = "#E8B847"
COLOR_WHITE   = "#FFFFFF"

# ============================================================
# ESTILOS
# ============================================================
st.markdown(f"""
<style>
    html, body, [class*="css"] {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 14px;
    }}
    .stApp {{
        background-color: {COLOR_GRAY_BG};
        background-image:
            linear-gradient(135deg, rgba(42,140,159,0.04) 25%, transparent 25%),
            linear-gradient(225deg, rgba(149,201,61,0.04) 25%, transparent 25%),
            linear-gradient(45deg,  rgba(124,131,136,0.04) 25%, transparent 25%),
            linear-gradient(315deg, rgba(42,140,159,0.04) 25%, transparent 25%);
        background-size: 80px 80px;
        background-position: 0 0, 40px 0, 40px 40px, 0 40px;
    }}
    .block-container {{
        padding-top: 0.8rem !important;
        padding-bottom: 0.5rem !important;
        padding-left: 1.5rem !important;
        padding-right: 1.5rem !important;
        max-width: 100% !important;
    }}
    header[data-testid="stHeader"] {{ background: transparent; height: 0; }}
    #MainMenu, footer {{ visibility: hidden; }}

    .header-bar {{
        background: linear-gradient(100deg, {COLOR_TEAL_D} 0%, {COLOR_TEAL} 60%, {COLOR_GREEN_D} 100%);
        padding: 14px 26px; border-radius: 12px;
        display: flex; justify-content: space-between; align-items: center;
        box-shadow: 0 4px 12px rgba(30,105,117,0.25);
        margin-bottom: 12px; color: white;
        position: relative; overflow: hidden;
    }}
    .header-bar::before {{
        content: ""; position: absolute;
        right: -20px; top: -20px;
        width: 160px; height: 160px;
        background: rgba(255,255,255,0.08);
        border-radius: 50%;
    }}
    .header-bar::after {{
        content: ""; position: absolute;
        right: 60px; top: 30px;
        width: 80px; height: 80px;
        border: 3px solid rgba(255,255,255,0.15);
        border-radius: 50%;
    }}
    .header-title {{ font-size: 22px; font-weight: 700; letter-spacing: 1.5px; color: white; position: relative; z-index: 1;}}
    .header-sub   {{ font-size: 13px; color: {COLOR_GREEN_L}; letter-spacing: 0.5px; text-transform: uppercase; position: relative; z-index: 1;}}
    .header-right {{ text-align: right; font-size: 13px; color: {COLOR_TEAL_L}; letter-spacing: 0.5px; position: relative; z-index: 1;}}
    .header-right b {{ color: white; font-size: 15px; letter-spacing: 1px; }}

    .kpi-card {{
        background: white; padding: 12px 16px; border-radius: 10px;
        box-shadow: 0 2px 6px rgba(30,105,117,0.10);
        border-left: 4px solid {COLOR_TEAL}; height: 82px;
        display: flex; flex-direction: column; justify-content: center;
    }}
    .kpi-card.alert  {{ border-left-color: {COLOR_ALERT}; }}
    .kpi-card.ok     {{ border-left-color: {COLOR_GREEN}; }}
    .kpi-card.warn   {{ border-left-color: {COLOR_WARN}; }}
    .kpi-card.gold   {{ border-left-color: {COLOR_GREEN_D}; }}
    .kpi-title {{ font-size: 12px; color: {COLOR_GRAY}; font-weight: 600; letter-spacing: 1px; text-transform: uppercase; }}
    .kpi-value {{ font-size: 30px; font-weight: 700; color: {COLOR_TEAL_D}; line-height: 1.1; margin-top: 4px; }}
    .kpi-value.alert {{ color: {COLOR_ALERT}; }}
    .kpi-value.ok    {{ color: {COLOR_GREEN_D}; }}
    .kpi-value.warn  {{ color: #B88820; }}
    .kpi-value.gold  {{ color: {COLOR_GREEN_D}; }}
    .kpi-sub {{ font-size: 11px; color: {COLOR_GRAY}; margin-top: 2px; }}

    .panel-title {{
        font-size: 13px; font-weight: 700; color: {COLOR_TEAL_D}; letter-spacing: 1.2px;
        text-transform: uppercase; border-bottom: 2px solid {COLOR_GREEN};
        padding-bottom: 5px; margin-bottom: 8px; margin-top: 14px;
        display: inline-block;
    }}

    section[data-testid="stSidebar"] {{
        background: linear-gradient(180deg, {COLOR_TEAL_D} 0%, {COLOR_TEAL} 100%);
    }}
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3,
    section[data-testid="stSidebar"] label,
    section[data-testid="stSidebar"] p {{
        color: {COLOR_GREEN_L} !important;
        font-size: 13px !important;
        letter-spacing: 1.2px;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] > div {{
        background-color: white !important;
        border: 1px solid {COLOR_GREEN} !important;
        border-radius: 6px !important;
        min-height: 38px !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] span,
    section[data-testid="stSidebar"] div[data-baseweb="select"] input,
    section[data-testid="stSidebar"] div[data-baseweb="tag"] {{
        color: {COLOR_TEAL_D} !important;
        font-weight: 600 !important;
        font-size: 13px !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="tag"] {{
        background-color: {COLOR_GREEN_L} !important;
    }}
    section[data-testid="stSidebar"] div[data-baseweb="select"] svg {{
        fill: {COLOR_TEAL_D} !important;
    }}
    section[data-testid="stSidebar"] [data-testid="stTickBar"] * {{ color: {COLOR_GREEN_L} !important; }}

    [data-testid="stDataFrame"] {{
        border-radius: 8px; overflow: hidden;
        font-size: 14px !important;
    }}

    div[data-testid="stDownloadButton"] button {{
        background: linear-gradient(90deg, {COLOR_TEAL}, {COLOR_GREEN_D}) !important;
        color: white !important;
        border: none !important;
        border-radius: 6px !important;
        padding: 8px 16px !important;
        font-weight: 600 !important;
        font-size: 13px !important;
        box-shadow: 0 2px 4px rgba(30,105,117,0.2);
    }}
    div[data-testid="stDownloadButton"] button:hover {{
        background: linear-gradient(90deg, {COLOR_TEAL_D}, {COLOR_GREEN}) !important;
    }}
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
        col_g = df.columns[6]
        df.rename(columns={col_g: 'Cuatrimestre'}, inplace=True)
    else:
        df['Cuatrimestre'] = ''

    if df.shape[1] > 11:
        col_l = df.columns[11]
        df.rename(columns={col_l: 'Link_Ariba'}, inplace=True)
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

etapas_def = [
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
    'PLIEGO':       '#C9E7EC',
    'REV. DOM':     '#A6D9E0',
    'PRESUPUESTO':  '#7CC3CE',
    'DOC. PAPEL':   '#52ADBC',
    'ORSNA':        COLOR_TEAL,
    'ADJUDIC.':     '#5BAA73',
    'EJECUCIÓN':    COLOR_GREEN,
    'CAO':          COLOR_GREEN_D,
    'FINALIZADAS':  COLOR_TEAL_D,
    'SIN INICIAR':  COLOR_GRAY_L,
}

def matchea_etapa(nombre_norm, sets_keywords):
    for kw_set in sets_keywords:
        if all(kw in nombre_norm for kw in kw_set):
            return True
    return False

# ============================================================
# 3. CÁLCULO DE INSTANCIA POR OBRA
# ============================================================
TOL = 1e-6
hoy = pd.Timestamp(datetime.now().date())

resultados = []
debug_rows = []

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

    sub = grupo[~grupo['Es_Principal']].copy()
    sub['Nombre_norm'] = sub['Nombre'].astype(str).str.strip().str.lower()

    etapas_pct = []
    for etapa_clave, _, kw_sets in etapas_def:
        mask = sub['Nombre_norm'].apply(lambda s: matchea_etapa(s, kw_sets))
        m = sub[mask]
        if not m.empty:
            pct = float(m['% completado'].max())
            etapas_pct.append((etapa_clave, pct))

    pct_ejecucion = next((p for e, p in etapas_pct if e == 'Ejecución'), 0)
    pct_cao       = next((p for e, p in etapas_pct if e == 'CAO presentado'), 0)
    ejecucion_full = pct_ejecucion >= 1.0 - TOL
    cao_full       = pct_cao       >= 1.0 - TOL

    instancia = "SIN INICIAR"
    if etapas_pct:
        if cao_full:
            instancia = "FINALIZADAS"
        elif all(p <= TOL for _, p in etapas_pct):
            instancia = "SIN INICIAR"
        else:
            primera_incompleta = next((e for e, p in etapas_pct if p < 1.0 - TOL), None)
            instancia = mapa_upper[primera_incompleta] if primera_incompleta else "FINALIZADAS"

    dias_rest = (fin - hoy).days if pd.notna(fin) else None

    if instancia == "FINALIZADAS":
        estado = "Completada"
    elif dias_rest is not None and dias_rest < 0 and avance < 1.0 - TOL:
        estado = "Crítica"
    elif dias_rest is not None and 0 <= dias_rest <= 30 and avance < 1.0 - TOL:
        estado = "Por vencer"
    else:
        estado = "En Curso"

    if cuatri in ('1', '2', '3'):
        cuatri_fmt = f"C{cuatri}"
    elif cuatri:
        cuatri_fmt = cuatri
    else:
        cuatri_fmt = "Sin dato"

    resultados.append({
        'ID': n_ome, 'OBRA': nombre, 'AERO': aero,
        'INSTANCIA': instancia, 'CUATRIMESTRE': cuatri_fmt,
        '% AVANCE': round(avance * 100, 0), 'ESTADO': estado,
        'INICIO': inicio, 'VENC.': fin, 'DÍAS REST.': dias_rest,
        'SAP ARIBA': link_ariba,
        '_EJECUCION_FULL': ejecucion_full, '_CAO_FULL': cao_full,
    })
    debug_rows.append({
        'OBRA': nombre, 'AERO': aero,
        'Sub-tareas en CSV': " | ".join(sub['Nombre'].astype(str).tolist()),
        'Etapas detectadas (pct)': " | ".join([f"{e}={p*100:.0f}%" for e, p in etapas_pct]),
        'Instancia asignada': instancia,
    })

df_inst = pd.DataFrame(resultados)
df_debug = pd.DataFrame(debug_rows)

# ============================================================
# 4. SIDEBAR
# ============================================================
st.sidebar.markdown("### FILTROS")

def multi_filter(label, options, key):
    sel = st.sidebar.multiselect(
        label, options, default=[],
        placeholder="Todos", key=key,
    )
    return sel if sel else options

aeros = sorted([a for a in df_inst['AERO'].dropna().unique() if str(a).strip()])
sel_aero = multi_filter("Aeropuerto", aeros, "f_aero")

instancias_disp = etapas_upper + ['FINALIZADAS', 'SIN INICIAR']
instancias_existentes = [i for i in instancias_disp if i in df_inst['INSTANCIA'].unique()]
sel_inst = multi_filter("Instancia", instancias_existentes, "f_inst")

def sort_key_cuatri(c):
    if c == "Sin dato":
        return 99
    if c.startswith("C") and len(c) >= 2 and c[1].isdigit():
        return int(c[1])
    return 50

cuatris = sorted(df_inst['CUATRIMESTRE'].unique(), key=sort_key_cuatri)
sel_cuatri = multi_filter("Cuatrimestre", cuatris, "f_cuatri")

st.sidebar.markdown("---")
META_FINALIZADAS = st.sidebar.slider("Meta % finalizadas", 0, 100, 85)
META_EJECUTADAS  = st.sidebar.slider("Meta % ejecutadas", 0, 100, 80)

st.sidebar.markdown("---")
auto_refresh = st.sidebar.checkbox("🔄 Auto-refresh (cada 5 min)", value=False)
if auto_refresh:
    try:
        from streamlit_autorefresh import st_autorefresh
        st_autorefresh(interval=5 * 60 * 1000, key="auto_ref")
    except ImportError:
        st.sidebar.caption("⚠ Instalá `streamlit-autorefresh`.")

df_f = df_inst[
    df_inst['AERO'].isin(sel_aero) &
    df_inst['INSTANCIA'].isin(sel_inst) &
    df_inst['CUATRIMESTRE'].isin(sel_cuatri)
].copy()

# ============================================================
# 5. HEADER + EXPORT
# ============================================================
fecha_actual = datetime.now().strftime("%d/%m/%Y · %H:%M")

col_head, col_dl = st.columns([5, 1])
with col_head:
    st.markdown(f"""
    <div class="header-bar">
        <div>
            <div class="header-title">✈ TABLERO DE CONTROL · OBRAS MENORES (OMEs)</div>
            <div class="header-sub">Aeropuertos Argentina · Gerencia de Mantenimiento</div>
        </div>
        <div class="header-right">
            <b>GESTOR DE PROYECTOS</b><br>
            Actualizado: {fecha_actual}
        </div>
    </div>
    """, unsafe_allow_html=True)

with col_dl:
    st.write("")
    buffer = BytesIO()
    df_export = df_f.drop(columns=['_EJECUCION_FULL', '_CAO_FULL']).copy()
    df_export['INICIO'] = df_export['INICIO'].dt.strftime('%d/%m/%Y')
    df_export['VENC.']  = df_export['VENC.'].dt.strftime('%d/%m/%Y')
    try:
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_export.to_excel(writer, sheet_name='OMEs', index=False)
        excel_data = buffer.getvalue()
        st.download_button(
            label="📥 Exportar a Excel",
            data=excel_data,
            file_name=f"OMEs_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
    except Exception as e:
        st.caption(f"⚠ Excel no disponible ({e}).")

# ============================================================
# 6. KPIs
# ============================================================
total = len(df_f)
activas = int((df_f['ESTADO'] == 'En Curso').sum())
atrasadas = int((df_f['ESTADO'] == 'Crítica').sum())
por_vencer = int((df_f['ESTADO'] == 'Por vencer').sum())
finalizadas = int(df_f['_CAO_FULL'].sum())
ejecutadas  = int(df_f['_EJECUCION_FULL'].sum())
pct_finalizadas = (finalizadas / total * 100) if total else 0
pct_ejecutadas  = (ejecutadas  / total * 100) if total else 0

if total > 0 and not df_f.empty:
    agg_aero = df_f.groupby('AERO').agg(
        total=('ID', 'count'),
        finalizadas=('_CAO_FULL', 'sum'),
    ).reset_index()
    agg_aero['pct'] = agg_aero['finalizadas'] / agg_aero['total'] * 100
    agg_aero = agg_aero.sort_values(['pct', 'total'], ascending=[False, False])
    aero_top = agg_aero.iloc[0]
    aero_top_nombre = aero_top['AERO']
    aero_top_pct = aero_top['pct']
else:
    aero_top_nombre = "—"
    aero_top_pct = 0

k1, k2, k3, k4, k5, k6 = st.columns(6)
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
    st.markdown(f"""<div class="kpi-card warn">
    <div class="kpi-title">Por vencer ≤30d</div>
    <div class="kpi-value warn">{por_vencer}</div></div>""", unsafe_allow_html=True)
with k6:
    st.markdown(f"""<div class="kpi-card alert">
    <div class="kpi-title">Críticas</div>
    <div class="kpi-value alert">{atrasadas}</div></div>""", unsafe_allow_html=True)

st.write("")
ka1, _ = st.columns([1, 5])
with ka1:
    st.markdown(f"""<div class="kpi-card gold">
    <div class="kpi-title">🏆 Aeropuerto Top</div>
    <div class="kpi-value gold">{aero_top_nombre}</div>
    <div class="kpi-sub">{aero_top_pct:.0f}% finalizadas</div>
    </div>""", unsafe_allow_html=True)

st.write("")

# ============================================================
# 7. GRÁFICOS
# ============================================================
g1, g2, g3 = st.columns([1, 1, 2.5])

def donut(pct, label, meta, color):
    fig = go.Figure(go.Pie(
        values=[pct, max(0, 100 - pct)],
        hole=0.78,
        marker=dict(colors=[color, COLOR_GRAY_BG], line=dict(color='white', width=2)),
        textinfo='none', sort=False,
    ))
    fig.update_layout(
        showlegend=False, margin=dict(l=0, r=0, t=0, b=0),
        height=220, paper_bgcolor='white',
        annotations=[
            dict(text=f"<b style='font-size:28px;color:{COLOR_TEAL_D}'>{pct:.0f}%</b>"
                      f"<br><span style='font-size:11px;color:{COLOR_GRAY};letter-spacing:1.5px'>{label}</span>"
                      f"<br><span style='font-size:11px;color:{COLOR_GREEN_D}'>Meta {meta}%</span>",
                 x=0.5, y=0.5, showarrow=False),
        ],
    )
    return fig

with g1:
    st.markdown('<div class="panel-title">Finalizadas (CAO 100%)</div>', unsafe_allow_html=True)
    st.plotly_chart(donut(pct_finalizadas, 'FINALIZADAS', META_FINALIZADAS, COLOR_TEAL),
                    use_container_width=True, config={'displayModeBar': False})
with g2:
    st.markdown('<div class="panel-title">Ejecutadas (Ejecución 100%)</div>', unsafe_allow_html=True)
    st.plotly_chart(donut(pct_ejecutadas, 'EJECUTADAS', META_EJECUTADAS, COLOR_GREEN),
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
        textfont=dict(size=13, color=COLOR_TEAL_D, family='Segoe UI'),
        marker_line_width=0,
    )
    fig_bar.update_layout(
        showlegend=False, margin=dict(l=10, r=10, t=10, b=10),
        height=220, plot_bgcolor='white', paper_bgcolor='white',
        yaxis=dict(title=None, gridcolor=COLOR_GRAY_BG, tickfont=dict(color=COLOR_GRAY, size=12)),
        xaxis=dict(title=None, tickfont=dict(color=COLOR_TEAL_D, size=12), tickangle=-15),
    )
    st.plotly_chart(fig_bar, use_container_width=True, config={'displayModeBar': False})

# ============================================================
# 8. LISTADO DETALLADO
# ============================================================
st.markdown('<div class="panel-title">Listado Detallado de OMEs</div>', unsafe_allow_html=True)

def fmt_estado(s):
    if s == "Completada": return "● Completada"
    if s == "En Curso":   return "● En Curso"
    if s == "Por vencer": return "● Por vencer"
    if s == "Crítica":    return "● Crítica"
    return s

df_show = df_f.copy()
df_show['ESTADO'] = df_show['ESTADO'].map(fmt_estado)
df_show['INICIO'] = df_show['INICIO'].dt.strftime('%d/%m/%y').fillna('—')
df_show['VENC.']  = df_show['VENC.'].dt.strftime('%d/%m/%y').fillna('—')
df_show['DÍAS REST.'] = df_show['DÍAS REST.'].apply(
    lambda d: f"{int(d)}" if pd.notna(d) else "—"
)
cols_order = ['ID', 'OBRA', 'AERO', 'INSTANCIA', 'CUATRIMESTRE',
              '% AVANCE', 'ESTADO', 'INICIO', 'VENC.', 'DÍAS REST.', 'SAP ARIBA']
df_show = df_show[cols_order]

st.dataframe(
    df_show, use_container_width=True, hide_index=True, height=380,
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
        "DÍAS REST.": st.column_config.TextColumn("DÍAS REST.", width="small"),
        "SAP ARIBA": st.column_config.LinkColumn(
            "SAP ARIBA", help="Abrir la obra en SAP Ariba",
            display_text="Abrir ›", width="small",
        ),
    },
)

# ============================================================
# DEBUG
# ============================================================
if DEBUG_MODE:
    st.markdown('<div class="panel-title">🔍 Diagnóstico de detección de etapas</div>', unsafe_allow_html=True)
    st.caption("Modo debug activo. Para ocultarlo, sacá `?debug=1` de la URL.")
    st.dataframe(df_debug, use_container_width=True, hide_index=True, height=320)
