#!/usr/bin/env python
# coding: utf-8

# In[ ]:


import streamlit as st
import pandas as pd

st.title("Consolidador de Nóminas (Modo Aspiradora)")

archivos_subidos = st.file_uploader("Sube todas las nóminas aquí (Excel)", type=["xlsx"], accept_multiple_files=True)

if archivos_subidos:
    lista_df = []
    
    for archivo in archivos_subidos:
        # sheet_name=None lee TODAS las hojas y devuelve un diccionario {Nombre_Hoja: Datos}
        diccionario_hojas = pd.read_excel(archivo, sheet_name=None, header=None)
        
        datos_de_este_archivo = []
        
        # Iteramos sobre cada hoja del Excel actual
        for nombre_hoja, df in diccionario_hojas.items():
            pat_col, mat_col, nom_col, imp_col = None, None, None, None
            
            for col in df.columns:
                col_str = df[col].astype(str).str.lower()
                if col_str.str.contains('paterno', na=False).any(): pat_col = col
                if col_str.str.contains('materno', na=False).any(): mat_col = col
                if col_str.str.contains('nombre', na=False).any(): nom_col = col
                if col_str.str.contains('importe|neto a pagar', na=False).any(): imp_col = col
                
            if nom_col is not None and imp_col is not None:
                nombres = pd.Series("", index=df.index)
                if pat_col is not None: nombres += df[pat_col].fillna("").astype(str) + " "
                if mat_col is not None: nombres += df[mat_col].fillna("").astype(str) + " "
                nombres += df[nom_col].fillna("").astype(str)
                
                temp_df = pd.DataFrame({'Nombre': nombres, 'Importe': df[imp_col]})
                
                # Limpieza
                temp_df['Importe'] = pd.to_numeric(temp_df['Importe'], errors='coerce')
                temp_df = temp_df.dropna(subset=['Importe'])
                temp_df = temp_df[~temp_df['Nombre'].str.contains('nombre', case=False, na=False)]
                temp_df = temp_df[temp_df['Nombre'].str.contains('[A-Za-z]', na=False)]
                temp_df['Nombre'] = temp_df['Nombre'].str.replace(r'\s+', ' ', regex=True).str.strip().str.upper()
                
                datos_de_este_archivo.append(temp_df)
        
        # Si logramos extraer datos de alguna hoja de este archivo, los consolidamos
        if datos_de_este_archivo:
            # Juntamos todas las hojas de este archivo en una sola tabla temporal
            df_archivo_completo = pd.concat(datos_de_este_archivo, ignore_index=True)
            
            # ELIMINAMOS DUPLICADOS EXACTOS dentro del mismo archivo para evitar sumar la hoja de "Resumen"
            df_archivo_completo = df_archivo_completo.drop_duplicates(subset=['Nombre', 'Importe'])
            
            # Ahora sí, guardamos los datos limpios de este Excel en la lista general
            lista_df.append(df_archivo_completo)

    if st.button("Generar Acumulado Total"):
        if lista_df:
            # Unimos TODOS los archivos
            df_total = pd.concat(lista_df, ignore_index=True)
            
            # Suma final general: agrupamos por nombre y sumamos sus distintos pagos a lo largo de las semanas
            df_agrupado = df_total.groupby('Nombre', as_index=False)['Importe'].sum()
            
            st.success("¡Extracción y consolidación completadas!")
            st.dataframe(df_agrupado)
            
            @st.cache_data
            def convert_df(df):
                return df.to_csv(index=False).encode('utf-8')
                
            st.download_button("Descargar Acumulado (.csv)", data=convert_df(df_agrupado), file_name='Acumulado_Total.csv', mime='text/csv')
        else:
            st.error("No se detectaron columnas de nombres o importes válidos en los archivos.")

