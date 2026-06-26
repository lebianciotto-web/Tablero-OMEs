# 3. Procesamiento (Aseguramos nombres de columnas claros)
df_inst = calcular_instancias(df)
conteo = df_inst['Instancia'].value_counts().reindex(
    ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
     'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado'], 
    fill_value=0
).reset_index()

# Renombramos las columnas para evitar ambigüedad
conteo.columns = ['Etapa', 'Cantidad']

# 4. Dashboard Visual
col1, col2 = st.columns(2)
with col1:
    # Contamos tareas principales (aquellas sin punto en el número de esquema)
    total_omes = df[~df['Número de esquema'].str.contains('\.', na=False)]['Nombre'].nunique()
    st.metric("Total OMEs (Principales)", total_omes)

st.subheader("Obras por Instancia Actual")

# Usamos las columnas renombradas explícitamente
fig = px.bar(
    conteo, 
    x='Etapa', 
    y='Cantidad', 
    title="Cantidad de Obras según su última etapa completada"
)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Listado Detallado")
st.dataframe(df)