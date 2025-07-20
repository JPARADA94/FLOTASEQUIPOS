# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from itertools import combinations

# Configuración de página
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# Encabezados esperados y mapeo de estados
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

# Variables para correlación
vars_correl = [
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)',
    'Pb (Lead)', 'PQ Index', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)',
    'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
    'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]

# Título
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown(
    """
    Esta app analiza datos de flotas por proyecto.   
    ✅ Sube un Excel filtrado y en formato Mobil Serv.
    """
)

# Carga de archivo
archivo = st.file_uploader("Sube tu Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.stop()

# Procesamiento
try:
    df = pd.read_excel(archivo)
    falt = sorted(set(columnas_esperadas) - set(df.columns))
    if falt:
        st.error("Faltan columnas:")
        st.code("\n".join(falt))
        st.stop()

    # Fechas
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

    # ---------------------------------------------
    # Limpiar y convertir a numérico columnas de variables de correlación
    for col in vars_correl:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                     .str.replace(r"[^0-9\.\-]", "", regex=True),
                errors='coerce'
            )

    # Mapear RESULT_ a estados
    result_cols = [c for c in df.columns if c.startswith('RESULT_')]
    for c in result_cols:
        df[c+'_status'] = df[c].astype(str).str.strip().map(lambda x: status_map.get(x,'Normal'))

    # Métricas
    total = len(df)
    lubs = df['Tested Lubricant'].nunique()
    ops = df['Account Name'].nunique()
    fecha_min = df['Date Reported'].min().date()
    fecha_max = df['Date Reported'].max().date()
    equipos = df['Unit ID'].nunique()

    # Intervalos
    df_s = df.sort_values(['Unit ID','Date Reported'])
    mean_int = df_s.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
    overall_mean = mean_int.mean()

    # Resumen
    st.subheader("🔎 Resumen")
    st.markdown(f"""
- Total muestras: **{total}**  
- Lubricantes: **{lubs}**  
- Operaciones: **{ops}**  
- Fechas: {fecha_min} a {fecha_max}  
- Equipos: **{equipos}**  
- Intervalo medio: **{overall_mean:.1f}** días
""")

    # 6 Gráficos
    # Fila1: Estados + Frecuencia
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Estados de muestras")
        vc = df['Report Status'].value_counts()
        ords = ['Normal','Caution','Alert']
        vals = [vc.get(o,0) for o in ords]
        cols = ['#2ecc71','#f1c40f','#e74c3c']
        fig, ax = plt.subplots(figsize=(4,3))
        ax.bar(ords, vals, color=cols)
        ax.set_ylabel('Cant. muestras')
        for i,v in enumerate(vals): ax.text(i,v+2,str(v),ha='center')
        st.pyplot(fig)
    with c2:
        st.subheader("Frecuencia muestreo (Top15)")
        top15 = df['Unit ID'].value_counts().head(15)
        cols2 = sns.color_palette('viridis',len(top15))
        fig, ax = plt.subplots(figsize=(4,3))
        ax.barh(top15.index, top15.values, color=cols2)
        ax.set_xlabel('N° muestras')
        for i,v in enumerate(top15.values): ax.text(v+1,i,str(v),va='center')
        st.pyplot(fig)

    # Fila2: Intervalos + Pareto Alert
    c3,c4 = st.columns(2)
    with c3:
        st.subheader("Intervalo promedio (Top15)")
        mt = mean_int.loc[top15.index].dropna()
        fig, ax = plt.subplots(figsize=(4,3))
        ax.barh(mt.index, mt.values, color=sns.color_palette('mako',len(mt)))
        ax.set_xlabel('Días promedio')
        for i,v in enumerate(mt.values): ax.text(v+0.5,i,f"{v:.1f}",va='center')
        st.markdown(f"**Nota:** Promedio Top15 = {mt.mean():.1f} días")
        st.pyplot(fig)
    with c4:
        st.subheader("Pareto Alert (Top10)")
        ser = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Alert').sum() for c in result_cols})
        ser = ser.sort_values(ascending=False).head(10)
        cols4 = sns.color_palette('Reds',len(ser))
        fig, ax = plt.subplots(figsize=(4,3))
        ser.plot.barh(color=cols4, ax=ax)
        ax.invert_yaxis(); ax.grid(axis='x',linestyle='--',alpha=0.5)
        ax.set_xlabel('N Alertas'); ax.set_title('Pareto Alert')
        for i,v in enumerate(ser.values): ax.text(v+1,i,str(v),va='center')
        cum = ser.cumsum()/ser.sum()*100
        ax2 = ax.twiny(); ax2.plot(cum.values,range(len(cum)),'-ok'); ax2.set_xlabel('% acum')
        for i,p in enumerate(cum): ax2.text(p+2,i,f"{p:.0f}%",va='center')
        st.pyplot(fig)

    # Fila3: Pareto Caution + combos Alert
    c5,c6 = st.columns(2)
    with c5:
        st.subheader("Pareto Caution (Top10)")
        ser2 = pd.Series({c.replace('RESULT_',''): (df[c+'_status']=='Caution').sum() for c in result_cols})
        ser2 = ser2.sort_values(ascending=False).head(10)
        cols5 = sns.color_palette('YlOrBr',len(ser2))
        fig,ax=plt.subplots(figsize=(4,3))
        ser2.plot.barh(color=cols5,ax=ax)
        ax.invert_yaxis();ax.grid(axis='x',linestyle='--',alpha=0.5)
        ax.set_xlabel('N Cautions'); ax.set_title('Pareto Caution')
        for i,v in enumerate(ser2.values): ax.text(v+1,i,str(v),va='center')
        cum2=ser2.cumsum()/ser2.sum()*100
        axb=ax.twiny();axb.plot(cum2.values,range(len(cum2)),'-ok'); axb.set_xlabel('% acum')
        for i,p in enumerate(cum2): axb.text(p+2,i,f"{p:.0f}%",va='center')
        st.pyplot(fig)
    with c6:
        st.subheader("Pareto combos Alert (Top10)")
        combos={}
        for _,r in df.iterrows():
            keys=[c.replace('RESULT_','') for c in result_cols if r[c+'_status']=='Alert']
            for a,b in combinations(keys,2): combos[f"{a}&{b}"]=combos.get(f"{a}&{b}",0)+1
        ser3=pd.Series(combos).sort_values(ascending=False).head(10)
        cols6=sns.color_palette('PuRd',len(ser3))
        fig,ax=plt.subplots(figsize=(4,3))
        ser3.plot.barh(color=cols6,ax=ax)
        ax.invert_yaxis();ax.grid(axis='x',linestyle='--',alpha=0.5)
        ax.set_xlabel('N muestras'); ax.set_title('Pareto combos')
        for i,v in enumerate(ser3.values): ax.text(v+1,i,str(v),va='center')
        cum3=ser3.cumsum()/ser3.sum()*100
        axb=ax.twiny();axb.plot(cum3.values,range(len(cum3)),'-ok'); axb.set_xlabel('% acum')
        for i,p in enumerate(cum3): axb.text(p+2,i,f"{p:.0f}%",va='center')
        st.pyplot(fig)

        # Filtrar variables numéricas válidas para correlación
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    valid_vars = [v for v in vars_correl if v in numeric_cols]
    if not valid_vars:
        st.warning("No hay variables numéricas válidas para correlación.")
    else:
        st.markdown(
            """
            A continuación se muestra un **heatmap de correlación** para las variables seleccionadas.
            - Los valores cercanos a **1** indican una correlación positiva alta.
            - Valores cercanos a **-1** indican una correlación negativa alta.
            - Un valor de **0** significa que no hay correlación lineal aparente.

            Selecciona cuántas variables quieres analizar y luego elige cada una.
            """
        )
        n = st.number_input(
            "¿Cuántas variables quieres correlacionar?",
            min_value=2, max_value=len(valid_vars), value=2, step=1
        )
        sel = st.multiselect(
            "Selecciona las variables:", valid_vars,
            default=valid_vars[:n]
        )
        if len(sel) == n:
            corr = df[sel].corr()
            # Ajuste dinámico de tamaño de figura y fuente para mejor legibilidad
            size = max(4, n * 0.6)
            annot_font = max(6, int(12 - n / 2))
            fig, ax = plt.subplots(figsize=(size, size))
            sns.heatmap(
                corr,
                annot=True,
                fmt='.2f',
                cmap='coolwarm',
                annot_kws={'fontsize': annot_font},
                linewidths=0.5,
                square=True,
                ax=ax
            )
            ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=annot_font)
            ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=annot_font)
            ax.set_title('Heatmap de correlación', fontsize=annot_font+2)
            st.pyplot(fig)
        else:
            st.warning(f"Selecciona exactamente {n} variables.")

except Exception as e:
    st.error(f"Error al procesar archivo: {e}")
    st.error(f"Error al procesar archivo: {e}")


