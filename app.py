import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # 1. Limpieza de Porcentaje (Convertir '0,6' a 0.6)
    df['% completado'] = df['% completado'].astype(str).str.replace(',', '.')
    df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce').fillna(0)
    # Si detecta números > 1, los divide por 100
    df['% completado'] = df['% completado'].apply(lambda x: x / 100 if x > 1 else x)
    
    # 2. Asegurar esquema como string
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()
    return df

df = cargar_datos()

# --- LÓGICA DE INSTANCIAS (Simplificada) ---
# Definimos las etapas para el orden lógico
etapas_lista = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']

# Creamos una columna temporal para identificar la obra principal
df['Es_Principal'] = ~df['Número de esquema'].str.contains('\.')
df['Obra_ID'] = df['Es_Principal'].cumsum() 

# Filtramos solo sub-tareas que tengan progreso > 0
progreso = df[~df['Es_Principal'] & (df['% completado'] > 0)].copy()

# Encontramos la última sub-tarea con progreso por cada obra
ultima_etapa = progreso.groupby('Obra_ID').apply(lambda x: x.iloc[-1])

# --- DASHBOARD ---
col1, col2 = st.columns(2)
with col1:
    st.metric("Total OMEs (Principales)", df[df['Es_Principal']]['Nombre'].nunique())

st.subheader("Obras por Instancia Actual")

# Preparamos los datos para el gráfico
conteo = ultima_etapa['Nombre'].value_counts().reindex(etapas_lista, fill_value=0).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Distribución de Obras según su última etapa activa")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)