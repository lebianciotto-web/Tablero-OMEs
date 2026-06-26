import streamlit as st
import pandas as pd
import plotly.express as px
import streamlit as st
import pandas as pd

# Carga de datos
@st.cache_data
def load_data():
    # Saltamos las 8 filas iniciales
    df = pd.read_csv("PR. OMES UNE.csv", skiprows=8)
    return df

df = load_data()

# --- ESTA LÍNEA TE AYUDARÁ A DEBUGUEAR ---
st.write("Columnas encontradas en el archivo:", df.columns.tolist())
# ------------------------------------------

# Ahora, reemplaza 'Aero' por el nombre exacto que veas en pantalla
# Ejemplo: si el log dice 'Aero ', usa df['Aero ']
aeropuerto = st.sidebar.multiselect("Aeropuerto", df['Aero'].unique())

@st.cache_data
def load_data():
    # 1. Leer el archivo forzando el separador ;
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    
    # 2. LIMPIEZA CRÍTICA: Eliminar espacios en blanco de los nombres de columnas
    df.columns = df.columns.str.strip()
    
    # 3. Asegurar que las columnas clave sean numéricas (ignorar errores si están vacías)
    if '% completado' in df.columns:
        df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce')
    
    # 4. Debug: Imprimir columnas si sigue fallando (esto aparecerá en tu app)
    # st.write("Columnas detectadas:", df.columns.tolist())
    
    return df

df = load_data()

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
