# flotasapp.py
# Autor: Javier Parada
# Formato de entrada: ARCHIVO 2 (nuevo)
# Mejoras: cache de lectura, compatibilidad nativa con ARCHIVO 2, optimización combinaciones (Counter + itertuples),
#          controles de robustez (fechas NaT, pareto vacío), evita SettingWithCopy.

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import string
from itertools import combinations
from collections import Counter

st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")
st.title("📊 Análisis de Flotas - Mobil Serv")
st.markdown("""
Esta aplicación analiza datos de flotas con base en informes (formato ARCHIVO 2).
Filtra por operación, clase de activo, lubricante y fecha, y luego pulsa "🚀 Empezar análisis".
AUTOR: Javier Parada.
""")

# =========================
# Helpers (ARCHIVO 2 nativo)
# =========================
@st.cache_data(show_spinner=False)
def load_excel(file) -> pd.DataFrame:
    return pd.read_excel(file)

def prepare_archivo2(df: pd.DataFrame) -> pd.DataFrame:
    """
    Convierte ARCHIVO 2 a las columnas que espera la app, sin perder nada del dataframe original.
    También crea columnas RESULT_... a partir de las columnas '... - Estado' (ALERTA/PRECAUCION/NORMAL).
    """
    df = df.copy()

    # Validación mínima ARCHIVO 2
    required_cols_new = [
        'NOMBRE_OPERACION', 'TIPO_EQUIPO', 'PRODUCTO', 'ESTADO_REPORTE',
        'FECHA_INFORME', 'EQUIPO'
    ]
    missing = [c for c in required_cols_new if c not in df.columns]
    if missing:
        st.error(f"❌ Falta(n) columna(s) requerida(s) en ARCHIVO 2: {missing}")
        st.stop()

    # Columnas base (equivalentes a tu app original)
    df['Account Name'] = df['NOMBRE_OPERACION'].astype(str)
    df['Asset Class'] = df['TIPO_EQUIPO'].astype(str)
    df['Tested Lubricant'] = df['PRODUCTO'].astype(str)

    # Estado global del reporte
    map_status = {'NORMAL': 'Normal', 'PRECAUCION': 'Caution', 'ALERTA': 'Alert'}
    df['Report Status'] = (
        df['ESTADO_REPORTE'].astype(str).str.strip().str.upper()
        .map(map_status)
        .fillna('Normal')
    )

    # Fecha reporte
    df['Date Reported'] = pd.to_datetime(df['FECHA_INFORME'], errors='coerce')

    # IDs: muestra y equipo
    # Preferimos CORRELATIVO por ser más probable que sea único; si no existe, usa N_MUESTRA; si no, index
    if 'CORRELATIVO' in df.columns:
        df['Sample Bottle ID'] = df['CORRELATIVO'].astype(str)
    elif 'N_MUESTRA' in df.columns:
        df['Sample Bottle ID'] = df['N_MUESTRA'].astype(str)
    else:
        df['Sample Bottle ID'] = df.index.astype(str)

    df['Asset ID'] = df['EQUIPO'].astype(str)

    # RESULT_... desde columnas "... - Estado"
    # Convierte: ALERTA->"*", PRECAUCION->"+", NORMAL->""
    estado_to_symbol = {'ALERTA': '*', 'PRECAUCION': '+', 'NORMAL': ''}

    estado_cols = [c for c in df.columns if ' - Estado' in str(c)]
    for c_estado in estado_cols:
        base = str(c_estado).replace(' - Estado ', '').replace(' - Estado', '').strip()
        # Creamos RESULT_base solo si existe la columna base (numérica o texto con números)
        if base in df.columns:
            df[f"RESULT_{base}"] = (
                df[c_estado].astype(str).str.strip().str.upper()
                .map(estado_to_symbol)
                .fillna('')
            )

    return df

# ========== Carga de archivo ==========
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx) - ARCHIVO 2", type=["xlsx"])
if not archivo:
    st.stop()

df_raw = load_excel(archivo)
df_raw = prepare_archivo2(df_raw)

# Validación de columnas clave (las que usa tu app)
required_cols = [
    'Account Name', 'Asset Class', 'Tested Lubricant', 'Report Status',
    'Date Reported', 'Sample Bottle ID', 'Asset ID'
]
for col in required_cols:
    if col not in df_raw.columns:
        st.error(f"❌ Falta columna requerida: {col}")
        st.stop()

