# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Análisis de muestras, Pareto de Alertas y combinaciones

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string
from itertools import combinations

# ---------------------------------------------
# Configuración de la página y encabezados
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos de flotas.
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
for col in ['Account Name','Asset Class','Tested Lubricant','Report Status']:
    if col not in raw.columns:
        st.error(f"Falta columna: {col}")
        st.stop()

# ---------------------------------------------
# Filtros
# ---------------------------------------------
sel_accounts = st.multiselect("Selecciona cuenta(s)", raw['Account Name'].unique(), default=raw['Account Name'].unique())
if not sel_accounts: st.stop()
df1 = raw[raw['Account Name'].isin(sel_accounts)]
sel_classes = st.multiselect("Selecciona Asset Class", df1['Asset Class'].unique(), default=df1['Asset Class'].unique())
if not sel_classes: st.stop()
df2 = df1[df1['Asset Class'].isin(sel_classes)]
sel_lubs = st.multiselect("Selecciona lubricante(s)", df2['Tested Lubricant'].unique(), default=df2['Tested Lubricant'].unique())
if not sel_lubs: st.stop()
df = df2[df2['Tested Lubricant'].isin(sel_lubs)].copy()

# ---------------------------------------------
# Mapear estados
# ---------------------------------------------
status_map = {'*':'Alert', '+':'Caution', '':'Normal'}
for c in [c for c in df.columns if c.startswith('RESULT_')]:
    df[c+'_status'] = df[c].astype(str).str.strip().map(lambda x: status_map.get(x, 'Normal'))

# ---------------------------------------------
# Análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    # Muestras por cuenta
    cnt = df['Account Name'].value_counts()
    df_cnt = cnt.reset_index(); df_cnt.columns = ['Cuenta','Muestras']
    df_cnt['Letra'] = list(string.ascii_lowercase[:len(df_cnt)])
    colors = sns.color_palette('tab10', len(df_cnt))

    # Fila 1: gráfica + tabla
    c1, c2 = st.columns([3,2])
    with c1:
        st.subheader("📊 Muestras por cuenta")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.bar(df_cnt['Letra'], df_cnt['Muestras'], color=colors)
        for i,v in enumerate(df_cnt['Muestras']): ax.text(i, v*1.01, str(v), ha='center')
        ax.set_xlabel('Cuenta'); ax.set_ylabel('Número de muestras')
        fig.tight_layout(); st.pyplot(fig, use_container_width=True)
    with c2:
        st.subheader("📋 Cuentas asignadas")
        tabla_df = df_cnt[['Letra','Cuenta','Muestras']].copy()
        tabla_df['% Muestras'] = (tabla_df['Muestras']/tabla_df['Muestras'].sum()*100).round(1)
        styles = [
            {"selector":"th","props":[("background-color","#4f81bd"),("color","white"),("font-size","14px")]},
            {"selector":"td","props":[("padding","8px"),("border","1px solid #ddd"),("font-size","13px")]},
            {"selector":"tr:nth-child(even)","props":[("background-color","#f9f9f9")]}
        ]
        styled = (tabla_df.style
                  .set_table_styles(styles)
                  .background_gradient(subset=['% Muestras'], cmap='Blues')
                  .format({'% Muestras':'{:.1f}%'}))
        st.write(styled)

    # Fila 2: Pareto de alertas + Estado de muestras
    c3, c4 = st.columns([3,2])
    with c3:
        st.subheader("📋 Pareto de Alertas (Top 10)")
        counts = {c.replace('RESULT_',''): (df[c+'_status']=='Alert').sum() for c in df.columns if c.startswith('RESULT_')}
        ser = pd.Series(counts); ser = ser[ser>0].sort_values(ascending=False)
        top = ser.head(10) if len(ser)>10 else ser
        fig2, ax2 = plt.subplots(figsize=(8,4))
        ax2.barh(top.index, top.values, color='crimson')
        ax2.invert_yaxis(); ax2.set_xlabel('Número de Alertas')
        for i,v in enumerate(top.values): ax2.text(v*1.01, i, str(v), va='center')
        cum = top.cumsum()/top.sum()*100
        ax2_line = ax2.twiny()
        ax2_line.plot(cum.values, range(len(cum)), '-o', color='black')
        ax2_line.set_xlabel('% acumulado')
        for i,p in enumerate(cum): ax2_line.text(p+1, i, f"{p:.0f}%", va='center')
        fig2.tight_layout(); st.pyplot(fig2, use_container_width=True)
    with c4:
        st.subheader("📊 Estados de muestras")
        cnt2 = df['Report Status'].value_counts().reindex(['Normal','Caution','Alert'],fill_value=0)
        cmap = {'Normal':'#2ecc71','Caution':'#f1c40f','Alert':'#e74c3c'}
        fig3, ax3 = plt.subplots(figsize=(8,4))
        ax3.bar(cnt2.index, cnt2.values, color=[cmap[s] for s in cnt2.index])
        for i,v in enumerate(cnt2.values): ax3.text(i, v*1.01, str(v), ha='center')
        ax3.set_xlabel('Estado'); ax3.set_ylabel('Cantidad de muestras')
        fig3.tight_layout(); st.pyplot(fig3, use_container_width=True)

    # Fila 3: Pareto de combinaciones (Alert+Caution)
    st.subheader("🔗 Pareto: combinaciones de Alertas y Precaución")
    combo_size = st.selectbox("Tamaño de combinación:", [2,3,4], index=0)
    combos = {}
    status_cols = [c for c in df.columns if c.endswith('_status')]
    for _,row in df.iterrows():
        alerts = [c.replace('_status','') for c in status_cols if row[c] in ['Alert','Caution']]
        if len(alerts)>=combo_size:
            for combo in combinations(alerts, combo_size):
                key=' & '.join(combo)
                combos[key]=combos.get(key,0)+1
    comb_ser = pd.Series(combos); comb_ser=comb_ser[comb_ser>0].sort_values(ascending=False)
    topc = comb_ser.head(10) if len(comb_ser)>10 else comb_ser
    if topc.empty:
        st.warning(f"Sin combinaciones de tamaño {combo_size}.")
    else:
        fig4, ax4 = plt.subplots(figsize=(8,4))
        ax4.barh(topc.index, topc.values, color='purple')
        ax4.invert_yaxis(); ax4.set_xlabel('Número de muestras')
        for i,v in enumerate(topc.values): ax4.text(v*1.01,i,str(v),va='center')
        fig4.tight_layout(); st.pyplot(fig4, use_container_width=True)

else:
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")
