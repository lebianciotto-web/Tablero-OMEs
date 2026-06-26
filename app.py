import streamlit as st
import pandas as pd
import plotly.express as px

# 1. Cargar y limpiar datos
@st.cache_data
def cargar_datos():
    # Usamos sep=';' y skiprows=8 como ya habíamos definido
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # Aseguramos que la columna de esquema sea tratada como string para detectar el punto
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df

df = cargar_datos()

# 2. Lógica para asignar instancia
def calcular_instancia(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    
    resultados = []
    # Agrupamos por bloques (cada vez que aparece un número entero, inicia un nuevo bloque)
    bloque_actual = None
    
    for _, fila in df.iterrows():
        esquema = fila['Número de esquema']
        
        # Si no tiene punto, es Tarea Principal
        if '.' not in esquema:
            bloque_actual = fila['Nombre']
        else:
            # Es sub-tarea, calculamos si está al 100%
            if float(fila['% completado']) == 1.0:
                resultados.append({
                    'Obra': bloque_actual,
                    'Instancia': fila['Nombre']
                })
    
    return pd.DataFrame(resultados)

# 3. Preparar gráfico
df_instancias = calcular_instancia(df)

# Contamos cuántas obras están en cada instancia (tomamos la última completada por obra)
resumen = df_instancias.sort_values('Instancia').groupby('Obra').tail(1)
conteo = resumen['Instancia'].value_counts().reindex(orden_etapas, fill_value=0).reset_index()

# 4. Visualización
st.subheader("Obras por Instancia Actual")
fig = px.bar(conteo, x='Instancia', y='count', title="Cantidad de Obras según su última etapa completada")
st.plotly_chart(fig, use_container_width=True)