# Fecha válida
if df_raw['Date Reported'].isna().all():
    st.error("❌ No hay fechas válidas en FECHA_INFORME / Date Reported (NaT). Revisa el Excel.")
    st.stop()

# ========== Filtros uno por fila y por fecha ==========
st.markdown("### 🎛️ Filtros de análisis")

cuentas = st.multiselect(
    "Selecciona cuenta(s) / operación(es)",
    df_raw['Account Name'].dropna().unique(),
    default=df_raw['Account Name'].dropna().unique()
)
df_fil = df_raw[df_raw['Account Name'].isin(cuentas)]

clases = st.multiselect(
    "Selecciona clase de activo",
    df_fil['Asset Class'].dropna().unique(),
    default=df_fil['Asset Class'].dropna().unique()
)
df_fil = df_fil[df_fil['Asset Class'].isin(clases)]

lubs = st.multiselect(
    "Selecciona lubricante(s)",
    df_fil['Tested Lubricant'].dropna().unique(),
    default=df_fil['Tested Lubricant'].dropna().unique()
)
df_fil = df_fil[df_fil['Tested Lubricant'].isin(lubs)]

# Copia para evitar SettingWithCopy y asegurar estabilidad
df_fil = df_fil.copy()

# Fechas filtrables
min_fecha = df_fil['Date Reported'].min()
max_fecha = df_fil['Date Reported'].max()

rango_fecha = st.checkbox("Filtrar por rango de fechas")
if rango_fecha:
    # Protege por si min/max son NaT
    if pd.isna(min_fecha) or pd.isna(max_fecha):
        st.warning("No se puede filtrar por fechas porque hay NaT en Date Reported.")
    else:
        fecha_ini, fecha_fin = st.date_input(
            "Selecciona rango de fechas:",
            value=[min_fecha.date(), max_fecha.date()],
            min_value=min_fecha.date(),
            max_value=max_fecha.date()
        )
        df_fil = df_fil[
            (df_fil['Date Reported'] >= pd.to_datetime(fecha_ini)) &
            (df_fil['Date Reported'] <= pd.to_datetime(fecha_fin))
        ].copy()

if df_fil.empty:
    st.warning("No hay datos con los filtros seleccionados.")
    st.stop()

# ========== Botón para análisis ==========
if 'analizado' not in st.session_state:
    st.session_state['analizado'] = False

if st.button("🚀 Empezar análisis"):
    st.session_state['analizado'] = True
if not st.session_state.get('analizado', False):
    st.stop()

# ========== Resumen General ==========
st.markdown("### 🧾 Resumen general del análisis")

df_nodup = df_fil.drop_duplicates(subset='Sample Bottle ID')
equipos_analizados = df_nodup['Asset ID'].nunique()

fecha_min = df_nodup['Date Reported'].min()
fecha_max = df_nodup['Date Reported'].max()
fecha_min_txt = fecha_min.date() if pd.notna(fecha_min) else "N/A"
fecha_max_txt = fecha_max.date() if pd.notna(fecha_max) else "N/A"

equipos_con_2m = df_nodup.groupby('Asset ID').filter(lambda x: len(x) >= 2).copy()
if not equipos_con_2m.empty:
    equipos_con_2m = equipos_con_2m.sort_values(['Asset ID', 'Date Reported'])
    equipos_con_2m['intervalo_dias'] = equipos_con_2m.groupby('Asset ID')['Date Reported'].diff().dt.days
    prom = equipos_con_2m['intervalo_dias'].mean()
    promedio_intervalo = round(prom, 1) if pd.notna(prom) else "N/A"
else:
    promedio_intervalo = "N/A"

st.markdown(f"""
- Total muestras (únicas): **{df_nodup.shape[0]}**
- Equipos analizados: **{equipos_analizados}**
- Rango de fechas: **{fecha_min_txt}** a **{fecha_max_txt}**
- Intervalo medio entre muestras (≥2 muestras): **{promedio_intervalo}**
""")

st.markdown("---")

# ========== 1ra fila: Muestras por cuenta ==========
cnt = df_fil['Account Name'].value_counts()
df_cnt = cnt.reset_index()
df_cnt.columns = ['Cuenta', 'Muestras']
df_cnt['Letra'] = list(string.ascii_lowercase[:len(df_cnt)])

# Paleta una vez (más eficiente)
pal = sns.color_palette('tab10', len(df_cnt))

