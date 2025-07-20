# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

# ---------------------------------------------
# 1. IMPORTACIÓN DE LIBRERÍAS NECESARIAS
# ---------------------------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------
# 2. CONFIGURACIÓN INICIAL DE LA APLICACIÓN
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# ---------------------------------------------
# 3. LISTA DE ENCABEZADOS ESPERADOS
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

# Columnas de desgaste
columnas_desgaste = ['Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index']

# ---------------------------------------------
# 4. TÍTULO Y DESCRIPCIÓN
# ---------------------------------------------
st.title("📊 Análisis de Datos de Flotas de Equipos - Mobil Serv")
st.markdown("""
Esta aplicación permite analizar datos históricos de flotas específicas de equipos.

✅ **Importante:** el archivo Excel debe estar filtrado (por ejemplo, sólo un modelo) y usar formato **Mobil Serv**.
""")

# ---------------------------------------------
# 5. SUBIDA DE ARCHIVO
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx) en formato Mobil Serv", type=["xlsx"])

# ---------------------------------------------
# 6. PROCESAMIENTO Y MÉTRICAS GENERALES
# ---------------------------------------------
if archivo:
    try:
        df = pd.read_excel(archivo)
        cols = set(df.columns.astype(str))
        req = set(columnas_esperadas)

        if req.issubset(cols):
            # Métricas generales
            total_muestras = len(df)
            unique_lub = df['Tested Lubricant'].nunique()
            lubs = df['Tested Lubricant'].unique().tolist()
            unique_ops = df['Account Name'].nunique()
            ops = df['Account Name'].unique().tolist()
            df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')
            fecha_min = df['Date Reported'].min().date()
            fecha_max = df['Date Reported'].max().date()
            equipos = df['Unit ID'].nunique()

            # Mostrar resumen
            st.subheader("🔎 Resumen general de los datos")
            st.markdown(f"""
- **Total de muestras:** {total_muestras}
- **Lubricantes analizados:** {unique_lub}
- **Operaciones:** {unique_ops}
- **Rango de fechas:** {fecha_min} a {fecha_max}
- **Equipos analizados:** {equipos}
""")

            # Detalles en desplegables
            with st.expander("📦 Lista de lubricantes"):
                for lub in lubs:
                    st.write(f"• {lub}")
            with st.expander("🚩 Lista de operaciones"):
                for op in ops:
                    st.write(f"• {op}")

            # Validación de columnas de desgaste
            for col in columnas_desgaste:
                if col in df.columns:
                    df[col] = pd.to_numeric(df[col].fillna(0), errors='coerce')

            # Columnas con pocos datos
            invalidas = [(c, df[c].notna().sum()) for c in df.columns if df[c].notna().sum() < 5]
            if invalidas:
                with st.expander("📋 Columnas ignoradas (datos insuficientes)"):
                    for c, n in invalidas:
                        st.write(f"• {c}: {n} datos válidos")

            # ---------------------------------------------
            # 7. GRÁFICO 1: DISTRIBUCIÓN DE ESTADOS
            # ---------------------------------------------
            st.subheader("📈 Distribución por estado de las muestras")
            conteo = df['Report Status'].value_counts()
            estados = list(conteo.index)
            labels = {'Normal':'🟢 Normal','Precaution':'🟡 Precaución','Abnormal':'🔴 Alerta'}
            display = [labels.get(e,e) for e in estados]
            valores = conteo.values

            fig, ax = plt.subplots(figsize=(4,3))
            sns.barplot(x=display, y=valores, ax=ax)
            ax.set_title("Estados de muestras", fontsize=12)
            ax.set_ylabel("Cantidad")
            ax.set_xlabel("")
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            # Anotar valores
            for p in ax.patches:
                ax.annotate(int(p.get_height()), (p.get_x()+p.get_width()/2, p.get_height()),
                            ha='center', va='bottom', fontsize=10)
            st.pyplot(fig)

            # ---------------------------------------------
            # 8. GRÁFICO 2: FRECUENCIA DE MUESTREO POR EQUIPO
            # ---------------------------------------------
            st.subheader("📊 Frecuencia de muestreo: Top 20 equipos")
            counts = df['Unit ID'].value_counts().head(20)
            fig2, ax2 = plt.subplots(figsize=(5,4))
            sns.barplot(x=counts.values, y=counts.index, ax=ax2, orient='h')
            ax2.set_title("Top 20 equipos por número de muestras", fontsize=12)
            ax2.set_xlabel("Número de muestras")
            ax2.set_ylabel("")
            # Etiquetas horizontales
            for p in ax2.patches:
                ax2.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2),
                             va='center', fontsize=9)
            ax2.spines['top'].set_visible(False)
            ax2.spines['right'].set_visible(False)
            st.pyplot(fig2)

        else:
            faltantes = req - cols
            st.error("❌ Archivo inválido: faltan columnas:")
            st.code("\n".join(sorted(faltantes)))
            st.info("Asegúrate de usar el formato Mobil Serv completo.")

    except Exception as e:
        st.error(f"❌ Error al procesar archivo: {e}")
