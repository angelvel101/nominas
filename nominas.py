#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd

st.title("Consolidador de Nóminas (Modo Avanzado)")

archivos_subidos = st.file_uploader("Sube todas las nóminas aquí (Excel)", type=["xlsx"], accept_multiple_files=True)

if archivos_subidos:
    lista_df = []
    
    for archivo in archivos_subidos:
        # Leemos el archivo como una cuadrícula cruda (sin encabezados)
        # sheet_name=0 le dice que solo lea la primera hoja para evitar duplicar
        df = pd.read_excel(archivo, sheet_name=0, header=None)
        
        pat_col, mat_col, nom_col, imp_col = None, None, None, None
        
        # 1. Escanear qué columna es cuál buscando palabras clave en toda la columna
        for col in df.columns:
            col_str = df[col].astype(str).str.lower()
            if col_str.str.contains('paterno', na=False).any(): pat_col = col
            if col_str.str.contains('materno', na=False).any(): mat_col = col
            if col_str.str.contains('nombre', na=False).any(): nom_col = col
            if col_str.str.contains('importe|neto a pagar', na=False).any(): imp_col = col
            
        if nom_col is not None and imp_col is not None:
            # 2. Armar el nombre completo uniendo las columnas que existan
            nombres = pd.Series("", index=df.index)
            if pat_col is not None: nombres += df[pat_col].fillna("").astype(str) + " "
            if mat_col is not None: nombres += df[mat_col].fillna("").astype(str) + " "
            nombres += df[nom_col].fillna("").astype(str)
            
            temp_df = pd.DataFrame({'Nombre': nombres, 'Importe': df[imp_col]})
            
            # 3. La Magia: Limpiar la tabla de logos y totales
            # Forzamos la columna Importe a números (los textos/logos se vuelven error/NaN)
            temp_df['Importe'] = pd.to_numeric(temp_df['Importe'], errors='coerce')
            
            # Borramos las filas donde el importe quedó como NaN
            temp_df = temp_df.dropna(subset=['Importe'])
            
            # Borramos las filas que son solo los títulos repitiéndose
            temp_df = temp_df[~temp_df['Nombre'].str.contains('nombre', case=False, na=False)]
            
            # Borramos comisiones donde el nombre es un número (ej. el 0.045)
            temp_df = temp_df[temp_df['Nombre'].str.contains('[A-Za-z]', na=False)]
            
            # Estandarizamos el texto final: Todo mayúsculas, quitamos dobles espacios
            temp_df['Nombre'] = temp_df['Nombre'].str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            
            lista_df.append(temp_df)

    if st.button("Generar Acumulado Total"):
        if lista_df:
            # Consolidación final
            df_total = pd.concat(lista_df, ignore_index=True)
            df_agrupado = df_total.groupby('Nombre', as_index=False)['Importe'].sum()
            
            st.success("¡Extracción y consolidación completadas!")
            st.dataframe(df_agrupado)
            
            @st.cache_data
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')
                
            st.download_button("Descargar Acumulado (.csv)", data=convert_df(df_agrupado), file_name='Acumulado_Total.csv', mime='text/csv')
        else:
            st.error("No se detectaron columnas de nombres o importes válidos en los archivos.")

