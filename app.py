import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
import pandas as pd

# Carga de datos
@st.cache_data
def load_data():
    # Agregamos sep=';' para decirle a Pandas que use el punto y coma como separador
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=0)
    return df

@st.cache_data
def load_data():
    # Cargamos el archivo indicando el separador correcto
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    
    # 1. Limpiamos espacios en los nombres de las columnas
    df.columns = df.columns.str.strip()
    
    # 2. FORZAMOS la conversión a números de la columna '% completado'
    # 'coerce' convierte cualquier valor no numérico a NaN (Not a Number) para evitar el error
    df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce')
    
    return df

# Configuración de página
st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

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
