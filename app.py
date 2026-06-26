def calcular_instancia(df):
    orden_etapas = ['Pliego', 'Revisión DOM', 'Presupuesto', 'Documentación en papel', 
                    'ORSNA', 'Adjudicación', 'Ejecución', 'CAO presentado']
    
    resultados = []
    bloque_actual = None
    
    # Aseguramos que la columna sea numérica, convirtiendo errores a 0
    df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce').fillna(0)
    
    for _, fila in df.iterrows():
        esquema = str(fila['Número de esquema'])
        
        # Si no tiene punto, es Tarea Principal
        if '.' not in esquema:
            bloque_actual = fila['Nombre']
        else:
            # Si es sub-tarea, verificamos si está al 100%
            # Usamos float() solo después de asegurar que es un número
            if float(fila['% completado']) >= 1.0:
                resultados.append({
                    'Obra': bloque_actual,
                    'Instancia': fila['Nombre']
                })
    
    return pd.DataFrame(resultados)