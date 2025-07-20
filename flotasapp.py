# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

# ---------------------------------------------
# 1. IMPORTACIÓN DE LIBRERÍAS NECESARIAS
# ---------------------------------------------
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------------------------------
# 2. CONFIGURACIÓN INICIAL DE LA APLICACIÓN
# ---------------------------------------------
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# ---------------------------------------------
# 3. LISTA DE ENCABEZADOS ESPERADOS
# ---------------------------------------------
columnas_esperadas = [
    'B (Boron)', 'Ca (Calcium)', 'Mg (Magnesium)', 'P (Phosphorus)', 'Zn (Zinc)',
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index',
    'Report Status', 'Date Reported', 'Unit ID', 'Tested Lubricant', 'Manufacturer', 'Alt Model',
    'Account Name', 'Parent Account Name', 'Equipment Age', 'Oil Age', 'Oxidation (Ab/cm)',
    'TBN (mg KOH/g)', 'Visc@100C (cSt)', 'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)',
    'Particle Count  >4um', 'Particle Count  >6um', 'Particle Count>14um',
    'Visc@40C (cSt)', 'Soot (Wt%)'
]

# Columnas de desgaste
columnas_desgaste = [
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)',
    'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index'
]

# ---------------------------------------------
# 4. TÍTULO Y DESCRIPCIÓN
# ---------------------------------------------
st.title("📊 Análisis de Datos de Flotas de Equipos - Mobil Serv")
st.markdown("""
Esta aplicación analiza datos históricos de flotas específicas.

✅ **Importante:** el archivo Excel debe estar filtrado (un solo modelo) y usar formato **Mobil Serv**.
""")

# ---------------------------------------------
# 5. SUBIDA DE ARCHIVO
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx) en formato Mobil Serv", type=["xlsx"])

# ---------------------------------------------
# 6. PROCESAMIENTO Y MÉTRICAS GENERALES
# ---------------------------------------------
if archivo:
    try:
        df = pd.read_excel(archivo)
        cols = set(df.columns.astype(str))
        req = set(columnas_esperadas)

        # Validar formato Mobil Serv
        if not req.issubset(cols):
            faltantes = sorted(req - cols)
            st.error("❌ Archivo inválido: faltan columnas:")
            st.code("\n".join(faltantes))
            st.info("Asegúrate de usar el formato Mobil Serv completo.")
            st.stop()

        # Convertir fecha y métricas básicas
        df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')
        total_muestras = len(df)
        unique_lub = df['Tested Lubricant'].nunique()
        lubs = df['Tested Lubricant'].unique().tolist()
        unique_ops = df['Account Name'].nunique()
        ops = df['Account Name'].unique().tolist()
        fecha_min = df['Date Reported'].min().date()
        fecha_max = df['Date Reported'].max().date()
        equipos = df['Unit ID'].nunique()

        # Resumen general
        st.subheader("🔎 Resumen general de los datos")
        st.markdown(f"""
- **Total de muestras:** {total_muestras}
- **Lubricantes analizados:** {unique_lub}
- **Operaciones:** {unique_ops}
- **Rango de fechas:** {fecha_min} a {fecha_max}
- **Equipos analizados:** {equipos}
""")

        # Detalles en expanders
        with st.expander("📦 Lista de lubricantes"):
            for lub in lubs:
                st.write(f"• {lub}")
        with st.expander("🚩 Lista de operaciones"):
            for op in ops:
                st.write(f"• {op}")

        # Preprocesar columnas de desgaste
        for col in columnas_desgaste:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].fillna(0), errors='coerce')

        # Columnas con datos insuficientes
        invalidas = [(c, df[c].notna().sum()) for c in df.columns if df[c].notna().sum() < 5]
        if invalidas:
            with st.expander("📋 Columnas ignoradas (datos insuficientes)"):
                for c, n in invalidas:
                    st.write(f"• {c}: {n} datos válidos")

        # ---------------------------------------------
# 7. GRÁFICOS EN UNA SOLA FILA
# ---------------------------------------------
col1, col2 = st.columns(2)

