import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide", page_title="Dashboard Obras UNE")
st.title("📊 Dashboard de Obras - UNE")

# ============================================================
# 1. CARGA DE DATOS
# ============================================================
@st.cache_data
def cargar_datos():
    df = pd.read_csv(
        "PR. OMES UNE.csv",
        sep=';',
        skiprows=8,
        decimal=',',
        encoding='utf-8'
    )
    df.columns = df.columns.str.strip()

    # Forzamos string para poder detectar el punto en el N° de esquema
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()

    # % completado a numérico (viene con coma decimal)
    df['% completado'] = (
        df['% completado']
        .astype(str)
        .str.replace('%', '', regex=False)
        .str.replace(',', '.', regex=False)
        .astype(float)
    )
    # Si vinieron como 80 en lugar de 0,8 los normalizamos
    if df['% completado'].max() > 1.5:
