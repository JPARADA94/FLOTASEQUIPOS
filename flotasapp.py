# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations

# Configuración de la página
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# Encabezados esperados
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
# Mapa para RESULT_ columnas
status_map = {'*':'Alert', '+':'Caution', '':'Normal'}

# Título e instrucciones
st.title("📊 Análisis de Flotas de Equipos - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos históricos de flotas específicas.

    ✅ **Importante:** el archivo Excel debe estar filtrado (un solo modelo) y usar formato **Mobil Serv**.
    """
)

# Subida de archivo
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        # Leer y validar
        df = pd.read_excel(archivo)
        if not set(columnas_esperadas).issubset(df.columns):
            faltantes = sorted(set(columnas_esperadas) - set(df.columns))
            st.error("❌ Faltan columnas:")
            st.code("\n".join(faltantes)); st.stop()

        # Convertir fechas
        df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

        # Detectar y mapear columnas RESULT_
        result_cols = [c for c in df.columns if c.startswith('RESULT_')]
        for col in result_cols:
            df[col + '_status'] = df[col].astype(str).str.strip().map(lambda x: status_map.get(x, 'Normal'))

        # Métricas generales
        total = len(df)
        lubs = df['Tested Lubricant'].nunique()
        ops = df['Account Name'].nunique()
        fecha_min = df['Date Reported'].min().date()
        fecha_max = df['Date Reported'].max().date()
        equipos = df['Unit ID'].nunique()

        st.subheader("🔎 Resumen general")
        st.markdown(
            f"- Total muestras: **{total}**\n"
            f"- Lubricantes distintos: **{lubs}**\n"
            f"- Operaciones distintas: **{ops}**\n"
            f"- Rango fechas: **{fecha_min}** a **{fecha_max}**\n"
            f"- Equipos distintos: **{equipos}**"
        )

        # Primera fila: Estados y Frecuencia
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.subheader("📈 Estados de muestras")
            conteo = df['Report Status'].value_counts()
            estados = ['Normal', 'Caution', 'Alert']
            valores = [conteo.get(e, 0) for e in estados]
            etiquetas = ['🟢 Normal', '🟡 Caution', '🔴 Alert']
            colores = ['#2ecc71', '#f1c40f', '#e74c3c']
            fig1, ax1 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=etiquetas, y=valores, palette=colores, ax=ax1)
            ax1.set_ylabel('Cantidad')
            ax1.spines[['top','right']].set_visible(False)
            for p in ax1.patches:
                ax1.annotate(int(p.get_height()), (p.get_x()+p.get_width()/2, p.get_height()), ha='center')
            st.pyplot(fig1)
        with r1c2:
            st.subheader("📊 Frec. muestreo: Top 15 equipos")
            top15 = df['Unit ID'].value_counts().head(15)
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=top15.values, y=top15.index, palette='Blues_r', ax=ax2)
            ax2.set_xlabel('N° muestras')
            ax2.spines[['top','right']].set_visible(False)
            for p in ax2.patches:
                ax2.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            st.pyplot(fig2)

        # Segunda fila: Intervalos y Pareto Alert
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.subheader("⏱️ Intervalo promedio: Top 15")
            df_sorted = df.sort_values(['Unit ID', 'Date Reported'])
            mean_int = df_sorted.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
            mean_top = mean_int.loc[top15.index].dropna()
            fig3, ax3 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=mean_top.values, y=mean_top.index, palette='mako', ax=ax3)
            ax3.set_xlabel('Días promedio')
            ax3.spines[['top','right']].set_visible(False)
            for p in ax3.patches:
                ax3.annotate(f"{p.get_width():.1f}", (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            st.pyplot(fig3)
        with r2c2:
            st.subheader("📋 Pareto: Alert por parámetro (Top 10)")
            alert_ser = pd.Series({col: (df[col+'_status']=='Alert').sum() for col in result_cols})
            alert_ser = alert_ser.sort_values(ascending=False).head(10)
            fig4, ax4 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=alert_ser.values, y=alert_ser.index, color='#e74c3c', ax=ax4)
            ax4.set_xlabel('N Alert')
            ax4.spines[['top','right']].set_visible(False)
            for p in ax4.patches:
                ax4.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            st.pyplot(fig4)

        # Tercera fila: Pareto Caution y combos Alert
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
            caution_ser = pd.Series({col: (df[col+'_status']=='Caution').sum() for col in result_cols})
            caution_ser = caution_ser.sort_values(ascending=False).head(10)
            fig5, ax5 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=caution_ser.values, y=caution_ser.index, color='#f1c40f', ax=ax5)
            ax5.set_xlabel('N Caution')
            ax5.spines[['top','right']].set_visible(False)
            for p in ax5.patches:
                ax5.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            st.pyplot(fig5)
        with r3c2:
            st.subheader("🔗 Pareto: combos Alert (Top 10)")
            comb_counts = {}
            for _, row in df.iterrows():
                al = [c for c in result_cols if row[c+'_status']=='Alert']
                if len(al)>1:
                    for combo in combinations(sorted(al), 2):
                        key = ' & '.join(combo)
                        comb_counts[key] = comb_counts.get(key, 0) + 1
            comb_ser = pd.Series(comb_counts).sort_values(ascending=False).head(10)
            fig6, ax6 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=comb_ser.values, y=comb_ser.index, color='#c0392b', ax=ax6)
            ax6.set_xlabel('N muestras')
            ax6.spines[['top','right']].set_visible(False)
            for p in ax6.patches:
                ax6.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            st.pyplot(fig6)

    except Exception as e:
        st.error(f"❌ Error al procesar archivo: {e}")





