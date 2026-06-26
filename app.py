import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Obras UNE")
st.title("Dashboard de Obras - UNE")

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

    # Forzamos string para detectar el punto en el N° de esquema
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()

    # % completado a numérico (viene con coma decimal)
    df['% completado'] = (
        df['% completado']
        .astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    # Si vinieron como 80 en lugar de 0.8, normalizamos
    if df['% completado'].max() > 1.5:
        df['% completado'] = df['% completado'] / 100.0

    return df

df = cargar_datos()

# ============================================================
# 2. IDENTIFICAR TAREAS PRINCIPALES Y SUB-TAREAS
# ============================================================
df['Es_Principal'] = ~df['Número de esquema'].str.contains(r'\.', regex=True, na=False)
df['Obra_ID'] = df['Es_Principal'].cumsum()

# ============================================================
# 3. ETAPAS DEL FLUJO (en orden)
# ============================================================
orden_etapas = {
    'Pliego':                 'Pliego',
    'Revisión DOM':           'Revisión DOM',
    'Presupuesto':            'Presupuesto',
    'Documentación en papel': 'Documentación en papel',
    'ORSNA':                  'ORSNA',
    'Adjudicación':           'Adjudicación',
    'Ejecución':              'Ejecución',
    'CAO presentado':         'CAO presentado',
}

# ============================================================
# 4. DETECTAR INSTANCIA ACTUAL DE CADA OBRA
# ============================================================
resultados = []

for obra_id, grupo in df.groupby('Obra_ID'):
    fila_principal = grupo[grupo['Es_Principal']].iloc[0]
    nombre_obra = fila_principal['Nombre']
    aero        = fila_principal.get('Aero', '')
    n_ome       = fila_principal.get('N° OME', '')
    avance_obra = fila_principal.get('% completado', 0)

    subtareas = grupo[~grupo['Es_Principal']].copy()
    subtareas['Nombre_norm'] = subtareas['Nombre'].astype(str).str.strip().str.lower()

    instancia_actual = "Finalizada"
    hay_progreso = False

    for etapa_clave in orden_etapas.keys():
        match = subtareas[subtareas['Nombre_norm'] == etapa_clave.lower()]
        if match.empty:
            continue
        pct = match['% completado'].iloc[0]
        if pct > 0:
            hay_progreso = True
        if pct < 1.0:
            instancia_actual = orden_etapas[etapa_clave]
            break

    if not hay_progreso:
        instancia_actual = "Sin iniciar"

    resultados.append({
        'N° OME':    n_ome,
        'Aero':      aero,
        'Obra':      nombre_obra,
        '% Avance':  round(avance_obra * 100, 1) if avance_obra <= 1 else round(avance_obra, 1),
        'Instancia': instancia_actual,
    })

df_inst = pd.DataFrame(resultados)

# ============================================================
# 5. FILTROS LATERALES
# ============================================================
st.sidebar.header("Filtros")
aeros = sorted([a for a in df_inst['Aero'].dropna().unique() if str(a).strip() != ''])
sel_aero = st.sidebar.multiselect("Aeropuerto (Aero)", aeros, default=aeros)

etapas_disp = list(orden_etapas.values()) + ['Finalizada', 'Sin iniciar']
sel_etapa = st.sidebar.multiselect("Instancia", etapas_disp, default=etapas_disp)

df_filtrado = df_inst[
    df_inst['Aero'].isin(sel_aero) &
    df_inst['Instancia'].isin(sel_etapa)
]

# ============================================================
# 6. INDICADORES
# ============================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Obras", len(df_inst))
col2.metric("En Ejecución",       (df_inst['Instancia'] == 'Ejecución').sum())
col3.metric("Con CAO presentado", (df_inst['Instancia'] == 'CAO presentado').sum())
col4.metric("Finalizadas",        (df_inst['Instancia'] == 'Finalizada').sum())

# ============================================================
# 7. GRÁFICO DE BARRAS POR INSTANCIA
# ============================================================
st.subheader("Obras por Instancia Actual")

conteo = (
    df_filtrado['Instancia']
    .value_counts()
    .reindex(etapas_disp, fill_value=0)
    .reset_index()
)
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(
    conteo,
    x='Etapa',
    y='Cantidad',
    text='Cantidad',
    title="Distribución de obras según la primera etapa no finalizada",
    color='Etapa',
)
fig.update_traces(textposition='outside')
fig.update_layout(showlegend=False, xaxis_tickangle=-30)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 8. LISTADO DETALLADO
# ============================================================
st.subheader("Listado detallado de obras")
st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

# ============================================================
# 9. DETALLE DE TAREAS Y SUB-TAREAS
# ============================================================
with st.expander("Ver todas las tareas y sub-tareas (datos crudos)"):
    st.dataframe(
        df[['Número de esquema', 'Nombre', 'Aero', 'N° OME',
            '% completado', 'Es_Principal', 'Obra_ID']],
        use_container_width=True,
        hide_index=True,
    )
