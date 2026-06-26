import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de OMEs - UNE")

# 1. CARGA DE DATOS
@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df

# 2. DEFINICIÓN DE LA FUNCIÓN (Debe ir antes de llamarla)
def calcular_instancias(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    resultados = []
    bloque_actual = None
    
    # Limpieza previa
    df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce').fillna(0)
    
    for _, fila in df.iterrows():
        esquema = str(fila['Número de esquema'])
        if '.' not in esquema:
            bloque_actual = fila['Nombre']
        else:
            if float(fila['% completado']) >= 0.99:
                resultados.append({'Obra': bloque_actual, 'Instancia': fila['Nombre']})
    
    df_res = pd.DataFrame(resultados)
    if not df_res.empty:
        return df_res.groupby('Obra').tail(1)
    return pd.DataFrame(columns=['Obra', 'Instancia'])

# 3. EJECUCIÓN (Llamamos a las funciones aquí abajo)
df = cargar_datos()
df_inst = calcular_instancias(df)

# Procesamiento para gráfico
conteo = df_inst['Instancia'].value_counts().reindex(
    ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
     'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado'], 
    fill_value=0
).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

# 4. DASHBOARD
col1, col2 = st.columns(2)
with col1:
    total_omes = df[~df['Número de esquema'].str.contains('\.', na=False)]['Nombre'].nunique()
    st.metric("Total OMEs (Principales)", total_omes)

st.subheader("Obras por Instancia Actual")
fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Cantidad de Obras según su última etapa completada")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)