import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Diagnóstico")

@st.cache_data
def cargar_datos():
    # Usamos el nombre exacto de tu archivo y el separador correcto
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    # Limpiamos nombres de columnas
    df.columns = df.columns.str.strip()
    return df

try:
    df = cargar_datos()
    st.write("¡Archivo cargado correctamente!")
    st.write("Columnas detectadas:", df.columns.tolist())
    
    # Mostrar el dataframe para ver qué datos hay realmente
    st.dataframe(df.head(10))
    
    # Probemos si existe la columna Aero
    if 'Aero' in df.columns:
        st.success("La columna 'Aero' existe.")
    else:
        st.error("La columna 'Aero' NO existe. Revisa los nombres listados arriba.")

except Exception as e:
    st.error(f"Error al cargar el archivo: {e}")