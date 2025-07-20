# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

# ---------------------------------------------
# 1. IMPORTACIÓN DE LIBRERÍAS NECESARIAS
# ---------------------------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# ---------------------------------------------
# 2. CONFIGURACIÓN INICIAL DE LA APLICACIÓN
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# ---------------------------------------------
# 3. LISTA DE NOMBRES DE COLUMNAS ESPERADAS (no códigos)
# ---------------------------------------------
columnas_esperadas = [
    'B (Boron)', 'Ca (Calcium)', 'Mg (Magnesium)', 'P (Phosphorus)', 'Zn (Zinc)',
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index',
    'Report Status', 'Date Reported', 'Unit ID', 'Tested Lubricant', 'Manufacturer', 'Alt Model',
    'Account Name', 'Parent Account Name', 'Equipment Age', 'Oil Age', 'Oxidation (Ab/cm)',
    'TBN (mg KOH/g)', 'Visc@100C (cSt)', 'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)',
    'Particle Count  >4um', 'Particle Count  >6um', 'Particle Count>14um',
    'Visc@40C (cSt)', 'Soot (Wt%)'
]

# Lista de columnas consideradas para desgaste
columnas_desgaste = ['Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index']

# ---------------------------------------------
# 4. TÍTULO Y DESCRIPCIÓN DE LA APLICACIÓN
# ---------------------------------------------
st.title("📊 Análisis de Datos de Flotas de Equipos - Mobil Serv")
st.markdown("""
Esta aplicación permite analizar datos históricos de flotas específicas de equipos.

✅ **Importante:** el archivo Excel debe estar previamente filtrado (por ejemplo, solo motores de un mismo modelo) y en formato **Mobil Serv**, con columnas correctamente estructuradas.
""")

# ---------------------------------------------
# 5. CARGA DEL ARCHIVO EXCEL
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel en formato Mobil Serv", type=["xlsx"])

# ---------------------------------------------
# 6. PROCESAMIENTO Y VALIDACIÓN
# ---------------------------------------------
if archivo:
    try:
        df = pd.read_excel(archivo)
        columnas_archivo = set(df.columns.astype(str))
        columnas_requeridas = set(columnas_esperadas)

        # Verificar si todas las columnas requeridas están presentes
        if columnas_requeridas.issubset(columnas_archivo):
            st.success("✅ Archivo válido. Formato Mobil Serv reconocido.")
            st.subheader("Vista previa de los primeros registros")
            st.dataframe(df.head())

            # Reemplazar vacíos por 0 en columnas de desgaste y convertir a número
            for col in columnas_desgaste:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].fillna(0), errors='coerce')

            # Validar columnas con pocos datos
            columnas_invalidas = []
            for col in df.columns:
                if df[col].notna().sum() < 5:
                    columnas_invalidas.append((col, df[col].notna().sum()))

            # Mostrar columnas ignoradas en un menú desplegable
            if columnas_invalidas:
                with st.expander("📋 Columnas ignoradas por tener pocos datos válidos"):
                    for col, count in columnas_invalidas:
                        st.markdown(f"• **{col}**: {count} datos válidos")

            # ---------------------------------------------
            # 7. GRÁFICO DE ESTADOS DE REPORTE
            # ---------------------------------------------
            st.subheader("📈 Estado general de las muestras")
            if 'Report Status' in df.columns:
                conteo_estados = df['Report Status'].value_counts()
                etiquetas = {'Normal': '🟢 Normal', 'Precaution': '🟡 Precaución', 'Abnormal': '🔴 Alerta'}
                estados = [etiquetas.get(k, k) for k in conteo_estados.index]

                fig, ax = plt.subplots(figsize=(4, 3))
                ax.bar(estados, conteo_estados.values, color=['green', 'orange', 'red'])
                ax.set_ylabel("Cantidad de muestras")
                ax.set_title("Distribución por estado")
                st.pyplot(fig)

                # Nota interpretativa
                st.markdown("""
                🔍 **Nota**: La distribución de estados permite identificar el porcentaje de muestras en condiciones críticas o que requieren atención.  
                Se recomienda revisar los equipos en estado 🟡 *Precaución* y 🔴 *Alerta* para priorizar acciones de mantenimiento.
                """)
            else:
                st.error("No se encontró la columna 'Report Status'.")

        else:
            columnas_faltantes = columnas_requeridas - columnas_archivo
            st.error("❌ Archivo inválido. Faltan las siguientes columnas requeridas:")
            st.code("\n".join(sorted(columnas_faltantes)))
            st.info("Asegúrate de que tu archivo esté estructurado como formato Mobil Serv.")

    except Exception as e:
        st.error(f"❌ Error al procesar el archivo: {str(e)}")
