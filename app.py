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
    df['% completado'] = df['% completado'].astype(str).str.replace(',', '.')
    df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce').fillna(0)
    df['% completado'] = df['% completado'].apply(lambda x: x / 100 if x > 1 else x)
    
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()
    return df

df = cargar_datos()

# --- LÓGICA DE INSTANCIAS ---
orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']

resultados = []
# Agrupamos por obra (bloques 1.0, 2.0, etc)
# Creamos un identificador de bloque: cada vez que el esquema no tiene punto, es una nueva obra
df['Es_Principal'] = ~df['Número de esquema'].str.contains('\.')
df['Obra_ID'] = df['Es_Principal'].cumsum()

for obra_id, grupo in df.groupby('Obra_ID'):
    nombre_obra = grupo.iloc[0]['Nombre']
    ultima_etapa_encontrada = "Ninguna"
    
    # Buscamos en orden inverso: la última etapa que tenga progreso > 0
    for etapa in reversed(orden_etapas):
        # Buscamos si el nombre de la etapa aparece en el nombre de la tarea (case insensitive)
        subtarea = grupo[grupo['Nombre'].str.contains(etapa, case=False, na=False)]
        if not subtarea.empty and subtarea.iloc[0]['% completado'] > 0:
            ultima_etapa_encontrada = etapa
            break
            
    resultados.append({'Obra': nombre_obra, 'Instancia': ultima_etapa_encontrada})

df_inst = pd.DataFrame(resultados)

# --- DASHBOARD ---
col1, _ = st.columns([1, 3])
with col1:
    st.metric("Total OMEs", df[df['Es_Principal']]['Nombre'].nunique())

st.subheader("Obras por Instancia Actual")
conteo = df_inst['Instancia'].value_counts().reindex(orden_etapas, fill_value=0).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Distribución de Obras")
st.plotly_chart(fig, use_container_width=True)

st.dataframe(df)