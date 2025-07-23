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
# Configuración de la página y encabezado
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown(
    """
    Esta aplicación permite analizar datos históricos de flotas.  
    Selecciona filtros y pulsa '🚀 Empezar análisis'.
    """
)

# ---------------------------------------------
# Carga y validación de archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.stop()

raw = pd.read_excel(archivo)
required = ['Account Name', 'Asset Class', 'Tested Lubricant', 'Report Status']
for col in required:
    if col not in raw.columns:
        st.error(f"Falta columna: {col}")
        st.stop()

# ---------------------------------------------
# Filtros
# ---------------------------------------------
sel_accounts = st.multiselect("Selecciona cuenta(s)", raw['Account Name'].unique(), default=raw['Account Name'].unique())
if not sel_accounts:
    st.stop()
df1 = raw[raw['Account Name'].isin(sel_accounts)]

sel_classes = st.multiselect("Selecciona Asset Class", df1['Asset Class'].unique(), default=df1['Asset Class'].unique())
if not sel_classes:
    st.stop()
df2 = df1[df1['Asset Class'].isin(sel_classes)]

sel_lubs = st.multiselect("Selecciona lubricante(s)", df2['Tested Lubricant'].unique(), default=df2['Tested Lubricant'].unique())
if not sel_lubs:
    st.stop()
df = df2[df2['Tested Lubricant'].isin(sel_lubs)].copy()

# ---------------------------------------------
# Análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    # Preparar conteo de muestras por cuenta
    cnt = df['Account Name'].value_counts()
    df_cnt = cnt.reset_index()
    df_cnt.columns = ['Cuenta', 'Muestras']
    df_cnt['Letra'] = list(string.ascii_lowercase[:len(df_cnt)])
    colors = sns.color_palette('tab10', len(df_cnt))

    # Fila 1: gráfica + tabla
    r1c1, r1c2 = st.columns([3, 2])
    with r1c1:
        st.subheader("📊 Muestras por cuenta")
        fig, ax = plt.subplots(figsize=(6, 3))
        ax.bar(df_cnt['Letra'], df_cnt['Muestras'], color=colors)
        for i, v in enumerate(df_cnt['Muestras']):
            ax.text(i, v + df_cnt['Muestras'].max() * 0.01, str(v), ha='center')
        ax.set_xlabel('Cuenta')
        ax.set_ylabel('Número de muestras')
        fig.tight_layout()
        st.pyplot(fig)

    with r1c2:
        st.subheader("📋 Cuentas asignadas")
        tabla_df = df_cnt[['Letra', 'Cuenta', 'Muestras']].copy()
        tabla_df['% Muestras'] = (tabla_df['Muestras'] / tabla_df['Muestras'].sum() * 100).round(1).astype(str) + '%'

        styles = [
            {"selector": "th", "props": [("background-color", "#4f81bd"), ("color", "white"), ("font-size", "14px"), ("text-align", "left")]},
            {"selector": "td", "props": [("padding", "8px"), ("border", "1px solid #ddd"), ("font-size", "13px"), ("text-align", "left")]},
            {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}
        ]
        styled = (
            tabla_df.style
            .set_table_styles(styles)
            .background_gradient(subset=['% Muestras'], cmap='Blues')
        )
        st.write(styled)

    # Fila 2: estado de muestras
    r2c1, _ = st.columns([2, 3])
    with r2c1:
        st.subheader("📊 Estados de muestras")
        order = ['Normal', 'Caution', 'Alert']
        cnt2 = df['Report Status'].value_counts().reindex(order, fill_value=0)
        cmap = {'Normal':'#2ecc71','Caution':'#f1c40f','Alert':'#e74c3c'}
        fig2, ax2 = plt.subplots(figsize=(6, 3))
        ax2.bar(cnt2.index, cnt2.values, color=[cmap[s] for s in cnt2.index])
        for i, v in enumerate(cnt2.values):
            ax2.text(i, v + cnt2.values.max() * 0.01, str(v), ha='center')
        ax2.set_xlabel('Estado')
        ax2.set_ylabel('Cantidad de muestras')
        fig2.tight_layout()
        st.pyplot(fig2)

else:
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")






