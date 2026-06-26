import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de OMEs - UNE")

# 1. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    # Carga el archivo con separador punto y coma y saltando los metadatos iniciales
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # Limpieza de la columna de porcentaje
    if '% completado' in df.columns:
        df['% completado'] = df['% completado'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce') / 100
        df['% completado'] = df['% completado'].fillna(0)
    
    # Asegurar que el esquema sea texto para detectar jerarquía
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df

# 2. LÓGICA DE INSTANCIAS (Jerarquía)
def calcular_instancias(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    
    resultados = []
    bloque_actual = None
    
    for _, fila in df.iterrows():
        esquema = str(fila['Número de esquema'])
        # Si no tiene punto es Tarea Principal
        if '.' not in esquema:
            bloque_actual = fila['Nombre']
        else:
            # Si es sub-tarea y está al 100% (o muy cerca)
            if float(fila['% completado']) >= 0.99:
                resultados.append({'Obra': bloque_actual, 'Instancia': fila['Nombre']})
    
    df_res = pd.DataFrame(resultados)
    if not df_res.empty:
        return df_res.groupby('Obra').tail(1)
    return pd.DataFrame(columns=['Obra', 'Instancia'])

# 3. EJECUCIÓN
df = cargar_datos()
df_inst = calcular_instancias(df)

# Procesamiento para gráfico
conteo = df_inst['Instancia'].value_counts().reindex(
    ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
     'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado'], 
    fill_value=0
).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

# 4. DASHBOARD VISUAL
col1, col2 = st.columns(2)
with col1:
    # Contamos tareas principales (aquellas sin punto en el número de esquema)
    total_omes = df[~df['Número de esquema'].str.contains('\.', na=False)]['Nombre'].nunique()
    st.metric("Total OMEs (Principales)", total_omes)

st.subheader("Obras por Instancia Actual")
fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Cantidad de Obras según su última etapa completada")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)