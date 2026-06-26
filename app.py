import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

# 1. CARGA Y LIMPIEZA
@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # Limpieza de porcentaje: quita el % y convierte a decimal (98% -> 0.98)
    if '% completado' in df.columns:
        df['% completado'] = df['% completado'].astype(str).str.replace('%', '').str.replace(',', '.')
        df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce') / 100
        df['% completado'] = df['% completado'].fillna(0)
    
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df

# 2. LÓGICA DE INSTANCIAS
def calcular_instancias(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    
    resultados = []
    indices_principales = df[~df['Número de esquema'].str.contains('\.', na=False)].index
    
    for i in range(len(indices_principales)):
        idx_inicio = indices_principales[i]
        idx_fin = indices_principales[i+1] if (i+1) < len(indices_principales) else len(df)
        
        bloque = df.iloc[idx_inicio:idx_fin]
        nombre_obra = bloque.iloc[0]['Nombre']
        
        # Buscamos la última etapa con progreso > 0
        etapa_actual = 'Pliego'
        for etapa in reversed(orden_etapas):
            subtarea = bloque[bloque['Nombre'] == etapa]
            # Ahora detecta cualquier progreso > 0.01 (1%)
            if not subtarea.empty and subtarea.iloc[0]['% completado'] >= 0.01:
                etapa_actual = etapa
                break
        
        resultados.append({'Obra': nombre_obra, 'Instancia': etapa_actual})
    
    return pd.DataFrame(resultados)

# 3. PROCESAMIENTO
df = cargar_datos()
df_inst = calcular_instancias(df)

etapas_orden = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']

if not df_inst.empty and 'Instancia' in df_inst.columns:
    conteo = df_inst['Instancia'].value_counts().reindex(etapas_orden, fill_value=0).reset_index()
    conteo.columns = ['Etapa', 'Cantidad']
else:
    conteo = pd.DataFrame({'Etapa': etapas_orden, 'Cantidad': 0})

# 4. DASHBOARD
col1, col2 = st.columns(2)
with col1:
    total_omes = df[~df['Número de esquema'].str.contains('\.', na=False)]['Nombre'].nunique()
    st.metric("Total OMEs (Principales)", total_omes)

st.subheader("Obras por Instancia Actual")
fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Cantidad de Obras según su última etapa con progreso")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)