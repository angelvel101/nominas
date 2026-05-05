#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd

st.title("Consolidador de Nóminas")

archivos_subidos = st.file_uploader("Sube todas las nóminas aquí (Excel)", type=["xlsx"], accept_multiple_files=True)

if archivos_subidos:
    lista_df = []
    
    for archivo in archivos_subidos:
        # 1. Leemos ÚNICAMENTE la primera hoja (sheet_name=0)
        df = pd.read_excel(archivo, sheet_name=0, header=None)
        
        pat_col, mat_col, nom_col, imp_col = None, None, None, None
        
        # 2. Escaneamos la ubicación de las columnas
        for col in df.columns:
            col_str = df[col].astype(str).str.lower()
            if col_str.str.contains('paterno', na=False).any(): pat_col = col
            if col_str.str.contains('materno', na=False).any(): mat_col = col
            if col_str.str.contains('nombre', na=False).any(): nom_col = col
            if col_str.str.contains('importe|neto a pagar', na=False).any(): imp_col = col
            
        if nom_col is not None and imp_col is not None:
            # 3. Armamos el nombre completo
            nombres = pd.Series("", index=df.index)
            if pat_col is not None: nombres += df[pat_col].fillna("").astype(str) + " "
            if mat_col is not None: nombres += df[mat_col].fillna("").astype(str) + " "
            nombres += df[nom_col].fillna("").astype(str)
            
            temp_df = pd.DataFrame({'Nombre': nombres, 'Importe': df[imp_col]})
            
            # 4. Limpieza (Forzar números y quitar filas de texto basura)
            temp_df['Importe'] = pd.to_numeric(temp_df['Importe'], errors='coerce')
            temp_df = temp_df.dropna(subset=['Importe'])
            temp_df = temp_df[~temp_df['Nombre'].str.contains('nombre', case=False, na=False)]
            temp_df = temp_df[temp_df['Nombre'].str.contains('[A-Za-z]', na=False)]
            
            # Formato estándar para que sume bien: Todo a mayúsculas y sin dobles espacios
            temp_df['Nombre'] = temp_df['Nombre'].str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
            
            # ¡Ya no eliminamos duplicados! Si alguien aparece 3 veces, las 3 se van a la lista.
            lista_df.append(temp_df)

    if st.button("Generar Acumulado Total"):
        if lista_df:
            # Unimos la información extraída de todos los archivos
            df_total = pd.concat(lista_df, ignore_index=True)
            
            # El groupby automáticamente suma TODOS los importes del mismo nombre
            df_agrupado = df_total.groupby('Nombre', as_index=False)['Importe'].sum()
            
            st.success("¡Extracción y consolidación completadas!")
            st.dataframe(df_agrupado)
            
            @st.cache_data
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')
                
            st.download_button(
                label="Descargar Acumulado (.csv)", 
                data=convert_df(df_agrupado), 
                file_name='Acumulado_Total.csv', 
                mime='text/csv'
            )
        else:
            st.error("No se detectaron columnas de nombres o importes válidos en los archivos subidos.")
