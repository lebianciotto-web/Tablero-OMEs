import streamlit as st
import pandas as pd

st.title("Diagnóstico de Datos")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    return df

df = cargar_datos()

# Esto nos mostrará la verdad absoluta de lo que hay en el archivo
st.write("Columnas detectadas:", df.columns.tolist())
st.write("Primeras 10 filas de la columna '% completado':")
st.write(df['% completado'].head(10))

# Verificar el tipo de dato
st.write("Tipo de dato de la columna:", df['% completado'].dtype)