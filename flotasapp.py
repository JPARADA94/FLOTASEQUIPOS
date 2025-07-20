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
# Encabezados esperados en el Excel y mapa de estados
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
# Categorías de variables
# ---------------------------------------------
vars_desgaste = ['Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index']
vars_contaminacion = ['K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)']
vars_lubricante = ['Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)', 'TAN (mg KOH/g)',
                   'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
                   'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)']

# ---------------------------------------------
# Título e instrucciones
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

if archivo:
    try:
        # Lectura y validación de columnas básicas
        df = pd.read_excel(archivo)
        falt = sorted(set(columnas_esperadas) - set(df.columns))
        if falt:
            st.error("❌ Faltan columnas requeridas:")
            st.code("\n".join(falt))
            st.stop()

        # Convertir 'Date Reported' a datetime
        df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

        # Detectar y mapear columnas RESULT_ a estados
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

        # ---------------------------------------------
        # Gráficos 6 existentes
        # ---------------------------------------------
                # Fila 1: Estados y Frecuencia de muestreo
        r1c1, r1c2 = st.columns(2)
        with r1c1:
            st.subheader("📈 Estados de muestras")
            conteo = df['Report Status'].value_counts()
            orden = ['Normal','Caution','Alert']
            vals = [conteo.get(o,0) for o in orden]
            labels = ['🟢 Normal','🟡 Caution','🔴 Alert']
            palette1 = sns.color_palette("tab10", len(vals))
            fig1, ax1 = plt.subplots(figsize=(4,3))
            ax1.bar(labels, vals, color=palette1)
            ax1.set_ylabel('Cantidad de muestras')
            ax1.spines[['top','right']].set_visible(False)
            for i, v in enumerate(vals):
                ax1.annotate(int(v), (i, v), ha='center', va='bottom')
            st.pyplot(fig1)
        with r1c2:
            st.subheader("📊 Frec. muestreo: Top 15 equipos")
            top15 = df['Unit ID'].value_counts().head(15)
            palette2 = sns.color_palette("viridis", len(top15))
            fig2, ax2 = plt.subplots(figsize=(4,3))
            ax2.barh(top15.index, top15.values, color=palette2)
            ax2.set_xlabel('Número de muestras')
            ax2.spines[['top','right']].set_visible(False)
            for i, v in enumerate(top15.values):
                ax2.annotate(int(v), (v + 0.5, i), va='center')
            st.pyplot(fig2)

        # Fila 2: Intervalos y Pareto Alert
        r2c1, r2c2 = st.columns(2)
                with r2c1:
            st.subheader("⏱️ Intervalo promedio: Top 15 equipos")
            mean_top = mean_int.loc[top15.index].dropna()
            fig3, ax3 = plt.subplots(figsize=(4,3))
            ax3.barh(mean_top.index, mean_top.values, color=sns.color_palette("mako", len(mean_top)))
            ax3.set_xlabel('Días promedio')
            ax3.spines[['top','right']].set_visible(False)
            for i, v in enumerate(mean_top.values):
                ax3.annotate(f"{v:.1f}", (v + 0.5, i), va='center')
            st.pyplot(fig3)
            # Nota de promedio
            st.markdown(f"**Nota:** Intervalo medio Top 15: {mean_top.mean():.1f} días")
        with r2c2:
            st.subheader("📋 Pareto: Alert por parámetro (Top 10)")
            alert_ser = pd.Series({col.replace('RESULT_',''):(df[col+'_status']=='Alert').sum() for col in result_cols}).sort_values(ascending=False).head(10)
            fig4, ax4 = plt.subplots(figsize=(4,3))
            ax4.barh(alert_ser.index, alert_ser.values, color='#e74c3c')
            ax4.set_xlabel('Número de Alert')
            ax4.spines[['top','right']].set_visible(False)
            for i, v in enumerate(alert_ser.values):
                ax4.annotate(int(v), (v+0.5, i), va='center')
            st.pyplot(fig4)

        # Fila 3
        r3c1, r3c2 = st.columns(2)
        with r3c1:
            st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
            caution_ser = pd.Series({col.replace('RESULT_',''):(df[col+'_status']=='Caution').sum() for col in result_cols}).sort_values(ascending=False).head(10)
            fig5, ax5 = plt.subplots(figsize=(4,3))
            ax5.barh(caution_ser.index, caution_ser.values, color='#f1c40f')
            ax5.set_xlabel('Número de Caution')
            ax5.spines[['top','right']].set_visible(False)
            for i, v in enumerate(caution_ser.values):
                ax5.annotate(int(v), (v+0.5, i), va='center')
            st.pyplot(fig5)
        with r3c2:
            st.subheader("🔗 Pareto: combos Alert (Top 10)")
            comb_counts = {}
            for _, row in df.iterrows():
                alerts = [c.replace('RESULT_','') for c in result_cols if row[c+'_status']=='Alert']
                if len(alerts)>1:
                    for combo in combinations(alerts,2):
                        key=' & '.join(combo)
                        comb_counts[key]=comb_counts.get(key,0)+1
            comb_ser = pd.Series(comb_counts).sort_values(ascending=False).head(10)
            fig6, ax6 = plt.subplots(figsize=(4,3))
            ax6.barh(comb_ser.index, comb_ser.values, color='#c0392b')
            ax6.set_xlabel('Número de muestras')
            ax6.spines[['top','right']].set_visible(False)
            for i, v in enumerate(comb_ser.values):
                ax6.annotate(int(v), (v+0.5, i), va='center')
            st.pyplot(fig6)

                        # ---------------------------------------------
        # Relación de variables con opciones de gráfico
        # ---------------------------------------------
        # Variables disponibles
        heatmap_vars = [
            'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
            'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)',
            'Pb (Lead)', 'PQ Index', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)',
            'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
            'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
        ]
        rel1, rel2 = st.columns(2)
        for idx, rel in enumerate([rel1, rel2], start=1):
            with rel:
                st.subheader(f"🔍 Relación variables {idx}")
                x_var = st.selectbox(f"Variable X #{idx}", heatmap_vars, key=f"x_rel{idx}")
                y_var = st.selectbox(f"Variable Y #{idx}", heatmap_vars, key=f"y_rel{idx}")
                tipo = st.radio("Tipo de gráfico", ["Heatmap","Scatter"], key=f"tipo{idx}", horizontal=True)
                if tipo == "Heatmap":
                    corr = df[[x_var, y_var]].corr()
                    fig, ax = plt.subplots(figsize=(4, 3))
                    sns.heatmap(corr, annot=True, fmt=".2f", cmap="coolwarm", ax=ax)
                    ax.set_title(f"Correlación: {x_var} vs {y_var}")
                    st.pyplot(fig)
                else:
                    fig, ax = plt.subplots(figsize=(4, 3))
                    sns.scatterplot(data=df, x=x_var, y=y_var,
                                    hue=df['Report Status'].map({'Normal':'🟢','Caution':'🟡','Alert':'🔴'}),
                                    palette=["#2ecc71","#f1c40f","#e74c3c"], alpha=0.7, ax=ax)
                    sns.regplot(data=df, x=x_var, y=y_var, scatter=False, ax=ax, color="black")
                    ax.set_title(f"Scatter: {x_var} vs {y_var}")
                    ax.legend(title='Estado', loc='upper right')
                    st.pyplot(fig)
    except Exception as e:
        st.error(f"❌ Error al procesar archivo: {e}")