# Gráfico 1: Distribución de estados
with col1:
    st.subheader("📈 Distribución por estado")
    conteo = df['Report Status'].value_counts()
    labels_map = {'Normal': '🟢 Normal', 'Precaution': '🟡 Precaución', 'Abnormal': '🔴 Alerta'}
    display = [labels_map.get(e, e) for e in conteo.index]
    valores = conteo.values
    palette = ['#2ecc71', '#f1c40f', '#e74c3c']  # verde, amarillo, rojo

    fig, ax = plt.subplots(figsize=(4, 3))
    sns.barplot(x=display, y=valores, palette=palette[:len(display)], ax=ax)
    ax.set_ylabel("Cantidad")
    ax.set_xlabel("")
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    for p in ax.patches:
        ax.annotate(int(p.get_height()),
                    (p.get_x() + p.get_width() / 2, p.get_height()),
                    ha='center', va='bottom', fontsize=10)
    st.pyplot(fig)
    st.markdown("""
🔍 **Nota**: Prioriza acciones en 🟡 Precaución y 🔴 Alerta.
""")

# Gráfico 2: Frecuencia top N equipos
with col2:
    # Determinar cuántos equipos mostrar (hasta 15)
    n_top = min(15, df['Unit ID'].nunique())
    st.subheader(f"📊 Frecuencia de muestreo: Top {n_top} equipos")
    top_counts = df['Unit ID'].value_counts().head(n_top)
    fig2, ax2 = plt.subplots(figsize=(4, 3.5))
    sns.barplot(x=top_counts.values, y=top_counts.index, palette='Blues_r', ax=ax2)
    ax2.set_xlabel("Número de muestras")
    ax2.set_ylabel("")
    ax2.spines['top'].set_visible(False)
    ax2.spines['right'].set_visible(False)
    for p in ax2.patches:
        ax2.annotate(int(p.get_width()),
                     (p.get_width() + 0.5, p.get_y() + p.get_height() / 2),
                     va='center', fontsize=9)
    st.pyplot(fig2)

# ---------------------------------------------
# 8. INTERVALOS DE MUESTREO
# ---------------------------------------------
st.subheader("⏱️ Intervalos de muestreo")
# Calcular diferencias de días entre muestras por equipo
df_sorted = df.sort_values(['Unit ID', 'Date Reported'])
intervals = df_sorted.groupby('Unit ID')['Date Reported'].diff().dt.days.dropna()

if not intervals.empty:
    fig3, ax3 = plt.subplots(figsize=(6, 3))
    sns.histplot(intervals, bins=20, kde=False, ax=ax3)
    ax3.set_xlabel('Días entre muestras')
    ax3.set_ylabel('Frecuencia')
    ax3.spines['top'].set_visible(False)
    ax3.spines['right'].set_visible(False)
    st.pyplot(fig3)
else:
    st.info("No hay suficientes datos de fecha para calcular intervalos.")

# ---------------------------------------------
# 9. PARETO DE ALERTAS Y PRECAUCIÓN POR EQUIPO
# ---------------------------------------------
st.subheader("📋 Pareto de muestras en Precaución y Alerta por equipo")
# Filtrar muestras en estado Precaución o Alerta
df_pareto = df[df['Report Status'].isin(['Precaution', 'Abnormal'])]
pareto_counts = df_pareto['Unit ID'].value_counts()
# Calcular porcentaje acumulado
cumperc = pareto_counts.cumsum() / pareto_counts.sum() * 100

fig4, ax4 = plt.subplots(figsize=(6, 3.5))
# Barras
sns.barplot(x=pareto_counts.values, y=pareto_counts.index, color='#e74c3c', ax=ax4)
# Línea de acumulado
ax4_line = ax4.twiny()
ax4_line.plot(cumperc.values, cumperc.index, '-o', color='#3498db')
ax4_line.set_xlabel('Porcentaje acumulado')

# Etiquetas y estilo
ax4.set_xlabel('Número de muestras')
ax4.set_ylabel('Unit ID')
ax4.spines['top'].set_visible(False)
ax4.spines['right'].set_visible(False)
ax4_line.spines['top'].set_visible(False)
ax4_line.spines['right'].set_visible(False)

# Anotar valores en barras y acumulado
for p in ax4.patches:
    ax4.annotate(int(p.get_width()),
                 (p.get_width() + 0.5, p.get_y() + p.get_height() / 2),
                 va='center', fontsize=9)
for x, y in zip(cumperc.values, cumperc.index):
    ax4_line.annotate(f"{x:.0f}%", (x, y), textcoords="offset points", xytext=(5,-5), fontsize=8)

st.pyplot(fig4)

