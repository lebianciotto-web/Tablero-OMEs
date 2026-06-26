import streamlit as st
import pandas as pd

st.title("Diagnóstico de Datos")
@st.cache_data
def cargar_datos():
    # Leemos el archivo saltando las filas de metadatos
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # --- LIMPIEZA DE LA COLUMNA DE PORCENTAJES ---
    if '% completado' in df.columns:
        # Convertimos a string, quitamos el '%', reemplazamos coma por punto
        df['% completado'] = df['% completado'].astype(str).str.replace('%', '').str.replace(',', '.')
        # Convertimos a número real. 'coerce' convierte errores (ej. celdas vacías) a NaN
        df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce')
        # Si el valor original era 50, ahora es 50. Lo dividimos por 100 para que sea 0.5
        df['% completado'] = df['% completado'] / 100
        # Rellenamos los valores vacíos con 0
        df['% completado'] = df['% completado'].fillna(0)
    
    # Aseguramos que el esquema sea texto para detectar puntos
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    
    return df

df = cargar_datos()

# Esto nos mostrará la verdad absoluta de lo que hay en el archivo
st.write("Columnas detectadas:", df.columns.tolist())
st.write("Primeras 10 filas de la columna '% completado':")
st.write(df['% completado'].head(10))

# Verificar el tipo de dato
st.write("Tipo de dato de la columna:", df['% completado'].dtype)
