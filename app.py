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
    # Convertimos a numérico de forma segura
    df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce').fillna(0)
    
    # Buscamos bloques: desde un número entero hasta el siguiente
    indices_principales = df[~df['Número de esquema'].str.contains('\.', na=False)].index
    
    for i in range(len(indices_principales)):
        idx_inicio = indices_principales[i]
        # El bloque termina donde empieza el siguiente o al final del archivo
        idx_fin = indices_principales[i+1] if (i+1) < len(indices_principales) else len(df)
        
        bloque = df.iloc[idx_inicio:idx_fin]
        nombre_obra = bloque.iloc[0]['Nombre']
        
        # Buscamos la última etapa completada en este bloque
        etapa_actual = 'Pliego' # Default
        for etapa in reversed(orden_etapas):
            # Filtramos si la fila coincide con el nombre de la etapa y está al 100%
            subtarea = bloque[bloque['Nombre'] == etapa]
            if not subtarea.empty and subtarea.iloc[0]['% completado'] >= 0.99:
                etapa_actual = etapa
                break
        
        resultados.append({'Obra': nombre_obra, 'Instancia': etapa_actual})
    
    return pd.DataFrame(resultados)

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
