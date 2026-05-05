#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd

st.title("Consolidador de Nóminas")

# Permite subir múltiples archivos a la vez
archivos_subidos = st.file_uploader("Sube todas las nóminas aquí (Excel)", type=["xlsx"], accept_multiple_files=True)

if archivos_subidos:
    lista_df = []
    
    for archivo in archivos_subidos:
        # 1. Leemos cada archivo sin encabezados y nombramos las columnas
        df = pd.read_excel(archivo, header=None, usecols=[0, 1], names=['Nombre', 'Importe'])
        
        # 2. Limpiamos los nombres (mayúsculas y sin espacios a los lados) para evitar duplicados
        df['Nombre'] = df['Nombre'].astype(str).str.upper().str.strip()
        
        # 3. ¡MUY IMPORTANTE! Guardamos el dataframe en la lista
        lista_df.append(df)
        
    if st.button("Generar Acumulado Total"):
        # Concatenar todo en una sola tabla
        df_total = pd.concat(lista_df, ignore_index=True)
        
        # Agrupar por nombre y obtener la suma de los pagos
        df_agrupado = df_total.groupby('Nombre', as_index=False)['Importe'].sum()
        
        st.success("¡Nóminas procesadas!")
        st.dataframe(df_agrupado) # Muestra una vista previa en la pantalla
        
        # Opción para descargar
        @st.cache_data
        def convert_df(df):
            return df.to_csv(index=False).encode('utf-8')
            
        csv = convert_df(df_agrupado)
        st.download_button(
            label="Descargar Acumulado (.csv)",
            data=csv,
            file_name='Acumulado_Total.csv',
            mime='text/csv',
        )

