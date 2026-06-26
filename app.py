import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

# 1. CARGA Y LIMPIEZA DE DATOS
@st.cache_data
def cargar_datos():
    # Carga el archivo saltando las 8 filas de metadatos según estructura de tu CSV
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # Limpieza de la columna '% completado':
    # 1. Reemplaza comas por puntos para que Python entienda el decimal.
    # 2. Convierte a numérico, transformando cualquier texto en NaN (luego 0).
    # 3. Normaliza: si el número es > 1 (ej. 60), lo divide por 100 para que sea 0.6.
    if '% completado' in df.columns:
        df['% completado'] = df['% completado'].astype(str).str.replace(',', '.')
        df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce').fillna(0)
        df['% completado'] = df['% completado'].apply(lambda x: x / 100 if x > 1 else x)
    
    # Convertir esquema a string para poder identificar tareas principales (sin puntos)
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df

# 2. LÓGICA DE INSTANCIAS (Jerarquía de tareas)
def calcular_instancias(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    
    resultados = []
    # Identificamos el inicio de cada bloque de obra (tareas principales)
    indices_principales = df[~df['Número de esquema'].str.contains('\.', na=False)].index
    
    for i in range(len(indices_principales)):
        idx_inicio = indices_principales[i]
        # El bloque termina donde empieza el siguiente, o al final del dataframe
        idx_fin = indices_principales[i+1] if (i+1) < len(indices_principales) else len(df)
        
        bloque = df.iloc[idx_inicio:idx_fin]
        nombre_obra = bloque.iloc[0]['Nombre']
        
        # Determinamos la última etapa alcanzada (umbral 5% para considerar activa)
        etapa_actual = 'Pliego'
        for etapa in reversed(orden_etapas):
            subtarea = bloque[bloque['Nombre'] == etapa]
            if not subtarea.empty and subtarea.iloc[0]['% completado'] >= 0.05:
                etapa_actual = etapa
                break
        
        resultados.append({'Obra': nombre_obra, 'Instancia': etapa_actual})
    
    return pd.DataFrame(resultados)

# 3. PROCESAMIENTO
df = cargar_datos()
df_inst = calcular_instancias(df)

etapas_orden = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']

# Preparar datos para gráfico
if not df_inst.empty:
    conteo = df_inst['Instancia'].value_counts().reindex(etapas_orden, fill_value=0).reset_index()
    conteo.columns = ['Etapa', 'Cantidad']
else:
    conteo = pd.DataFrame({'Etapa': etapas_orden, 'Cantidad': 0})

# 4. DASHBOARD VISUAL
col1, col2 = st.columns(2)
with col1:
    # Contamos tareas principales (aquellas sin punto en el número de esquema)
    total_omes = df[~df['Número de esquema'].str.contains('\.', na=False)]['Nombre'].nunique()
    st.metric("Total OMEs (Principales)", total_omes)

st.subheader("Obras por Instancia Actual")
fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Cantidad de Obras según su última etapa con progreso")
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)