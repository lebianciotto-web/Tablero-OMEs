import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

# ---------- CARGA DE DATOS ----------
@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8, decimal=',')
    df.columns = df.columns.str.strip()
    # Forzamos string para poder buscar el punto
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()
    # % completado a numérico (viene con coma decimal)
    df['% completado'] = (
        df['% completado'].astype(str).str.replace(',', '.').astype(float)
    )
    return df

df = cargar_datos()

# ---------- IDENTIFICAR TAREAS PRINCIPALES Y SUB-TAREAS ----------
# Principal = el "Número de esquema" NO contiene punto (ej: "1", "2", "3")
# Sub-tarea = contiene punto (ej: "1.1", "2.3")
df['Es_Principal'] = ~df['Número de esquema'].str.contains(r'\.', regex=True, na=False)
df['Obra_ID'] = df['Es_Principal'].cumsum()

# ---------- ETAPAS EN ORDEN ----------
orden_etapas = {
    'Pliego': 'Pliego',
    'Revisión DOM': 'Revisión DOM',
    'Presupuesto': 'Presupuesto',
    'Documentación en papel': 'Documentación en papel',
    'ORSNA': 'ORSNA',
    'Adjudicación': 'Adjudicación',
    'Ejecución': 'Ejecución',
    'CAO presentado': 'CAO presentado',
}

# ---------- DETECTAR ÚLTIMA ETAPA CON PROGRESO ----------
resultados = []
for obra_id, grupo in df.groupby('Obra_ID'):
    fila_principal = grupo[grupo['Es_Principal']].iloc[0]
    nombre_obra = fila_principal['Nombre']
    aero = fila_principal.get('Aero', '')
    n_ome = fila_principal.get('N° OME', '')
    avance_obra = fila_principal.get('% completado', 0)

    subtareas = grupo[~grupo['Es_Principal']]
    ultima_etapa = "Ninguna"

    # Recorremos las etapas en el orden definido y nos quedamos con
    # la última que tenga % completado > 0
    for etapa_clave in orden_etapas.keys():
        match = subtareas[subtareas['Nombre'].str.contains(etapa_clave, case=False, na=False)]
        if not match.empty and (match['% completado'] > 0).any():
            ultima_etapa = orden_etapas[etapa_clave]

    resultados.append({
        'Obra': nombre_obra,
        'Aero': aero,
        'N° OME': n_ome,
        '% Avance': avance_obra,
        'Instancia': ultima_etapa,
    })

df_inst = pd.DataFrame(resultados)

# ---------- DASHBOARD ----------
col1, col2 = st.columns([1, 3])
with col1:
    st.metric("Total Obras Principales", df['Es_Principal'].sum())
with col2:
    st.metric("Obras en Ejecución / CAO",
              df_inst['Instancia'].isin(['Ejecución', 'CAO presentado']).sum())

st.subheader("Obras por Instancia Actual")
conteo = (
    df_inst['Instancia']
    .value_counts()
    .reindex(list(orden_etapas.values()) + ['Ninguna'], fill_value=0)
    .reset_index()
)
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(
    conteo, x='Etapa', y='Cantidad',
    title="Distribución de Obras según su última etapa con progreso",
    text='Cantidad'
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado por Obra")
st.dataframe(df_inst, use_container_width=True)

with st.expander("Ver todas las tareas y sub-tareas"):
    st.dataframe(df, use_container_width=True)
