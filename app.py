import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # Limpieza de porcentajes: quita '%' y comas, convierte a decimal
    if '% completado' in df.columns:
        col = df['% completado'].astype(str).str.strip().str.replace('%', '').str.replace(',', '.')
        df['% completado'] = pd.to_numeric(col, errors='coerce').fillna(0)
        df['% completado'] = df['% completado'].apply(lambda x: x / 100 if x > 1 else x)
    
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()
    return df

df = cargar_datos()

# Lista de palabras clave que aparecen en tus sub-tareas
# El código buscará si el nombre de la tarea contiene estas palabras
orden_etapas = {
    'Pliego': 'Pliego',
    'Revisión DOM': 'DOM',
    'Presupuesto': 'Presupuesto',
    'Documentación en papel': 'Documentación',
    'ORSNA': 'ORSNA',
    'Adjudicación': 'Adjudicación',
    'Ejecución': 'Ejecución',
    'CAO presentado': 'CAO'
}

resultados = []
df['Es_Principal'] = ~df['Número de esquema'].str.contains('\.')
df['Obra_ID'] = df['Es_Principal'].cumsum()

for obra_id, grupo in df.groupby('Obra_ID'):
    nombre_obra = grupo.iloc[0]['Nombre']
    ultima_etapa_encontrada = "Ninguna"
    
    # Buscamos de atrás hacia adelante (de CAO a Pliego)
    for etapa_larga, palabra_clave in reversed(list(orden_etapas.items())):
        match = grupo[grupo['Nombre'].str.contains(palabra_clave, case=False, na=False)]
        
        if not match.empty:
            if match.iloc[0]['% completado'] > 0:
                ultima_etapa_encontrada = etapa_larga
                break
            
    resultados.append({'Obra': nombre_obra, 'Instancia': ultima_etapa_encontrada})

df_inst = pd.DataFrame(resultados)

# --- DASHBOARD ---
col1, _ = st.columns([1, 3])
with col1:
    st.metric("Total Obras Principales", df[df['Es_Principal']]['Nombre'].nunique())

st.subheader("Obras por Instancia Actual")
conteo = df_inst['Instancia'].value_counts().reindex(orden_etapas.keys(), fill_value=0).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Distribución de Obras según su última etapa con progreso")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)