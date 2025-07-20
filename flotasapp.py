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
status_map = {'*': 'Alert', '+': 'Caution', '': 'Normal'}

# ---------------------------------------------
# Variables para relacionar
# ---------------------------------------------
heatmap_vars = [
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)',
    'Pb (Lead)', 'PQ Index', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)',
    'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
    'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]

# ---------------------------------------------
# Título
# ---------------------------------------------
st.title("📊 Análisis de Flotas de Equipos - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos históricos de flotas específicas.

    ✅ **Importante:** el archivo Excel debe estar filtrado (un único modelo) y usar formato **Mobil Serv**.
    """
)

# ---------------------------------------------
# Carga del archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.info("Espera a subir un archivo para comenzar el análisis.")
    st.stop()

# ---------------------------------------------
# Procesamiento principal
# ---------------------------------------------
try:
    # Lectura y validación
    df = pd.read_excel(archivo)
    faltantes = sorted(set(columnas_esperadas) - set(df.columns))
    if faltantes:
        st.error("❌ Faltan columnas requeridas:")
        st.code("\n".join(faltantes))
        st.stop()

    # Convertir fechas
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

    # Mapear columnas RESULT_
    result_cols = [c for c in df.columns if c.startswith('RESULT_')]
    for col in result_cols:
        df[col + '_status'] = (
            df[col].astype(str).str.strip().map(lambda x: status_map.get(x, 'Normal'))
        )

    # Métricas
    total = len(df)
    lubs = df['Tested Lubricant'].nunique()
    ops = df['Account Name'].nunique()
    fecha_min = df['Date Reported'].min().date()
    fecha_max = df['Date Reported'].max().date()
    equipos = df['Unit ID'].nunique()
    
    # Intervalos de muestreo
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

    # Fila 1: Estados y frecuencia
    r1c1, r1c2 = st.columns(2)
    with r1c1:
        st.subheader("📈 Estados de muestras")
        conteo = df['Report Status'].value_counts()
        orden = ['Normal','Caution','Alert']
        vals = [conteo.get(o,0) for o in orden]
        labels = ['🟢 Normal','🟡 Caution','🔴 Alert']
        colors = sns.color_palette('tab10', 3)
        fig1, ax1 = plt.subplots(figsize=(4,3))
        ax1.bar(labels, vals, color=colors)
        ax1.set_ylabel('Cantidad de muestras')
        ax1.spines[['top','right']].set_visible(False)
        for i,v in enumerate(vals): ax1.annotate(v,(i,v),ha='center',va='bottom')
        st.pyplot(fig1)
    with r1c2:
        st.subheader("📊 Frec. muestreo: Top 15 equipos")
        top15 = df['Unit ID'].value_counts().head(15)
        colors2 = sns.color_palette('viridis', len(top15))
        fig2, ax2 = plt.subplots(figsize=(4,3))
        ax2.barh(top15.index, top15.values, color=colors2)
        ax2.set_xlabel('Número de muestras')
        ax2.spines[['top','right']].set_visible(False)
        for i,v in enumerate(top15.values): ax2.annotate(v,(v+0.5,i),va='center')
        st.pyplot(fig2)

    # Fila 2: Intervalos Top 15 & Pareto Alert
    r2c1, r2c2 = st.columns(2)
    with r2c1:
        st.subheader("⏱️ Intervalo promedio: Top 15 equipos")
        mean_top = mean_int.loc[top15.index].dropna()
        fig3, ax3 = plt.subplots(figsize=(4,3))
        ax3.barh(mean_top.index, mean_top.values, color=sns.color_palette('mako',len(mean_top)))
        ax3.set_xlabel('Días promedio')
        ax3.spines[['top','right']].set_visible(False)
        for i,v in enumerate(mean_top.values): ax3.annotate(f"{v:.1f}",(v+0.5,i),va='center')
        st.markdown(f"**Nota:** Intervalo medio Top 15 = {mean_top.mean():.1f} días")
        st.pyplot(fig3)
    with r2c2:
        st.subheader("📋 Pareto: Alert por parámetro (Top 10)")
        alert_ser = pd.Series({c.replace('RESULT_',''):(df[c+'_status']=='Alert').sum() for c in result_cols})
        alert_ser = alert_ser.sort_values(ascending=False).head(10)
        fig4, ax4 = plt.subplots(figsize=(4,3))
        ax4.bar(alert_ser.index, alert_ser.values, color=sns.color_palette('Reds',10))
        ax4.set_ylabel('N° Alert')
        ax4.spines[['top','right']].set_visible(False)
        for idx,v in enumerate(alert_ser.values): ax4.annotate(v,(idx,v),ha='center',va='bottom')
        cum4 = alert_ser.cumsum()/alert_ser.sum()*100
        ax4_line = ax4.twinx(); ax4_line.plot(cum4.values,alert_ser.index,'-o',color='black');
        ax4_line.set_ylabel('Porcentaje acumulado');
        for y,x in enumerate(cum4): ax4_line.annotate(f"{x:.0f}%",(x,alert_ser.index[y]),xytext=(0,5),textcoords='offset points')
        st.pyplot(fig4)

    # Fila 3: Pareto Caution & combos Alert
    r3c1, r3c2 = st.columns(2)
    with r3c1:
        st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
        caut_ser = pd.Series({c.replace('RESULT_',''):(df[c+'_status']=='Caution').sum() for c in result_cols})
        caut_ser = caut_ser.sort_values(ascending=False).head(10)
        fig5, ax5 = plt.subplots(figsize=(4,3))
        ax5.bar(caut_ser.index,caut_ser.values,color=sns.color_palette('YlOrBr',10))
        ax5.set_ylabel('N° Caution'); ax5.spines[['top','right']].set_visible(False)
        for idx,v in enumerate(caut_ser.values): ax5.annotate(v,(idx,v),ha='center',va='bottom')
        cum5 = caut_ser.cumsum()/caut_ser.sum()*100
        ax5_line = ax5.twinx(); ax5_line.plot(cum5.values,caut_ser.index,'-o',color='black'); ax5_line.set_ylabel('Porc acumulado')
        for i,x in enumerate(cum5): ax5_line.annotate(f"{x:.0f}%",(x,caut_ser.index[i]),xytext=(0,5),textcoords='offset points')
        st.pyplot(fig5)
    with r3c2:
        st.subheader("🔗 Pareto: combos Alert (Top 10)")
        comb_counts={}
        for _,r in df.iterrows():
            al=[c.replace('RESULT_','') for c in result_cols if r[c+'_status']=='Alert']
            if len(al)>1:
                for combo in combinations(al,2): comb_counts[' & '.join(combo)]=comb_counts.get(' & '.join(combo),0)+1
        comb_ser=pd.Series(comb_counts).sort_values(ascending=False).head(10)
        fig6, ax6 = plt.subplots(figsize=(4,3))
        ax6.bar(comb_ser.index,comb_ser.values, color=sns.color_palette('PuRd',10))
        ax6.set_ylabel('N° muestras'); ax6.spines[['top','right']].set_visible(False)
        for idx,v in enumerate(comb_ser.values): ax6.annotate(v,(idx,v),ha='center',va='bottom')
        cum6=comb_ser.cumsum()/comb_ser.sum()*100
        ax6_line=ax6.twinx(); ax6_line.plot(cum6.values,comb_ser.index,'-o',color='black'); ax6_line.set_ylabel('Porc acumulado')
        for i,x in enumerate(cum6): ax6_line.annotate(f"{x:.0f}%",(x,comb_ser.index[i]),xytext=(0,5),textcoords='offset points')
        st.pyplot(fig6)

    # Relación variables por pairplot
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
