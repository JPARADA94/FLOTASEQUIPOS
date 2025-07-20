# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

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
    'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]
status_map = {'*':'Alert', '+':'Caution', '':'Normal'}

# ---------------------------------------------
# Variables para relación
# ---------------------------------------------
heatmap_vars = [
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)',
    'Pb (Lead)', 'PQ Index', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)',
    'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
    'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]

# ---------------------------------------------
# Título y descripción
# ---------------------------------------------
st.title("📊 Análisis de Flotas de Equipos - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos históricos de flotas específicas.

    ✅ **Importante:** el archivo Excel debe estar filtrado (un único modelo) y usar formato **Mobil Serv**.
    """
)

# ---------------------------------------------
# Carga de archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.info("Espera a subir un archivo para comenzar el análisis.")
    st.stop()

# ---------------------------------------------
# Procesamiento principal
# ---------------------------------------------
try:
    # Leer y validar columnas
    df = pd.read_excel(archivo)
    falt = sorted(set(columnas_esperadas) - set(df.columns))
    if falt:
        st.error("❌ Faltan columnas requeridas:")
        st.code("\n".join(falt))
        st.stop()

    # Fechas
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

    # Mapear RESULT_
    result_cols = [c for c in df.columns if c.startswith('RESULT_')]
    for col in result_cols:
        df[col + '_status'] = df[col].astype(str).str.strip().map(lambda x: status_map.get(x,'Normal'))

    # Métricas
    total = len(df)
    lubs = df['Tested Lubricant'].nunique()
    ops = df['Account Name'].nunique()
    fecha_min = df['Date Reported'].min().date()
    fecha_max = df['Date Reported'].max().date()
    equipos = df['Unit ID'].nunique()

    # Intervalo medio global
    df_sorted = df.sort_values(['Unit ID','Date Reported'])
    mean_int = df_sorted.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
    overall_mean = mean_int.mean()

    # Resumen general
    st.subheader("🔎 Resumen general")
    resumen = (
        f"- Total muestras: **{total}**  \n"
        f"- Lubricantes distintos: **{lubs}**  \n"
        f"- Operaciones distintas: **{ops}**  \n"
        f"- Rango fechas: **{fecha_min}** a **{fecha_max}**  \n"
        f"- Equipos distintos: **{equipos}**  \n"
        f"- Intervalo medio de muestreo: **{overall_mean:.1f}** días"
    )
    st.markdown(resumen)

    # ------------------------------
    # Gráficos en 3 filas x 2 columnas
    # ------------------------------

    # Fila 1
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.subheader("📈 Estados de muestras")
        conteo = df['Report Status'].value_counts()
        orden = ['Normal','Caution','Alert']
        vals = [conteo.get(o,0) for o in orden]
        labels = ['🟢 Normal','🟡 Caution','🔴 Alert']
        colors = sns.color_palette('tab10',3)
        fig1, ax1 = plt.subplots(figsize=(4,3))
        ax1.bar(labels, vals, color=colors)
        ax1.set_ylabel('Cantidad de muestras')
        ax1.spines[['top','right']].set_visible(False)
        for i,v in enumerate(vals): ax1.text(i, v+1, str(v), ha='center')
        st.pyplot(fig1)
    with r1c2:
        st.subheader("📊 Frecuencia de muestreo: Top 15 equipos")
        top15 = df['Unit ID'].value_counts().head(15)
        colors2 = sns.color_palette('viridis',len(top15))
        fig2, ax2 = plt.subplots(figsize=(4,3))
        ax2.barh(top15.index, top15.values, color=colors2)
        ax2.set_xlabel('Número de muestras')
        ax2.spines[['top','right']].set_visible(False)
        for i,v in enumerate(top15.values): ax2.text(v+1, i, str(v), va='center')
        st.pyplot(fig2)

    # Fila 2
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.subheader("⏱️ Intervalo promedio: Top 15 equipos")
        mean_top = mean_int.loc[top15.index].dropna()
        fig3, ax3 = plt.subplots(figsize=(4,3))
        ax3.barh(mean_top.index, mean_top.values, color=sns.color_palette('mako',len(mean_top)))
        ax3.set_xlabel('Días promedio')
        ax3.spines[['top','right']].set_visible(False)
        for i,v in enumerate(mean_top.values): ax3.text(v+0.1, i, f"{v:.1f}", va='center')
        st.markdown(f"**Nota:** Intervalo medio Top 15 = {mean_top.mean():.1f} días")
        st.pyplot(fig3)
    with r2c2:
        st.subheader("📋 Pareto: Alert por parámetro (Top 10)")
        alert_ser = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Alert').sum() for c in result_cols})
        alert_ser = alert_ser.sort_values(ascending=False).head(10)
        colors4 = sns.color_palette('Reds', len(alert_ser))
        fig4, ax4 = plt.subplots(figsize=(4,3))
        alert_ser.plot.barh(color=colors4, ax=ax4)
        ax4.invert_yaxis()
        ax4.set_xlabel('Número de Alertas')
        ax4.set_title('Pareto: Alert por parámetro (Top 10)')
        ax4.grid(axis='x', linestyle='--', alpha=0.5)
        for i,(idx,v) in enumerate(alert_ser.items()): ax4.text(v+0.5, i, str(v), va='center')
        cum4 = alert_ser.cumsum()/alert_ser.sum()*100
        ax4_line = ax4.twiny()
        ax4_line.plot(cum4.values, range(len(cum4)), '-o', color='black')
        ax4_line.set_xlabel('Porcentaje acumulado')
        for i,pct in enumerate(cum4): ax4_line.text(pct+1, i, f"{pct:.0f}%", va='center')
        st.pyplot(fig4)

    # Fila 3
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
        caut_ser = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Caution').sum() for c in result_cols})
        caut_ser = caut_ser.sort_values(ascending=False).head(10)
        colors5 = sns.color_palette('YlOrBr', len(caut_ser))
        fig5, ax5 = plt.subplots(figsize=(4,3))
        caut_ser.plot.barh(color=colors5, ax=ax5)
        ax5.invert_yaxis()
        ax5.set_xlabel('Número de Cautions')
        ax5.set_title('Pareto: Caution por parámetro (Top 10)')
        ax5.grid(axis='x', linestyle='--', alpha=0.5)
        for i,(idx,v) in enumerate(caut_ser.items()): ax5.text(v+0.5, i, str(v), va='center')
        cum5 = caut_ser.cumsum()/caut_ser.sum()*100
        ax5_line = ax5.twiny()
        ax5_line.plot(cum5.values, range(len(cum5)), '-o', color='black')
        ax5_line.set_xlabel('Porcentaje acumulado')
        for i,pct in enumerate(cum5): ax5_line.text(pct+1, i, f"{pct:.0f}%", va='center')
        st.pyplot(fig5)
    with r3c2:
        st.subheader("🔗 Pareto: combos Alert (Top 10)")
        comb_counts = {}
        for _,row in df.iterrows():
            al = [c.replace('RESULT_','') for c in result_cols if row[c+'_status']=='Alert']
            if len(al)>1:
                for combo in combinations(al,2): comb_counts[' & '.join(combo)] = comb_counts.get(' & '.join(combo),0)+1
        comb_ser = pd.Series(comb_counts).sort_values(ascending=False).head(10)
        colors6 = sns.color_palette('PuRd', len(comb_ser))
        fig6, ax6 = plt.subplots(figsize=(4,3))
        comb_ser.plot.barh(color=colors6, ax=ax6)
        ax6.invert_yaxis()
        ax6.set_xlabel('Número de muestras')
        ax6.set_title('Pareto: combos Alert (Top 10)')
        ax6.grid(axis='x', linestyle='--', alpha=0.5)
        for i,(idx,v) in enumerate(comb_ser.items()): ax6.text(v+0.5, i, str(v), va='center')
        cum6 = comb_ser.cumsum()/comb_ser.sum()*100
        ax6_line = ax6.twiny()
        ax6_line.plot(cum6.values, range(len(cum6)), '-o', color='black')
        ax6_line.set_xlabel('Porcentaje acumulado')
        for i,pct in enumerate(cum6): ax6_line.text(pct+1, i, f"{pct:.0f}%", va='center')
        st.pyplot(fig6)

    # Relación de variables por pairplot
    st.subheader("🔍 Relación de variables seleccionadas")
    n_vars = st.number_input("¿Cuántas variables quieres relacionar?", min_value=2, max_value=len(heatmap_vars), value=2)
    vars_sel = st.multiselect("Selecciona las variables:", heatmap_vars, default=heatmap_vars[:n_vars])
    if len(vars_sel)==n_vars:
        st.info(f"Analizando: {', '.join(vars_sel)}")
        pair = sns.pairplot(df[vars_sel], diag_kind='kde', plot_kws={'alpha':0.6})
        st.pyplot(pair.fig)
    else:
        st.warning(f"Selecciona exactamente {n_vars} variables.")

except Exception as e:
    st.error(f"❌ Error al procesar archivo: {e}")