r1c1, r1c2 = st.columns(2)
with r1c1:
    st.subheader("📊 Muestras por cuenta")
    fig1, ax1 = plt.subplots(figsize=(7, 4))
    ax1.bar(df_cnt['Letra'], df_cnt['Muestras'], color=pal)
    for i, v in enumerate(df_cnt['Muestras']):
        ax1.text(i, v + 0.5, str(int(v)), ha='center')
    ax1.set_xlabel('Cuenta')
    ax1.set_ylabel('Nº muestras')
    fig1.tight_layout()
    st.pyplot(fig1, use_container_width=True)

with r1c2:
    st.subheader("📋 Cuentas asignadas")
    tabla = df_cnt[['Letra', 'Cuenta', 'Muestras']].copy()
    tabla['% Muestras'] = ((tabla['Muestras'] / tabla['Muestras'].sum()) * 100).round(0).astype(int)

    styles = [
        {"selector": "th",
         "props": [("background-color", "#4f81bd"), ("color", "white"), ("text-align", "left")]},
        {"selector": "td",
         "props": [("padding", "8px"), ("border", "1px solid #ddd"), ("text-align", "left")]},
        {"selector": "tr:nth-child(even)", "props": [("background-color", "#f9f9f9")]}
    ]

    st.write(
        tabla.style
        .set_table_styles(styles)
        .background_gradient(subset=['% Muestras'], cmap='Blues')
        .format({'% Muestras': '{:.0f}%'})
    )

st.markdown("---")

# ========== 2da fila: Estado y muestras por año ==========
col3, col4 = st.columns(2)
with col3:
    st.subheader("📊 Estado de muestras")
    cnt2 = df_fil['Report Status'].value_counts().reindex(['Normal', 'Caution', 'Alert'], fill_value=0)
    cmap2 = {'Normal': '#2ecc71', 'Caution': '#f1c40f', 'Alert': '#e74c3c'}

    fig2, ax2 = plt.subplots(figsize=(7, 4))
    ax2.bar(cnt2.index, cnt2.values, color=[cmap2[s] for s in cnt2.index])
    for i, v in enumerate(cnt2.values):
        ax2.text(i, v + 0.5, str(int(v)), ha='center')
    ax2.set_xlabel('Estado')
    ax2.set_ylabel('Nº muestras')
    fig2.tight_layout()
    st.pyplot(fig2, use_container_width=True)

with col4:
    st.subheader("📈 Muestras por año")
    yearly = df_fil['Date Reported'].dt.year.value_counts().sort_index()
    figyr, axy = plt.subplots(figsize=(7, 4))
    axy.bar(yearly.index.astype(str), yearly.values, color='steelblue')
    for i, v in enumerate(yearly.values):
        axy.text(i, v + 0.5, str(int(v)), ha='center')
    axy.set_xlabel('Año')
    axy.set_ylabel('Nº muestras')
    figyr.tight_layout()
    st.pyplot(figyr, use_container_width=True)

st.markdown("---")

# ========== 3ra fila: Paretos ==========
# Mapea símbolos en RESULT_... a estatus
status_map = {'*': 'Alert', '+': 'Caution', '': 'Normal'}

# Construye columnas _status SOLO para columnas RESULT_
result_cols = [c for c in df_fil.columns if c.startswith('RESULT_') and not c.endswith('_status')]
for c in result_cols:
    df_fil[c + '_status'] = (
        df_fil[c].astype(str).str.strip()
        .map(lambda x: status_map.get(x, 'Normal'))
    )

col5, col6 = st.columns(2)

with col5:
    st.subheader("📋 Pareto de Alertas (Top 10)")

    # Cuenta Alertas por variable RESULT_
    cnts = {c.replace('RESULT_', ''): df_fil[c + '_status'].eq('Alert').sum() for c in result_cols}
    ser = pd.Series(cnts).loc[lambda x: x > 0].sort_values(ascending=False)
    top10 = ser.head(10) if len(ser) > 10 else ser

    if top10.empty:
        st.warning("No hay Alertas en variables RESULT_. (Con estos filtros)")

    else:
        etiquetas = [x.split('_')[-1] for x in top10.index]
        fig3, ax3 = plt.subplots(figsize=(7, 4))
        ax3.barh(etiquetas, top10.values, color='crimson')
        ax3.invert_yaxis()
        ax3.set_xlabel('Nº Alertas')

        for i, v in enumerate(top10.values):
            ax3.text(v + 0.5, i, str(int(v)), va='center')

        cum = top10.cumsum() / top10.sum() * 100
        ln = ax3.twiny()
        ln.plot(cum.values, range(len(cum)), '-o', color='black')
        ln.set_xlabel('% acumulado')
        for i, p in enumerate(cum):
            ln.text(p + 1, i, f"{int(p)}%", va='center')

        fig3.tight_layout()
        st.pyplot(fig3, use_container_width=True)

