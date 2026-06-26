import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de OMEs - UNE")

# 1. Carga de datos
@st.cache_data
def cargar_datos():
    # Usamos el archivo real y el separador que confirmamos
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    # Limpieza básica de la columna clave
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df

df = cargar_datos()

# 2. Lógica para determinar la instancia actual de cada obra
def calcular_instancias(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    
    resultados = []
    bloque_actual = None
    
    for _, fila in df.iterrows():
        esquema = str(fila['Número de esquema'])
        # Si no tiene punto es Tarea Principal, si tiene es Sub-tarea
        if '.' not in esquema:
            bloque_actual = fila['Nombre']
        else:
            # Si sub-tarea completada al 100%, la marcamos
            # (Usamos 0.99 para evitar errores de precisión decimal)
            val = pd.to_numeric(fila['% completado'], errors='coerce')
            if val and val >= 0.99:
                resultados.append({'Obra': bloque_actual, 'Instancia': fila['Nombre']})
    
    # Nos quedamos con la última etapa alcanzada por cada obra
    df_res = pd.DataFrame(resultados)
    if not df_res.empty:
        return df_res.groupby('Obra').tail(1)
    return pd.DataFrame(columns=['Obra', 'Instancia'])

# 3. Procesamiento
df_inst = calcular_instancias(df)
conteo = df_inst['Instancia'].value_counts().reindex(
    ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado'], 
    fill_value=0
).reset_index()

# 4. Dashboard Visual
col1, col2 = st.columns(2)
with col1:
    st.metric("Total OMEs (Principales)", df[~df['Número de esquema'].str.contains('\.')]['Nombre'].nunique())

st.subheader("Obras por Instancia Actual")
fig = px.bar(conteo, x='index', y='Instancia', labels={'index': 'Etapa', 'Instancia': 'Cantidad'})
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)