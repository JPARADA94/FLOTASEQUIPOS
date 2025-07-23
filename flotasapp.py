# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Solo gráficas de muestras por cuenta y estado de muestras

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string

# ---------------------------------------------
# Título e instrucciones
# ---------------------------------------------
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown(
    """
    Esta aplicación permite analizar datos históricos de flotas.
    Selecciona filtros y pulsa '🚀 Empezar análisis'.
    """
)

st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# ---------------------------------------------
# Carga y validación de archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.stop()
raw = pd.read_excel(archivo)
for col in ['Account Name','Asset Class','Tested Lubricant','Report Status']:
    if col not in raw.columns:
        st.error(f"Falta columna: {col}")
        st.stop()

# ---------------------------------------------
# Filtros
# ---------------------------------------------
c_accounts = raw['Account Name'].unique().tolist()
sel_accounts = st.multiselect("Selecciona cuenta(s)", c_accounts, default=c_accounts)
if not sel_accounts: st.stop()
df1 = raw[raw['Account Name'].isin(sel_accounts)]

c_classes = df1['Asset Class'].unique().tolist()
sel_classes = st.multiselect("Selecciona Asset Class", c_classes, default=c_classes)
if not sel_classes: st.stop()
df2 = df1[df1['Asset Class'].isin(sel_classes)]

c_lubs = df2['Tested Lubricant'].unique().tolist()
sel_lubs = st.multiselect("Selecciona lubricante(s)", c_lubs, default=c_lubs)
if not sel_lubs: st.stop()
df = df2[df2['Tested Lubricant'].isin(sel_lubs)].copy()

# ---------------------------------------------
# Análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    # Preparar datos de cuentas
    cnt = df['Account Name'].value_counts()
    df_cnt = cnt.reset_index()
    df_cnt.columns = ['Cuenta','Muestras']
    df_cnt['Letra'] = list(string.ascii_lowercase[:len(df_cnt)])
    colors = sns.color_palette('tab10', len(df_cnt))

    # Fila 1: gráfica de muestras por cuenta y tabla
    r1c1, r1c2 = st.columns([3, 2])
    with r1c1:
        st.subheader("📊 Muestras por cuenta")
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.bar(df_cnt['Letra'], df_cnt['Muestras'], color=colors)
        for i, v in enumerate(df_cnt['Muestras']):
            ax.text(i, v + df_cnt['Muestras'].max()*0.01, str(v), ha='center')
        # Eliminar leyenda interna, tabla a la derecha cubre el mapeo
        fig.tight_layout()
        st.pyplot(fig)
    with r1c2:
        st.subheader("📋 Cuentas asignadas")
        # Usar df_cnt para incluir Muestras y calcular porcentaje
        tabla_df = df_cnt[['Letra', 'Cuenta', 'Muestras']].copy()
        tabla_df['% Muestras'] = (tabla_df['Muestras'] / tabla_df['Muestras'].sum() * 100).round(1)
        # Estilos de tabla
        styles = [
            {"selector": "th", "props": [("background-color", "#4f81bd"), ("color", "white"), ("font-size", "14px"), ("text-align", "left")]},
            {"selector": "td", "props": [("padding", "8px"), ("border", "1px solid #ddd"), ("font-size", "13px"), ("text-align", "left")]},
            {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}
        ]
        # Aplicar estilos y degradado
        styled = (
            tabla_df.style
            .set_table_styles(styles)
            .background_gradient(subset=['% Muestras'], cmap='Blues')
            .format({'% Muestras': '{:.1f}%'} )
        )
        st.write(styled)

        # Fila 2: Pareto de fallas (Alert + Caution)
    r2c1, r2c2 = st.columns([3, 2])
    with r2c1:
        st.subheader("📋 Pareto de fallas (Alert + Precaución)")
        # Parámetros de resultado
        status_cols = [c for c in df.columns if c.endswith('_status')]
        counts = {}
        for sc in status_cols:
            param = sc.replace('_status','')
            counts[param] = ((df[sc] == 'Alert') | (df[sc] == 'Caution')).sum()
        pareto = pd.Series(counts).sort_values(ascending=False).head(10)
        fig3, ax3 = plt.subplots(figsize=(8, 4))
        ax3.barh(pareto.index, pareto.values)
        ax3.invert_yaxis()
        ax3.set_xlabel('Número de fallas')
        for i, v in enumerate(pareto.values):
            ax3.text(v + pareto.values.max()*0.01, i, str(v), va='center')
        # Línea de % acumulado
        cum = pareto.cumsum() / pareto.sum() * 100
        ax3_line = ax3.twiny()
        ax3_line.plot(cum.values, range(len(cum)), '-o')
        ax3_line.set_xlabel('% acumulado')
        for i, p in enumerate(cum):
            ax3_line.text(p + 2, i, f"{p:.0f}%", va='center')
        fig3.tight_layout()
        st.pyplot(fig3)
    # Columna derecha vacía o para futuros contenidos

else:
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")