with col6:
    st.subheader("🔗 Pareto de combinaciones de fallas")

    status_cols = [c for c in df_fil.columns if c.endswith('_status')]
    combos = Counter()

    # Optimizado: itertuples + Counter (mismo resultado)
    for row in df_fil[status_cols].itertuples(index=False, name=None):
        alerts = [
            status_cols[i].replace('RESULT_', '').replace('_status', '')
            for i, stt in enumerate(row)
            if stt in ('Alert', 'Caution')
        ]
        for size in range(2, len(alerts) + 1):
            for combo in combinations(sorted(alerts), size):
                combos[' & '.join(combo)] += 1

    comb_ser = pd.Series(combos).loc[lambda x: x > 0].sort_values(ascending=False)
    topc = comb_ser.head(10) if len(comb_ser) > 10 else comb_ser

    if topc.empty:
        st.warning("No hay combinaciones de Alertas/Precauciones.")
    else:
        fig4, ax4 = plt.subplots(figsize=(7, 4))
        ax4.barh(topc.index, topc.values, color='#8e44ad')
        ax4.invert_yaxis()
        ax4.set_xlabel('Nº muestras')

        for i, v in enumerate(topc.values):
            ax4.text(v + 0.5, i, str(int(v)), va='center')

        cum2 = topc.cumsum() / topc.sum() * 100
        ln2 = ax4.twiny()
        ln2.plot(cum2.values, range(len(cum2)), '-o', color='black')
        ln2.set_xlabel('% acumulado')
        for i, p in enumerate(cum2):
            ln2.text(p + 1, i, f"{int(p)}%", va='center')

        fig4.tight_layout()
        st.pyplot(fig4, use_container_width=True)

st.markdown("---")

# ========== Análisis por variable ==========
st.markdown("### 🔍 Análisis por variable")

# Solo permite selector si existe top10 (si no, se mantiene toda la app sin romper)
if 'top10' not in locals() or top10.empty:
    st.info("No hay variables con Alertas para analizar en esta sección (con los filtros actuales).")
    st.stop()

pareto_vars = [x for x in top10.index]  # nombres base (sin RESULT_)
sel_var = st.selectbox("Selecciona variable de Pareto:", pareto_vars)

status_col = f"RESULT_{sel_var}_status"

desc_map = {
    'count': 'Número de muestras', 'mean': 'Media aritmética', 'std': 'Desviación estándar',
    'min': 'Valor mínimo', '25%': 'Primer cuartil', '50%': 'Mediana', '75%': 'Tercer cuartil', 'max': 'Valor máximo'
}

stats_col1, stats_col2 = st.columns(2)

with stats_col1:
    st.markdown("**Global**")
    if sel_var not in df_fil.columns:
        st.warning(f"No existe la columna numérica '{sel_var}' en el archivo (solo existe RESULT_{sel_var}).")
    else:
        series_glob = pd.to_numeric(df_fil[sel_var], errors='coerce')
        stats_glob = (series_glob.describe().round(0).fillna(0).astype(int)
                      .to_frame().rename(columns={sel_var: 'Valor'}))
        stats_glob['Descripción'] = stats_glob.index.map(lambda i: desc_map.get(i, i))
        st.table(stats_glob[['Descripción', 'Valor']])

with stats_col2:
    st.markdown("**Alert/Caution**")
    if sel_var not in df_fil.columns or status_col not in df_fil.columns:
        st.warning("No se puede calcular esta tabla porque falta la variable o su columna de estado.")
    else:
        df_sub = df_fil[df_fil[status_col].isin(['Alert', 'Caution'])]
        series_sub = pd.to_numeric(df_sub[sel_var], errors='coerce')
        stats_sub = (series_sub.describe().round(0).fillna(0).astype(int)
                     .to_frame().rename(columns={sel_var: 'Valor'}))
        stats_sub['Descripción'] = stats_sub.index.map(lambda i: desc_map.get(i, i))
        st.table(stats_sub[['Descripción', 'Valor']])

