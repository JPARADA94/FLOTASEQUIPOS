# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Aplicación Streamlit para análisis de datos de flotas basada en formato Mobil Serv

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations
import string

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
missing_cols = sorted(set(columnas_esperadas) - set(df_raw.columns))
if missing_cols:
    st.error("❌ Faltan columnas en el archivo:")
    st.code("\n".join(missing_cols))
    st.stop()

# ---------------------------------------------
# Paso 2: Selección de filtros básicos
# ---------------------------------------------
cuentas = df_raw['Account Name'].unique().tolist()
seleccion_cuentas = st.multiselect("Selecciona la(s) cuenta(s):", cuentas, default=cuentas)
if not seleccion_cuentas:
    st.warning("Selecciona al menos una cuenta.")
    st.stop()
df_cuentas = df_raw[df_raw['Account Name'].isin(seleccion_cuentas)]

clases = df_cuentas['Asset Class'].unique().tolist()
seleccion_clases = st.multiselect("Selecciona clase(s) de equipo:", clases, default=clases)
if not seleccion_clases:
    st.warning("Selecciona al menos una clase.")
    st.stop()
df_clases = df_cuentas[df_cuentas['Asset Class'].isin(seleccion_clases)]

lubricantes = df_clases['Tested Lubricant'].unique().tolist()
seleccion_lub = st.multiselect("Selecciona lubricante(s):", lubricantes, default=lubricantes)
if not seleccion_lub:
    st.warning("Selecciona al menos un lubricante.")
    st.stop()
df = df_clases[df_clases['Tested Lubricant'].isin(seleccion_lub)]

# ---------------------------------------------
# Paso final: Análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')
    for col in vars_correl:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[^0-9\.\-]", "", regex=True), errors='coerce')
    result_cols = [c for c in df.columns if c.startswith('RESULT_')]
    for c in result_cols:
        df[c + '_status'] = df[c].astype(str).map(lambda x: status_map.get(x.strip(), 'Normal'))

    # Métricas principales
    total = len(df)
    lubs = df['Tested Lubricant'].nunique()
    ops = df['Account Name'].nunique()
    equipos = df['Unit ID'].nunique()
    fecha_min = df['Date Reported'].min().date()
    fecha_max = df['Date Reported'].max().date()
    df_sorted = df.sort_values(['Unit ID', 'Date Reported'])
    mean_int = df_sorted.groupby('Unit ID')['Date Reported'].diff().dt.days.mean()

    # Tarjetas de resumen
    st.subheader("🔎 Resumen general")
    cols = st.columns(4)
    cols[0].metric("Muestras totales", total)
    cols[1].metric("Lubricantes distintos", lubs)
    cols[2].metric("Operaciones", ops)
    cols[3].metric("Equipos", equipos)

    # ---------------------------------------------
    # Gráficos fila 1: Muestras por cuenta y estados
    # ---------------------------------------------
    r1c1, r1c2 = st.columns(2)
    # Preparar datos de cuentas con letras
    cuenta_counts = df['Account Name'].value_counts()
    df_cuenta = cuenta_counts.reset_index()
    df_cuenta.columns = ['Cuenta', 'Muestras']
    df_cuenta['Letra'] = list(string.ascii_lowercase[:len(df_cuenta)])

    # Colores
    palette = sns.color_palette('tab10', len(df_cuenta))
    colores = [palette[i] for i in range(len(df_cuenta))]

    with r1c1:
        st.subheader("📊 Muestras por cuenta")
        fig1, ax1 = plt.subplots(figsize=(4,3))
        ax1.bar(df_cuenta['Letra'], df_cuenta['Muestras'], color=colores)
        ax1.set_xlabel('Cuenta')
        ax1.set_ylabel('Número de muestras')
        for i, v in enumerate(df_cuenta['Muestras']):
            ax1.text(i, v + max(df_cuenta['Muestras'])*0.01, str(v), ha='center')
        st.pyplot(fig1)
        # Tabla con letras
        df_table = df_cuenta[['Letra', 'Cuenta', 'Muestras']]
        st.table(df_table)

    with r1c2:
        st.subheader("📊 Estados de muestras")
        status_counts = df['Report Status'].value_counts().reindex(['Normal', 'Caution', 'Alert']).fillna(0)
        colores_status = {'Normal':'#2ecc71', 'Caution':'#f1c40f', 'Alert':'#e74c3c'}
        fig2, ax2 = plt.subplots(figsize=(4,3))
        ax2.bar(status_counts.index, status_counts.values, color=[colores_status[s] for s in status_counts.index])
        ax2.set_ylabel('Cantidad de muestras')
        for i, v in enumerate(status_counts.values):
            ax2.text(i, v + max(status_counts.values)*0.01, str(int(v)), ha='center')
        st.pyplot(fig2)

    # ... resto de filas ...
else:
    st.info("Configura los filtros y haz clic en '🚀 Empezar análisis' para ver resultados.")


