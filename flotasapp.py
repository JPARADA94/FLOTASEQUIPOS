# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

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
# Validar columnas
afalt = sorted(set(columnas_esperadas) - set(df_raw.columns))
if falt:
    st.error("❌ Faltan columnas en el archivo:")
    st.code("\n".join(falt))
    st.stop()

# ---------------------------------------------
# Paso 2: Selección de cuenta(s)
# ---------------------------------------------
cuentas = df_raw['Account Name'].unique().tolist()
seleccion_cuentas = st.multiselect(
    "Selecciona la(s) cuenta(s) a analizar:", cuentas, default=cuentas
)
if not seleccion_cuentas:
    st.warning("Debes seleccionar al menos una cuenta.")
    st.stop()
df_cuentas = df_raw[df_raw['Account Name'].isin(seleccion_cuentas)].copy()

# ---------------------------------------------
# Paso 3: Selección de clase(s) de equipo
# ---------------------------------------------
clases = df_cuentas['Asset Class'].unique().tolist()
seleccion_clases = st.multiselect(
    "Selecciona la(s) clase(s) de equipo:", clases, default=clases
)
if not seleccion_clases:
    st.warning("Debes seleccionar al menos una clase de equipo.")
    st.stop()
df_clases = df_cuentas[df_cuentas['Asset Class'].isin(seleccion_clases)].copy()

# ---------------------------------------------
# Paso 4: Selección de lubricante(s)
# ---------------------------------------------
lubricantes = df_clases['Tested Lubricant'].unique().tolist()
seleccion_lub = st.multiselect(
    "Selecciona el/los lubricante(s):", lubricantes, default=lubricantes
)
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
            df[col] = pd.to_numeric(
                df[col].astype(str).str.replace(r"[^0-9\.\-]", "", regex=True),
                errors='coerce'
            )
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

    # Gráficos fijos (3 filas x 2 columnas)
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.subheader("📈 Estados de muestras")
        vc = df['Report Status'].value_counts()
        orden = ['Normal', 'Caution', 'Alert']
        vals = [vc.get(o, 0) for o in orden]
        fig1, ax1 = plt.subplots(figsize=(4,3))
        ax1.bar(orden, vals)
        ax1.set_ylabel('Cantidad de muestras')
        for i, v in enumerate(vals): ax1.text(i, v+2, str(v), ha='center')
        st.pyplot(fig1)
    with r1c2:
        st.subheader("📊 Frecuencia de muestreo (Top 15 equipos)")
        top15 = df['Unit ID'].value_counts().head(15)
        fig2, ax2 = plt.subplots(figsize=(4,3))
        ax2.barh(top15.index, top15.values)
        ax2.set_xlabel('Número de muestras')
        for i, v in enumerate(top15.values): ax2.text(v+1, i, str(v), va='center')
        st.pyplot(fig2)

    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.subheader("⏱️ Intervalo promedio (Top 15 equipos)")
        mean_top = mean_int.loc[top15.index].dropna()
        fig3, ax3 = plt.subplots(figsize=(4,3))
        ax3.barh(mean_top.index, mean_top.values)
        ax3.set_xlabel('Días promedio')
        for i, v in enumerate(mean_top.values): ax3.text(v+0.5, i, f"{v:.1f}", va='center')
        st.markdown(f"**Nota:** Promedio Top 15 = {mean_top.mean():.1f} días")
        st.pyplot(fig3)
    with r2c2:
        st.subheader("📋 Pareto: Alert por parámetro (Top 10)")
        alert_ser = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Alert').sum() for c in result_cols}).sort_values(ascending=False).head(10)
        fig4, ax4 = plt.subplots(figsize=(4,3))
        ax4.barh(alert_ser.index, alert_ser.values)
        ax4.invert_yaxis()
        ax4.set_xlabel('Número de Alertas')
        for i, v in enumerate(alert_ser.values): ax4.text(v+1, i, str(v), va='center')
        st.pyplot(fig4)

    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
        caut_ser = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Caution').sum() for c in result_cols}).sort_values(ascending=False).head(10)
        fig5, ax5 = plt.subplots(figsize=(4,3))
        ax5.barh(caut_ser.index, caut_ser.values)
        ax5.invert_yaxis()
        ax5.set_xlabel('Número de Cautions')
        for i, v in enumerate(caut_ser.values): ax5.text(v+1, i, str(v), va='center')
        st.pyplot(fig5)
    with r3c2:
        st.subheader("🔗 Pareto: combos Alert (Top 10)")
        combos = {}
        for _, row in df.iterrows():
            alerts = [c.replace('RESULT_','') for c in result_cols if row[c+'_status']=='Alert']
            if len(alerts)>1:
                for a,b in combinations(alerts,2):
                    combos[f"{a} & {b}"] = combos.get(f"{a} & {b}",0)+1
        comb_ser = pd.Series(combos).sort_values(ascending=False).head(10)
        fig6, ax6 = plt.subplots(figsize=(4,3))
        ax6.barh(comb_ser.index, comb_ser.values)
        ax6.invert_yaxis()
        ax6.set_xlabel('Número de muestras')
        for i, v in enumerate(comb_ser.values): ax6.text(v+1, i, str(v), va='center')
        st.pyplot(fig6)

else:
    st.info("Configura los filtros y haz clic en '🚀 Empezar análisis' para ver resultados.")

