import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # Limpieza de porcentajes
    if '% completado' in df.columns:
        col = df['% completado'].astype(str).str.strip().str.replace('%', '').str.replace(',', '.')
        df['% completado'] = pd.to_numeric(col, errors='coerce').fillna(0)
        df['% completado'] = df['% completado'].apply(lambda x: x / 100 if x > 1 else x)
    
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()
    return df

df = cargar_datos()

# --- LÓGICA DE INSTANCIAS ---
orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']

resultados = []
df['Es_Principal'] = ~df['Número de esquema'].str.contains('\.')
df['Obra_ID'] = df['Es_Principal'].cumsum()

# Depuración: vemos qué tareas existen realmente
nombres_tareas_unicos = df['Nombre'].unique()
st.sidebar.write("Tareas detectadas en el CSV:", nombres_tareas_unicos)

for obra_id, grupo in df.groupby('Obra_ID'):
    nombre_obra = grupo.iloc[0]['Nombre']
    ultima_etapa_encontrada = "Ninguna"
    
    # Buscamos de atrás hacia adelante
    for etapa in reversed(orden_etapas):
        # Buscamos cualquier fila en el grupo que contenga el nombre de la etapa
        match = grupo[grupo['Nombre'].str.contains(etapa, case=False, na=False)]
        
        # Si encontramos la tarea y tiene progreso > 0
        if not match.empty:
            progreso = match.iloc[0]['% completado']
            if progreso > 0:
                ultima_etapa_encontrada = etapa
                break
            
    resultados.append({'Obra': nombre_obra, 'Instancia': ultima_etapa_encontrada})

df_inst = pd.DataFrame(resultados)

# --- DASHBOARD ---
st.subheader("Obras por Instancia Actual")
conteo = df_inst['Instancia'].value_counts().reindex(orden_etapas, fill_value=0).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Distribución de Obras")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df)