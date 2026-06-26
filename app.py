import streamlit as st
import pandas as pd
import plotly.express as px

# Configuración de página
st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

# Carga de datos (Aquí conectaríamos la API de SharePoint/Planner)
# Por ahora simulamos la carga de tu CSV
@st.cache_data(ttl=600) # Se refresca cada 10 minutos automáticamente
def cargar_datos():
    df = pd.read_csv("tu_archivo.csv") # En el futuro, reemplaza por conexión a SharePoint
    return df

df = cargar_datos()

# Sidebar: Filtros
aeropuerto = st.sidebar.multiselect("Aeropuerto", df['Aero'].unique())
estado = st.sidebar.multiselect("Instancia", df['Nombre'].unique())

# KPIs
col1, col2, col3 = st.columns(3)
col1.metric("Total OMEs", df['N° OME'].nunique())
col2.metric("Valor POA", f"${df['POA'].sum():,.0f}")
col3.metric("Avance Promedio", f"{df['% completado'].mean()*100:.1f}%")

# Gráfico de barras (Instancias)
fig = px.bar(df, x='Nombre', y='POA', color='Aero', title="Distribución de Obras")
st.plotly_chart(fig, use_container_width=True)

# Listado
st.dataframe(df)