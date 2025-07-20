# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations

# Configuración de la página
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# Encabezados esperados en el Excel y mapa de estados
columnas_esperadas = [
    'B (Boron)', 'Ca (Calcium)', 'Mg (Magnesium)', 'P (Phosphorus)', 'Zn (Zinc)',
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)',
    'PQ Index', 'Report Status', 'Date Reported', 'Unit ID', 'Tested Lubricant',
    'Manufacturer', 'Alt Model', 'Account Name', 'Parent Account Name', 'Equipment Age',
    'Oil Age', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)', 'TAN (mg KOH/g)',
    'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um', 'Particle Count  >6um',
    'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]
status_map = {'*': 'Alert', '+': 'Caution', '': 'Normal'}

# Título e instrucciones
st.title("📊 Análisis de Flotas de Equipos - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos históricos de flotas específicas.

    ✅ **Importante:** el archivo Excel debe estar filtrado (un único modelo) y usar formato **Mobil Serv**.
    """
)

# Carga del archivo
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        # Leer y validar columnas básicas
        df = pd.read_excel(archivo)
        falt = sorted(set(columnas_esperadas) - set(df.columns))
        if falt:
            st.error("❌ Faltan columnas requeridas:")
            st.code("\n".join(falt))
            st.stop()

        # Convertir 'Date Reported' a datetime
        df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

        # Detectar y mapear columnas RESULT_
        result_cols = [c for c in df.columns if c.startswith('RESULT_')]
        for col in result_cols:
            df[col + '_status'] = (
                df[col].astype(str)
                     .str.strip()
                     .map(lambda x: status_map.get(x, 'Normal'))
            )

        # Métricas generales
        total = len(df)
        lubs = df['Tested Lubricant'].nunique()
        ops = df['Account Name'].nunique()
        fecha_min = df['Date Reported'].min().date()
        fecha_max = df['Date Reported'].max().date()
        equipos = df['Unit ID'].nunique()

        # Calcular intervalo medio global
        df_sorted = df.sort_values(['Unit ID','Date Reported'])
        mean_int = df_sorted.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
        overall_mean = mean_int.mean()

        # Resumen general
        st.subheader("🔎 Resumen general")
        texto_resumen = (
            f"- Total muestras: **{total}**  \n"
            f"- Lubricantes distintos: **{lubs}**  \n"
            f"- Operaciones distintas: **{ops}**  \n"
            f"- Rango fechas: **{fecha_min}** a **{fecha_max}**  \n"
            f"- Equipos distintos: **{equipos}**  \n"
            f"- Intervalo medio de muestreo: **{overall_mean:.1f}** días"
        )
        st.markdown(texto_resumen)

        # Gráficos en 3 filas x 2 columnas
        # Fila 1: Estados y Frecuencia de muestreo
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.subheader("📈 Estados de muestras")
            conteo = df['Report Status'].value_counts()
            orden = ['Normal', 'Caution', 'Alert']
            vals = [conteo.get(o, 0) for o in orden]
            labels = ['🟢 Normal', '🟡 Caution', '🔴 Alert']
            colors = ['#2ecc71', '#f1c40f', '#e74c3c']
            fig1, ax1 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=labels, y=vals, palette=colors, ax=ax1)
            ax1.set_ylabel('Cantidad de muestras')
            ax1.spines[['top','right']].set_visible(False)
            for p in ax1.patches:
                ax1.annotate(int(p.get_height()), (p.get_x()+p.get_width()/2, p.get_height()), ha='center', va='bottom')
            st.pyplot(fig1)
        with r1c2:
            st.subheader("📊 Frec. muestreo: Top 15 equipos")
            top15 = df['Unit ID'].value_counts().head(15)
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=top15.values, y=top15.index, palette='Blues_r', ax=ax2)
            ax2.set_xlabel('Número de muestras')
            ax2.spines[['top','right']].set_visible(False)
            for p in ax2.patches:
                ax2.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            st.pyplot(fig2)

        # Fila 2: Intervalos promedio Top 15 y Pareto Alert
        r2c1, r2c2 = st.columns(2)
        with r2c1:
            st.subheader("⏱️ Intervalo promedio: Top 15 equipos")
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
            alert_ser = (
                pd.Series({col.replace('RESULT_',''): (df[col+'_status']=='Alert').sum() for col in result_cols})
                  .sort_values(ascending=False)
                  .head(10)
            )
            fig4, ax4 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=alert_ser.values, y=alert_ser.index, color='#e74c3c', ax=ax4)
            ax4.set_xlabel('Número de Alert')
            ax4.spines[['top','right']].set_visible(False)
            for p in ax4.patches:
                ax4.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            # Línea acumulada
            cum4 = alert_ser.cumsum() / alert_ser.sum() * 100
            ax4_line = ax4.twiny()
            ax4_line.plot(cum4.values, cum4.index, '-o', color='#3498db')
            ax4_line.set_xlabel('Porcentaje acumulado')
            ax4_line.spines[['top','right']].set_visible(False)
            for x, y in zip(cum4.values, cum4.index):
                ax4_line.annotate(f"{x:.0f}%", (x, y), textcoords='offset points', xytext=(5,0), fontsize=8)
            st.pyplot(fig4)

        # Fila 3: Pareto Caution y combos Alert
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
            caution_ser = (
                pd.Series({col.replace('RESULT_',''): (df[col+'_status']=='Caution').sum() for col in result_cols})
                  .sort_values(ascending=False)
                  .head(10)
            )
            fig5, ax5 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=caution_ser.values, y=caution_ser.index, color='#f1c40f', ax=ax5)
            ax5.set_xlabel('Número de Caution')
            ax5.spines[['top','right']].set_visible(False)
            for p in ax5.patches:
                ax5.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            cum5 = caution_ser.cumsum() / caution_ser.sum() * 100
            ax5_line = ax5.twiny()
            ax5_line.plot(cum5.values, cum5.index, '-o', color='#2c3e50')
            ax5_line.set_xlabel('Porcentaje acumulado')
            ax5_line.spines[['top','right']].set_visible(False)
            for x, y in zip(cum5.values, cum5.index):
                ax5_line.annotate(f"{x:.0f}%", (x, y), textcoords='offset points', xytext=(5,0), fontsize=8)
            st.pyplot(fig5)
        with r3c2:
            st.subheader("🔗 Pareto: combos Alert (Top 10)")
            comb_counts = {}
            for _, row in df.iterrows():
                alerts = [c.replace('RESULT_','') for c in result_cols if row[c+'_status']=='Alert']
                if len(alerts) > 1:
                    for combo in combinations(alerts, 2):
                        key = ' & '.join(combo)
                        comb_counts[key] = comb_counts.get(key, 0) + 1
            comb_ser = pd.Series(comb_counts).sort_values(ascending=False).head(10)
            fig6, ax6 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=comb_ser.values, y=comb_ser.index, color='#c0392b', ax=ax6)
            ax6.set_xlabel('Número de muestras')
            ax6.spines[['top','right']].set_visible(False)
            for p in ax6.patches:
                ax6.annotate(int(p.get_width()), (p.get_width()+0.5, p.get_y()+p.get_height()/2), va='center')
            cum6 = comb_ser.cumsum() / comb_ser.sum() * 100
            ax6_line = ax6.twiny()
            ax6_line.plot(cum6.values, cum6.index, '-o', color='#16a085')
            ax6_line.set_xlabel('Porcentaje acumulado')
            ax6_line.spines[['top','right']].set_visible(False)
            for x, y in zip(cum6.values, cum6.index):
                ax6_line.annotate(f"{x:.0f}%", (x, y), textcoords='offset points', xytext=(5,0), fontsize

