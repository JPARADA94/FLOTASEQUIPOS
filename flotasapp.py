# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Solo gráficas de muestras por cuenta y estado de muestras

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string

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
    # Fila 1: muestras por cuenta + tabla
    st.subheader("📊 Muestras por cuenta")
    cnt = df['Account Name'].value_counts()
    df_cnt = cnt.reset_index()
    df_cnt.columns = ['Cuenta','Muestras']
    df_cnt['Letra'] = list(string.ascii_lowercase[:len(df_cnt)])
    colors = sns.color_palette('tab10', len(df_cnt))
    r1c1, r1c2 = st.columns([3,2])
    with r1c1:
        fig, ax = plt.subplots(figsize=(6,3))
        ax.bar(df_cnt['Letra'], df_cnt['Muestras'], color=colors)
        for i, v in enumerate(df_cnt['Muestras']):
            ax.text(i, v + df_cnt['Muestras'].max()*0.01, str(v), ha='center')
        handles = [plt.Rectangle((0,0),1,1,color=colors[i]) for i in range(len(df_cnt))]
        labels = [f"{l}: {c}" for l,c in zip(df_cnt['Letra'], df_cnt['Cuenta'])]
        ax.legend(handles, labels, title='Cuentas', loc='upper right', fontsize='small', title_fontsize='small')
        ax.set_xlabel('Cuenta')
        ax.set_ylabel('Número de muestras')
        fig.tight_layout()
        st.pyplot(fig)
    with r1c2:
        st.table(df_cnt.set_index('Letra'))

    # Fila 2: estado de muestras
    st.subheader("📊 Estados de muestras")
    status_order = ['Normal','Caution','Alert']
    cnt2 = df['Report Status'].value_counts().reindex(status_order, fill_value=0)
    color_map = {'Normal':'#2ecc71','Caution':'#f1c40f','Alert':'#e74c3c'}
    fig2, ax2 = plt.subplots(figsize=(8,3))
    ax2.bar(cnt2.index, cnt2.values, color=[color_map[s] for s in cnt2.index])
    for i, v in enumerate(cnt2.values):
        ax2.text(i, v + cnt2.values.max()*0.01, str(v), ha='center')
    ax2.set_xlabel('Estado')
    ax2.set_ylabel('Cantidad')
    fig2.tight_layout()
    st.pyplot(fig2)

else:
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")
