import streamlit as st
import pandas as pd

st.set_page_config(layout="wide")
st.title("Diagnóstico de Datos - OMEs")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    return df

df = cargar_datos()

# Muestra qué hay exactamente en la columna
st.write("### Datos crudos de la columna '% completado'")
st.write(df['% completado'].head(20))

# Muestra cómo ve Python el tipo de dato
st.write("### Tipo de dato detectado:")
st.write(df['% completado'].dtype)

# Muestra el contenido de la columna como texto puro
st.write("### Contenido como texto:")
st.write(df['% completado'].astype(str).unique())