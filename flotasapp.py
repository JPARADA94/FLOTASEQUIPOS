# flotasapp.py
# Autor: Javier Parada
# Fecha de creación: 2025-07-20
# Descripción: Análisis de flotas con filtros, gráficos y estadísticas avanzadas (enteros)

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string
from itertools import combinations

# ---------------------------------------------
# Configuración de la aplicación
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos de flotas en formato Mobil Serv.
    Filtra cuentas, clases de equipo y lubricantes, y genera gráficos y estadísticas.
    Todos los valores numéricos se muestran como enteros.
    """
)

# ---------------------------------------------
# Estado de análisis
# ---------------------------------------------
if 'analizado' not in st.session_state:
    st.session_state.analizado = False

# ---------------------------------------------
# Carga y validación del archivo Excel
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.stop()
raw = pd.read_excel(archivo)
cols_req = ['Account Name','Asset Class','Tested Lubricant','Report Status','Date Reported']
for col in cols_req:
    if col not in raw.columns:
        st.error(f"Falta columna: {col}")
        st.stop()
raw['Date Reported'] = pd.to_datetime(raw['Date Reported'], errors='coerce')

# ---------------------------------------------
# Filtros interactivos
# ---------------------------------------------
sel_cuentas = st.multiselect(
    "Selecciona cuenta(s)",
    raw['Account Name'].unique(),
    default=raw['Account Name'].unique()
)
if not sel_cuentas:
    st.stop()
df1 = raw[raw['Account Name'].isin(sel_cuentas)]

sel_clases = st.multiselect(
    "Selecciona Asset Class",
    df1['Asset Class'].unique(),
    default=df1['Asset Class'].unique()
)
if not sel_clases:
    st.stop()
df2 = df1[df1['Asset Class'].isin(sel_clases)]

sel_lubs = st.multiselect(
    "Selecciona lubricante(s)",
    df2['Tested Lubricant'].unique(),
    default=df2['Tested Lubricant'].unique()
)
if not sel_lubs:
    st.stop()
df = df2[df2['Tested Lubricant'].isin(sel_lubs)].copy()

# ---------------------------------------------
# Mapeo de estados de RESULT_
# ---------------------------------------------
status_map = {'*':'Alert','+':'Caution','':'Normal'}
for c in [c for c in df.columns if c.startswith('RESULT_')]:
    df[c + '_status'] = df[c].astype(str).str.strip().map(lambda x: status_map.get(x, 'Normal'))

# ---------------------------------------------
# Botón para iniciar análisis
# ---------------------------------------------
if st.button("🚀 Empezar análisis"):
    st.session_state.analizado = True
if not st.session_state.analizado:
    st.info("Configura los filtros y pulsa '🚀 Empezar análisis'.")

# ---------------------------------------------
# Bloque de análisis
# ---------------------------------------------
if st.session_state.analizado:
    # Fila 1: muestras por cuenta + tabla de letras
    cnt = df['Account Name'].value_counts()
    df_cnt = cnt.reset_index()
    df_cnt.columns = ['Cuenta','Muestras']
    df_cnt['Letra'] = list(string.ascii_lowercase[:len(df_cnt)])
    pal = sns.color_palette('tab10', len(df_cnt))

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📊 Muestras por cuenta")
        fig, ax = plt.subplots(figsize=(8,4))
        ax.bar(df_cnt['Letra'], df_cnt['Muestras'], color=pal)
        for i,v in enumerate(df_cnt['Muestras']): ax.text(i, v+0.5, str(int(v)), ha='center')
        ax.set_xlabel('Cuenta'); ax.set_ylabel('Nº muestras')
        fig.tight_layout(); st.pyplot(fig, use_container_width=True)
    with c2:
        st.subheader("📋 Cuentas asignadas")
        tabla = df_cnt[['Letra','Cuenta','Muestras']].copy()
        tabla['% Muestras'] = ((tabla['Muestras']/tabla['Muestras'].sum())*100).round(0).astype(int)
        styles = [
            {"selector":"th","props":[("background-color","#4f81bd"),("color","white"),("text-align","left")]},
            {"selector":"td","props":[("padding","8px"),("border","1px solid #ddd"),("text-align","left")]},
            {"selector":"tr:nth-child(even)","props":[("background-color","#f9f9f9")]}
        ]
        st.write(
            tabla.style
                 .set_table_styles(styles)
                 .background_gradient(subset=['% Muestras'], cmap='Blues')
                 .format({'% Muestras':'{:.0f}%'})
        )

    # Fila 2: estado de muestras + muestras por año
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("📊 Estados de muestras")
        s_cnt = df['Report Status'].value_counts().reindex(['Normal','Caution','Alert'], fill_value=0)
        cmap2 = {'Normal':'#2ecc71','Caution':'#f1c40f','Alert':'#e74c3c'}
        fig2, ax2 = plt.subplots(figsize=(8,4))
        ax2.bar(s_cnt.index, s_cnt.values, color=[cmap2[s] for s in s_cnt.index])
        for i,v in enumerate(s_cnt.values): ax2.text(i, v+0.5, str(int(v)), ha='center')
        ax2.set_xlabel('Estado'); ax2.set_ylabel('Nº muestras')
        fig2.tight_layout(); st.pyplot(fig2, use_container_width=True)
    with c4:
        st.subheader("📈 Muestras por año")
        yearly = df['Date Reported'].dt.year.value_counts().sort_index()
        figyr, axy = plt.subplots(figsize=(8,4))
        axy.bar(yearly.index.astype(str), yearly.values, color='steelblue')
        for i,v in enumerate(yearly.values): axy.text(i, v+0.5, str(int(v)), ha='center')
        axy.set_xlabel('Año'); axy.set_ylabel('Nº muestras')
        figyr.tight_layout(); st.pyplot(figyr, use_container_width=True)

    # Fila 3: pareto de alertas + combinaciones
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("📋 Pareto de Alertas (Top 10)")
        cols_res = [c for c in df.columns if c.startswith('RESULT_') and not c.endswith('_status')]
        cnts = {c.replace('RESULT_',''): df[c + '_status'].eq('Alert').sum() for c in cols_res}
        ser = pd.Series(cnts).loc[lambda x: x>0].sort_values(ascending=False)
        top10 = ser.head(10) if len(ser)>10 else ser
        fig3, ax3 = plt.subplots(figsize=(8,4))
        ax3.barh(top10.index, top10.values, color='crimson'); ax3.invert_yaxis(); ax3.set_xlabel('Nº Alertas')
        for i,v in enumerate(top10.values): ax3.text(v+0.5, i, str(int(v)), va='center')
        cum = top10.cumsum()/top10.sum()*100
        ln = ax3.twiny(); ln.plot(cum.values, range(len(cum)), '-o', color='black'); ln.set_xlabel('% acumulado')
        for i,p in enumerate(cum): ln.text(p+1, i, f"{int(p)}%", va='center')
        fig3.tight_layout(); st.pyplot(fig3, use_container_width=True)
    with c6:
        st.subheader("🔗 Pareto de combinaciones de fallas")
        st_cols = [c for c in df.columns if c.endswith('_status')]
        combos = {}
        for _,r in df.iterrows():
            alerts = [c.replace('RESULT_','').replace('_status','') for c in st_cols if r[c] in ['Alert','Caution']]
            for n in range(2, len(alerts)+1):
                for combo in combinations(alerts, n):
                    key = ' & '.join(combo)
                    combos[key] = combos.get(key, 0) + 1
        comb_ser = pd.Series(combos).loc[lambda x: x>0].sort_values(ascending=False)
        topc = comb_ser.head(10) if len(comb_ser)>10 else comb_ser
        if topc.empty:
            st.warning("No hay combinaciones de Alertas/Precauciones.")
        else:
            fig4, ax4 = plt.subplots(figsize=(8,4))
            ax4.barh(topc.index, topc.values, color='#8e44ad'); ax4.invert_yaxis(); ax4.set_xlabel('Nº muestras')
            for i,v in enumerate(topc.values): ax4.text(v+0.5, i, str(int(v)), va='center')
            cum2 = topc.cumsum()/topc.sum()*100
            ln2 = ax4.twiny(); ln2.plot(cum2.values, range(len(cum2)), '-o', color='black'); ln2.set_xlabel('% acumulado')
            for i,p in enumerate(cum2): ln2.text(p+1, i, f"{int(p)}%", va='center')
            fig4.tight_layout(); st.pyplot(fig4, use_container_width=True)

    # ---------------------------------------------
    # Estadísticas por variable
    # ---------------------------------------------
    st.subheader("🔍 Análisis por variable")
    pareto_vars = top10.index.tolist()
    sel_var = st.selectbox("Selecciona variable de Pareto:", pareto_vars)
    status_col = f"RESULT_{sel_var}_status"

    # Diccionario de descripciones
    desc_map = {
        'count':'Número de muestras','mean':'Media aritmética','std':'Desviación estándar',
        'min':'Valor mínimo','25%':'Primer cuartil','50%':'Mediana','75%':'Tercer cuartil','max':'Valor máximo'
    }

    s1, s2 = st.columns(2)
    with s1:
        st.markdown("**Global**")
        s_glob = pd.to_numeric(df[sel_var], errors='coerce')
        stats_glob = (
            s_glob
            .describe()
            .round(0)
            .fillna(0)
            .astype(int)
            .to_frame()
            .rename(columns={sel_var:'Valor'})
        )
        stats_glob['Descripción'] = stats_glob.index.map(lambda i: desc_map.get(i, i))
        st.table(stats_glob[['Descripción','Valor']])
    with s2:
        st.markdown("**Alert/Caution**")
        df_sub = df[df[status_col].isin(['Alert','Caution'])]
        s_sub = pd.to_numeric(df_sub[sel_var], errors='coerce')
        stats_sub = (
            s_sub
            .describe()
            .round(0)
            .fillna(0)
            .astype(int)
            .to_frame()
            .rename(columns={sel_var:'Valor'})
        )
        stats_sub['Descripción'] = stats_sub.index.map(lambda i: desc_map.get(i, i))
        st.table(stats_sub[['Descripción','Valor']])

        # Tabla adicional para Visc@40C (cSt)
        if sel_var == 'Visc@40C (cSt)':
            st.subheader("🛢️ Alertas/Precauciones por lubricante (Visc@40C)")
            df_visc40 = df[df[status_col].isin(['Alert','Caution'])].copy()
            # Convertir a numérico antes de agrupar
            df_visc40[sel_var] = pd.to_numeric(df_visc40[sel_var], errors='coerce')
            df_visc40 = (
                df_visc40
                .groupby('Tested Lubricant')[sel_var]
                .agg(**{
                    '# Alertas/Precauciones':'count',
                    'Promedio':'mean'
                })
                .round(0)
                .astype(int)
                .reset_index()
                .rename(columns={'Tested Lubricant':'Lubricante'})
            )
            st.table(df_visc40[['Lubricante','# Alertas/Precauciones','Promedio']])

