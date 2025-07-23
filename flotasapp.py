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
# Definiciones
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
    **Autor:** Javier Parada – Ingeniero de Soporte en Campo  \
    **Fecha de creación:** 2025-07-20

    Esta aplicación analiza datos históricos de flotas en formato Mobil Serv.
    """
)

# ---------------------------------------------
# Carga y validación de archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (Mobil Serv)", type=["xlsx"])
if not archivo:
    st.info("Espera a subir un archivo para comenzar.")
    st.stop()

df_raw = pd.read_excel(archivo)
falt = sorted(set(columnas_esperadas) - set(df_raw.columns))
if falt:
    st.error("❌ Faltan columnas:")
    st.code("\n".join(falt))
    st.stop()

# ---------------------------------------------
# Filtros: Cuentas, Clases, Lubricantes
# ---------------------------------------------
cuentas = df_raw['Account Name'].unique().tolist()
sel_c = st.multiselect("Cuenta(s)", cuentas, default=cuentas)
if not sel_c:
    st.warning("Selecciona al menos una Cuenta.")
    st.stop()
df1 = df_raw[df_raw['Account Name'].isin(sel_c)]

clases = df1['Asset Class'].unique().tolist()
sel_cl = st.multiselect("Asset Class", clases, default=clases)
if not sel_cl:
    st.warning("Selecciona al menos una Clase.")
    st.stop()
df2 = df1[df1['Asset Class'].isin(sel_cl)]

lubs = df2['Tested Lubricant'].unique().tolist()
sel_l = st.multiselect("Lubricante(s)", lubs, default=lubs)
if not sel_l:
    st.warning("Selecciona al menos un Lubricante.")
    st.stop()

df = df2[df2['Tested Lubricant'].isin(sel_l)].copy()

# ---------------------------------------------
# Botón de Análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    # Preparación de datos
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')
    for col in vars_correl:
        if col in df:
            df[col] = pd.to_numeric(df[col].astype(str).str.replace(r"[^0-9\.\-]", "", regex=True), errors='coerce')
    rc = [c for c in df if c.startswith('RESULT_')]
    for c in rc:
        df[c+'_status'] = df[c].astype(str).map(lambda x: status_map.get(x.strip(), 'Normal'))

    # Métricas generales
    total = len(df)
    nut = df['Tested Lubricant'].nunique()
    nop = df['Account Name'].nunique()
    neq = df['Unit ID'].nunique()
    dmin = df['Date Reported'].min().date()
    dmax = df['Date Reported'].max().date()
    dff = df.sort_values(['Unit ID','Date Reported'])
    avg_int = dff.groupby('Unit ID')['Date Reported'].diff().dt.days.mean()

    # Resumen general
    st.subheader("🔎 Resumen")
    c1,c2,c3,c4 = st.columns(4)
    c1.metric("Muestras", total)
    c2.metric("Lubricantes", nut)
    c3.metric("Operaciones", nop)
    c4.metric("Equipos", neq)

    # Fila 1: Muestras por Cuenta + Tabla
    st.subheader("📊 Muestras por Cuenta")
    r1c1,r1c2 = st.columns([3,2])
    cnt = df['Account Name'].value_counts()
    dfc = cnt.reset_index(); dfc.columns=['Cuenta','Muestras']
    dfc['Letra'] = list(string.ascii_uppercase[:len(dfc)])
    pal = sns.color_palette('tab10', len(dfc))
    with r1c1:
        fig,ax=plt.subplots(figsize=(6,3))
        ax.bar(dfc['Letra'], dfc['Muestras'], color=pal)
        for i,v in enumerate(dfc['Muestras']): ax.text(i,v+total*0.01,str(v),ha='center')
        ax.set_ylabel('Nº Muestras'); ax.set_xlabel('Cuenta')
        ax.legend([plt.Rectangle((0,0),1,1,color=pal[i]) for i in dfc.index],
                  dfc['Letra']+": "+dfc['Cuenta'], loc='upper right', fontsize='small')
        st.pyplot(fig)
    with r1c2:
        st.table(dfc.set_index('Letra'))

    # Fila 2: Estados de Muestras
    st.subheader("🎯 Estados de Muestras")
    sc = df['Report Status'].value_counts().reindex(['Normal','Caution','Alert'],fill_value=0)
    cols_s = {'Normal':'#2ecc71','Caution':'#f1c40f','Alert':'#e74c3c'}
    fig2,ax2=plt.subplots(figsize=(6,2))
    ax2.bar(sc.index, sc.values, color=[cols_s[k] for k in sc.index])
    for i,v in enumerate(sc.values): ax2.text(i,v+total*0.01,str(v),ha='center')
    ax2.set_ylabel('Nº Muestras')
    st.pyplot(fig2)

    # Fila 3: Intervalos promedio y Pareto Alert
    r2c1,r2c2 = st.columns(2)
    with r2c1:
        st.subheader("⏱️ Intervalo promedio (Top15)")
        top15=df['Unit ID'].value_counts().head(15)
        mean_int = dff.groupby('Unit ID')['Date Reported'].diff().dt.days
        mt = mean_int.groupby(dff['Unit ID']).mean().loc[top15.index]
        fig3,ax3=plt.subplots(figsize=(4,3))
        ax3.barh(mt.index, mt.values)
        for i,v in enumerate(mt): ax3.text(v+0.1,i,f"{v:.1f}",va='center')
        st.pyplot(fig3)
    with r2c2:
        st.subheader("📋 Pareto Alert (Top10)")
        alert = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Alert').sum() for c in rc}).sort_values(ascending=False).head(10)
        fig4,ax4=plt.subplots(figsize=(4,3)); alert.plot.barh(ax=ax4)
        ax4.invert_yaxis(); st.pyplot(fig4)

    # Fila 4: Pareto Caution y Combos Alert
    r3c1,r3c2=st.columns(2)
    with r3c1:
        st.subheader("📋 Pareto Caution (Top10)")
        caut=pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Caution').sum() for c in rc}).sort_values(ascending=False).head(10)
        fig5,ax5=plt.subplots(figsize=(4,3)); caut.plot.barh(ax=ax5)
        ax5.invert_yaxis(); st.pyplot(fig5)
    with r3c2:
        st.subheader("🔗 Combos Alert (Top10)")
        combos={}
        for _,r in df.iterrows():
            a=[c.replace('RESULT_','') for c in rc if r[c+'_status']=='Alert']
            for x,y in combinations(a,2): combos[f"{x}&{y}"]=combos.get(f"{x}&{y}",0)+1
        comb=pd.Series(combos).sort_values(ascending=False).head(10)
        fig6,ax6=plt.subplots(figsize=(4,3)); comb.plot.barh(ax=ax6); ax6.invert_yaxis(); st.pyplot(fig6)

    # Correlación
    st.subheader("📈 Heatmap Correlación")
    num=df.select_dtypes('number')[vars_correl]
    corr=num.corr()
    fig7,ax7=plt.subplots(figsize=(5,4)); sns.heatmap(corr,annot=True,fmt='.2f',ax=ax7); st.pyplot(fig7)

    # Distribuciones (Variable1 y 2)
    st.subheader("📊 Distribuciones por Intervalos")
    vars_int=[v for v in vars_correl if v in df]
    if len(vars_int)>=2:
        v1=st.selectbox("Var1",vars_int,vars_int[:1])
        v2=st.selectbox("Var2",vars_int,vars_int[1:2],key=2)
        n1=st.slider("Intervals V1",3,10,5,key=1)
        n2=st.slider("Intervals V2",3,10,5,key=2)
        for var,n,r in [(v1,n1,'V1'),(v2,n2,'V2')]:
            data=df[var].dropna()
            bins=pd.interval_range(data.min(),data.max(),periods=n)
            counts=[data.between(b.left,b.right,left=True).sum() for b in bins]
            fig,ax=plt.subplots(figsize=(4,2))
            ax.bar(range(len(counts)),counts); ax.set_xticks(range(len(counts))); ax.set_xticklabels([f"{b.left:.1f}-{b.right:.1f}" for b in bins],rotation=45)
            st.pyplot(fig)

else:
    st.info("Configura filtros y haz clic en '🚀 Empezar análisis'.")


