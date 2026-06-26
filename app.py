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

    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()

    df['% completado'] = (
        df['% completado']
        .astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    if df['% completado'].max() > 1.5:
        df['% completado'] = df['% completado'] / 100.0

    return df

df = cargar_datos()

# ============================================================
# 2. TAREAS PRINCIPALES Y SUB-TAREAS
# ============================================================
df['Es_Principal'] = ~df['Número de esquema'].str.contains(r'\.', regex=True, na=False)
df['Obra_ID'] = df['Es_Principal'].cumsum()

# ============================================================
# 3. ETAPAS DEL FLUJO (en orden)
# ============================================================
orden_etapas = [
    'Pliego',
    'Revisión DOM',
    'Presupuesto',
    'Documentación en papel',
    'ORSNA',
    'Adjudicación',
    'Ejecución',
    'CAO presentado',
]

# ============================================================
# 4. DETECTAR INSTANCIA ACTUAL DE CADA OBRA
# ============================================================
TOL = 1e-6  # tolerancia numérica

resultados = []

for obra_id, grupo in df.groupby('Obra_ID'):
    fila_principal = grupo[grupo['Es_Principal']].iloc[0]
    nombre_obra = fila_principal['Nombre']
    aero        = fila_principal.get('Aero', '')
    n_ome       = fila_principal.get('N° OME', '')
    avance_obra = fila_principal.get('% completado', 0)

    subtareas = grupo[~grupo['Es_Principal']].copy()
    subtareas['Nombre_norm'] = subtareas['Nombre'].astype(str).str.strip().str.lower()

    # Construimos un dict {etapa: pct} respetando el orden del flujo
    etapas_pct = []
    for etapa in orden_etapas:
        match = subtareas[subtareas['Nombre_norm'] == etapa.lower()]
        if not match.empty:
            etapas_pct.append((etapa, float(match['% completado'].iloc[0])))

    instancia_actual = "Sin iniciar"
    estado = "sin_iniciar"

    if etapas_pct:
        # 1) ¿Hay alguna en curso (0 < pct < 1)?
        en_curso = next(
            ((e, p) for e, p in etapas_pct if TOL < p < 1.0 - TOL),
            None
        )
        if en_curso:
            instancia_actual = f"En curso: {en_curso[0]}"
            estado = "en_curso"
        else:
            # 2) ¿Todas finalizadas?
            if all(p >= 1.0 - TOL for _, p in etapas_pct):
                instancia_actual = "Finalizada"
                estado = "finalizada"
            # 3) ¿Ninguna iniciada?
            elif all(p <= TOL for _, p in etapas_pct):
                instancia_actual = "Sin iniciar"
                estado = "sin_iniciar"
            # 4) Entre etapas: primera con pct=0 después de las completadas
            else:
                pendiente = next(
                    (e for e, p in etapas_pct if p <= TOL),
                    None
                )
                if pendiente:
                    instancia_actual = f"Pendiente: {pendiente}"
                    estado = "pendiente"

    resultados.append({
        'N° OME':    n_ome,
        'Aero':      aero,
        'Obra':      nombre_obra,
        '% Avance':  round(avance_obra * 100, 1) if avance_obra <= 1 else round(avance_obra, 1),
        'Instancia': instancia_actual,
        'Estado':    estado,
    })

df_inst = pd.DataFrame(resultados)

# ============================================================
# 5. FILTROS LATERALES
# ============================================================
st.sidebar.header("Filtros")
aeros = sorted([a for a in df_inst['Aero'].dropna().unique() if str(a).strip() != ''])
sel_aero = st.sidebar.multiselect("Aeropuerto (Aero)", aeros, default=aeros)

instancias_disp = sorted(df_inst['Instancia'].unique().tolist())
sel_inst = st.sidebar.multiselect("Instancia", instancias_disp, default=instancias_disp)

df_filtrado = df_inst[
    df_inst['Aero'].isin(sel_aero) &
    df_inst['Instancia'].isin(sel_inst)
]

# ============================================================
# 6. INDICADORES
# ============================================================
col1, col2, col3, col4 = st.columns(4)
col1.metric("Total Obras",   len(df_inst))
col2.metric("En curso",      (df_inst['Estado'] == 'en_curso').sum())
col3.metric("Pendientes",    (df_inst['Estado'] == 'pendiente').sum())
col4.metric("Finalizadas",   (df_inst['Estado'] == 'finalizada').sum())

# ============================================================
# 7. GRÁFICO DE BARRAS POR INSTANCIA
# ============================================================
st.subheader("Obras por Instancia Actual")

conteo = (
    df_filtrado['Instancia']
    .value_counts()
    .reset_index()
)
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(
    conteo,
    x='Etapa',
    y='Cantidad',
    text='Cantidad',
    title="Distribución de obras según su instancia actual",
    color='Etapa',
)
fig.update_traces(textposition='outside')
fig.update_layout(showlegend=False, xaxis_tickangle=-30)
st.plotly_chart(fig, use_container_width=True)

# ============================================================
# 8. LISTADO DETALLADO
# ============================================================
st.subheader("Listado detallado de obras")
st.dataframe(
    df_filtrado.drop(columns=['Estado']),
    use_container_width=True,
    hide_index=True,
)

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
