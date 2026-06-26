@st.cache_data
def cargar_datos():
    df = pd.read_csv("PR. OMES UNE.csv", sep=';', skiprows=8)
    df.columns = df.columns.str.strip()
    
    # 1. Limpiar la columna % completado:
    # Quitamos el símbolo %, reemplazamos comas por puntos (si las hubiera) y convertimos a número
    if '% completado' in df.columns:
        # Convertimos a string primero para poder manipular el texto
        df['% completado'] = df['% completado'].astype(str).str.replace('%', '').str.replace(',', '.')
        # Convertimos a numérico real (si es 50%, quedará como 0.5)
        df['% completado'] = pd.to_numeric(df['% completado'], errors='coerce') / 100
        # Rellenamos nulos con 0
        df['% completado'] = df['% completado'].fillna(0)
    
    df['Número de esquema'] = df['Número de esquema'].astype(str)
    return df