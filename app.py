import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(layout="wide")
st.title("Dashboard de Obras - UNE")

@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # LIMPIEZA AGRESIVA
    if '% completado' in df.columns:
        # 1. Convertir a string y quitar espacios en blanco
        col = df['% completado'].astype(str).str.strip()
        # 2. Quitar el símbolo '%'
        col = col.str.replace('%', '', regex=False)
        # 3. Reemplazar comas por puntos (ej: 48,5 -> 48.5)
        col = col.str.replace(',', '.', regex=False)
        # 4. Convertir a número (float)
        df['% completado'] = pd.to_numeric(col, errors='coerce')
        # 5. Dividir por 100 para convertir 48 en 0.48
        df['% completado'] = df['% completado'] / 100
        # 6. Rellenar vacíos con 0
        df['% completado'] = df['% completado'].fillna(0)
    
    df['Número de esquema'] = df['Número de esquema'].astype(str).str.strip()
    return df

df = cargar_datos()

# Verificación visual rápida para estar seguros
st.write("Verificación de datos (primeros 5):", df[['Nombre', '% completado']].head())

# --- LÓGICA DE INSTANCIAS ---
orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']

resultados = []
df['Es_Principal'] = ~df['Número de esquema'].str.contains('\.', na=False)
df['Obra_ID'] = df['Es_Principal'].cumsum()

for obra_id, grupo in df.groupby('Obra_ID'):
    nombre_obra = grupo.iloc[0]['Nombre']
    ultima_etapa_encontrada = "Pliego" 
    
    for etapa in reversed(orden_etapas):
        subtarea = grupo[grupo['Nombre'].str.contains(etapa, case=False, na=False)]
        # Ahora el umbral > 0 funcionará porque los números son reales (ej. 0.48)
        if not subtarea.empty and subtarea.iloc[0]['% completado'] > 0:
            ultima_etapa_encontrada = etapa
            break
            
    resultados.append({'Obra': nombre_obra, 'Instancia': ultima_etapa_encontrada})

df_inst = pd.DataFrame(resultados)

# --- DASHBOARD ---
st.subheader("Obras por Instancia Actual")
conteo = df_inst['Instancia'].value_counts().reindex(orden_etapas, fill_value=0).reset_index()
conteo.columns = ['Etapa', 'Cantidad']

fig = px.bar(conteo, x='Etapa', y='Cantidad', title="Cantidad de Obras por etapa")
st.plotly_chart(fig, use_container_width=True)