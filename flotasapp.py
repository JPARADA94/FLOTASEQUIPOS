# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Aplicación Streamlit para análisis de datos de flotas basada en formato Mobil Serv

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations

# ---------------------------------------------
# Configuración de la página
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# ---------------------------------------------
# Estilos personalizados
# ---------------------------------------------
st.markdown("""
<style>
  .stApp { background-color: #f5f5f5; }
  .block {
    padding: 1rem;
    margin: 1rem 0;
    border: 1px solid #DDDDDD;
    border-radius: 8px;
    background-color: #FFFFFF;
  }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------
# Encabezados esperados y mapeo de estados
# ---------------------------------------------
columnas_esperadas = [
    'B (Boron)', 'Ca (Calcium)', 'Mg (Magnesium)', 'P (Phosphorus)', 'Zn (Zinc)',
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)',
    'PQ Index', 'Report Status', 'Date Reported', 'Unit ID', 'Tested Lubricant',
    'Manufacturer', 'Alt Model', 'Account Name', 'Parent Account Name', 'Equipment Age',
    'Oil Age', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)', 'TAN (mg KOH/g)',
    'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um', 'Particle Count  >6um',
    'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)', 'Asset Class'
]
status_map = {'*': 'Alert', '+': 'Caution', '': 'Normal'}

# ---------------------------------------------
# Variables disponibles para correlación e intervalos
# ---------------------------------------------
vars_correl = [
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)',
    'Pb (Lead)', 'PQ Index', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)',
    'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
    'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]

# ---------------------------------------------
# Título e instrucciones
# ---------------------------------------------
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown(
    """
    **Autor:** Javier Parada - Ingeniero de soporte en campo  \
    **Fecha de creación:** 2025-07-20
    """
)
st.markdown(
    """
    Esta aplicación permite analizar datos históricos de flotas.  
    ✅ **Importante:** el archivo Excel debe estar filtrado (un único tipo de equipo) y seguir el formato **Mobil Serv**.
    """
)

# ---------------------------------------------
# Paso 1: Carga del archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.info("Espera a subir un archivo para comenzar.")
    st.stop()

df_raw = pd.read_excel(archivo)
# Validar columnas faltantes
missing_cols = sorted(set(columnas_esperadas) - set(df_raw.columns))
if missing_cols:
    st.error("❌ Faltan columnas en el archivo:")
    st.code("\n".join(missing_cols))
    st.stop()

# ---------------------------------------------
# Paso 2: Selección de cuenta(s)
# ---------------------------------------------
cuentas = df_raw['Account Name'].unique().tolist()
seleccion_cuentas = st.multiselect("Selecciona la(s) cuenta(s) a analizar:", cuentas, default=cuentas)
if not seleccion_cuentas:
    st.warning("Debes seleccionar al menos una cuenta.")
    st.stop()
df_cuentas = df_raw[df_raw['Account Name'].isin(seleccion_cuentas)].copy()

# ---------------------------------------------
# Paso 3: Selección de clase(s) de equipo
# ---------------------------------------------
clases = df_cuentas['Asset Class'].unique().tolist()
seleccion_clases = st.multiselect("Selecciona la(s) clase(s) de equipo:", clases, default=clases)
if not seleccion_clases:
    st.warning("Debes seleccionar al menos una clase de equipo.")
    st.stop()
df_clases = df_cuentas[df_cuentas['Asset Class'].isin(seleccion_clases)].copy()

# ---------------------------------------------
# Paso 4: Selección de lubricante(s)
# ---------------------------------------------
lubricantes = df_clases['Tested Lubricant'].unique().tolist()
seleccion_lub = st.multiselect("Selecciona el/los lubricante(s):", lubricantes, default=lubricantes)
if not seleccion_lub:
    st.warning("Debes seleccionar al menos un lubricante.")
    st.stop()

df = df_clases[df_clases['Tested Lubricant'].isin(seleccion_lub)].copy()

# ---------------------------------------------
# Paso 5: Botón para iniciar análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    # Preparar datos
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')
    for col in vars_correl:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[^0-9\.\-]", "", regex=True), errors='coerce')
    result_cols = [c for c in df.columns if c.startswith('RESULT_')]
    for c in result_cols:
        df[c + '_status'] = df[c].astype(str).str.strip().map(lambda x: status_map.get(x, 'Normal'))

    # Métricas generales
    total = len(df)
    lubs = df['Tested Lubricant'].nunique()
    ops = df['Account Name'].nunique()
    fecha_min = df['Date Reported'].min().date()
    fecha_max = df['Date Reported'].max().date()
    equipos = df['Unit ID'].nunique()
    df_sorted = df.sort_values(['Unit ID', 'Date Reported'])
    mean_int = df_sorted.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
    overall_mean = mean_int.mean()

    # Resumen general
    st.subheader("🔎 Resumen general")
    st.markdown(f"""
- Total muestras: **{total}**  
- Lubricantes distintos: **{lubs}**  
- Operaciones distintas: **{ops}**  
- Rango de fechas: **{fecha_min}** a **{fecha_max}**  
- Equipos distintos: **{equipos}**  
- Intervalo medio de muestreo: **{overall_mean:.1f}** días
"""
    )
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total muestras", total)
    c2.metric("Equipos analizados", equipos)
    c3.metric("Lubricantes distintos", lubs)
    c4.metric("Intervalo medio (días)", f"{overall_mean:.1f}")

    # ---------------------------------------------
    # Gráficos fila 1: Muestras por cuenta y estados
    # ---------------------------------------------
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.subheader("🍰 Muestras por cuenta")
        cuenta_counts = df['Account Name'].value_counts()
        fig1, ax1 = plt.subplots(figsize=(4, 3))
        ax1.pie(cuenta_counts.values, labels=cuenta_counts.index, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor':'white'})
        ax1.axis('equal')
        st.pyplot(fig1)
    with r1c2:
        st.subheader("📊 Estados de muestras")
        status_counts = df['Report Status'].value_counts().reindex(['Normal', 'Caution', 'Alert']).fillna(0)
        colors = {'Normal':'#2ecc71', 'Caution':'#f1c40f', 'Alert':'#e74c3c'}
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        ax2.bar(status_counts.index, status_counts.values, color=[colors[s] for s in status_counts.index])
        ax2.set_ylabel('Cantidad de muestras')
        for i, v in enumerate(status_counts.values):
            ax2.text(i, v + max(status_counts.values)*0.01, str(int(v)), ha='center')
        st.pyplot(fig2)

    # Aquí continuarían los gráficos de filas 2 y 3...
else:
    st.info("Configura los filtros y haz clic en '🚀 Empezar análisis' para ver resultados.")