# Tabla especial para Visc@40C (cSt) - se mantiene (si el ARCHIVO 2 trae ese nombre exacto)
if sel_var == 'Visc@40C (cSt)':
    st.subheader("🛢️ Alertas/Precauciones por lubricante (Visc@40C)")
    if sel_var in df_fil.columns and status_col in df_fil.columns:
        df_visc40 = df_fil[df_fil[status_col].isin(['Alert', 'Caution'])].copy()
        df_visc40[sel_var] = pd.to_numeric(df_visc40[sel_var], errors='coerce')
        df_visc40 = (
            df_visc40
            .groupby('Tested Lubricant')[sel_var]
            .agg(**{
                '# Alertas/Precauciones': 'count',
                'Promedio': 'mean'
            })
            .round(0)
            .astype(int)
            .reset_index()
            .rename(columns={'Tested Lubricant': 'Lubricante'})
        )

        styles_visc = [
            {"selector": "th",
             "props": [("background-color", "#2f4f4f"), ("color", "white"), ("font-size", "14px"),
                       ("text-align", "center")]},
            {"selector": "td", "props": [("padding", "8px"), ("font-size", "13px"), ("text-align", "center")]},
            {"selector": "tr:nth-child(even)", "props": [("background-color", "#f0f0f0")]}
        ]

        styled_visc = (
            df_visc40[['Lubricante', '# Alertas/Precauciones', 'Promedio']]
            .style
            .set_table_styles(styles_visc)
            .background_gradient(subset=['# Alertas/Precauciones'], cmap='Oranges')
            .format({'Promedio': '{:.0f}'})
        )
        st.write(styled_visc)
    else:
        st.warning("No se encontró Visc@40C (cSt) o su estado en el archivo.")

st.markdown("---")

# ========== Mapa de calor final (dinámico para ARCHIVO 2) ==========
st.markdown("### 🔥 Mapa de calor de correlación")

# Excluir textos/IDs (mantiene tu sección pero adaptada al archivo 2)
exclude = {
    'NOMBRE_CLIENTE', 'NOMBRE_OPERACION', 'EQUIPO', 'TIPO_EQUIPO', 'PRODUCTO', 'ESTADO_REPORTE',
    'Account Name', 'Asset Class', 'Tested Lubricant', 'Report Status', 'Sample Bottle ID', 'Asset ID',
    'FECHA_INFORME'
}

valid_vars = []
for c in df_fil.columns:
    if c in exclude:
        continue
    if str(c).startswith('RESULT_') or str(c).endswith('_status'):
        continue
    # intentamos quedarnos con variables numéricas o que parezcan numéricas
    if df_fil[c].dtype != 'O':
        valid_vars.append(c)
    else:
        # si es objeto pero contiene números, se deja como candidata
        sample_nonnull = df_fil[c].dropna().astype(str).head(30)
        if not sample_nonnull.empty:
            looks_numeric = sample_nonnull.str.contains(r"\d", regex=True).mean() >= 0.6
            if looks_numeric:
                valid_vars.append(c)

# Quitar duplicados conservando orden
seen = set()
valid_vars = [x for x in valid_vars if not (x in seen or seen.add(x))]

if not valid_vars:
    st.warning("No hay variables numéricas válidas para correlación.")
else:
    n = st.number_input(
        "¿Cuántas variables quieres correlacionar?",
        min_value=2, max_value=len(valid_vars),
        value=min(5, len(valid_vars)), step=1
    )
    sel = st.multiselect("Selecciona las variables:", valid_vars, default=valid_vars[:n])

    if len(sel) == n:
        df_corr = df_fil.copy()
        for col in sel:
            df_corr[col] = pd.to_numeric(
                df_corr[col].astype(str).str.replace(r"[^0-9\.\-]", "", regex=True),
                errors='coerce'
            )

        corr = df_corr[sel].corr()
        size = max(4, n * 0.6)
        annot_font = max(6, 14 - n)

        fig, ax = plt.subplots(figsize=(size, size))
        sns.heatmap(
            corr, annot=True, fmt='.2f', cmap='coolwarm',
            annot_kws={'fontsize': annot_font},
            linewidths=0.5, square=True, ax=ax
        )
        ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right', fontsize=annot_font)
        ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=annot_font)
        ax.set_title('Heatmap de correlación', fontsize=annot_font + 2)
        fig.tight_layout()
        st.pyplot(fig, use_container_width=True)
    else:
        st.warning(f"Selecciona exactamente {n} variables.")

