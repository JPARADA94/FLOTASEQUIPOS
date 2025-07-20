# flotasapp.py
# Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv

import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Configuración de la página
st.set_page_config(page_title="Análisis de Flotas - Mobil Serv", layout="wide")

# Encabezados esperados (nombres visibles)
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

# Columnas de desgaste para reemplazar vacíos
columnas_desgaste = [
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)',
    'Mo (Molybdenum)', 'Pb (Lead)', 'PQ Index'
]

# Título e instrucciones iniciales
st.title("📊 Análisis de Flotas de Equipos - Mobil Serv")
st.markdown(
    """
    Esta aplicación analiza datos históricos de flotas específicas.

    ✅ **Importante:** el archivo Excel debe estar filtrado (un solo modelo) y usar formato **Mobil Serv**.
    """
)

# Subida de archivo
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])

if archivo:
    try:
        # Lectura y validación de columnas
        df = pd.read_excel(archivo)
        cols = set(df.columns.astype(str))
        if not set(columnas_esperadas).issubset(cols):
            faltantes = sorted(set(columnas_esperadas) - cols)
            st.error("❌ Archivo inválido: faltan columnas:")
            st.code("\n".join(faltantes))
            st.stop()

        # Convertir fecha
        df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

        # Métricas generales
        total_muestras = len(df)
        unique_lub = df['Tested Lubricant'].nunique()
        lubs = df['Tested Lubricant'].unique().tolist()
        unique_ops = df['Account Name'].nunique()
        ops = df['Account Name'].unique().tolist()
        fecha_min = df['Date Reported'].min().date()
        fecha_max = df['Date Reported'].max().date()
        equipos = df['Unit ID'].nunique()

        # Mostrar resumen
        st.subheader("🔎 Resumen general de los datos")
        st.markdown(f"""
- **Total de muestras:** {total_muestras}
- **Lubricantes analizados:** {unique_lub}
- **Operaciones:** {unique_ops}
- **Rango de fechas:** {fecha_min} a {fecha_max}
- **Equipos analizados:** {equipos}
"""
        )
        with st.expander("📦 Lista de lubricantes"):
            for lub in lubs:
                st.write(f"• {lub}")
        with st.expander("🚩 Lista de operaciones"):
            for op in ops:
                st.write(f"• {op}")

        # Reemplazar vacíos en columnas de desgaste
        for col in columnas_desgaste:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col].fillna(0), errors='coerce')

        # Columnas con pocos datos
        invalidas = [(c, df[c].notna().sum()) for c in df.columns if df[c].notna().sum() < 5]
        if invalidas:
            with st.expander("📋 Columnas ignoradas (datos insuficientes)"):
                for c, n in invalidas:
                    st.write(f"• {c}: {n} datos válidos")

        # Preparar diseño de grillas
        col1, col2 = st.columns(2)

        # 1. Gráfico: Distribución de Report Status
        with col1:
            st.subheader("📈 Estados de muestras (Report Status)")
            conteo = df['Report Status'].value_counts()
            # Etiquetas y colores dinámicos
            labels_map = {'Normal': '🟢 Normal', 'Precaution': '🟡 Precaución', 'Abnormal': '🔴 Alerta'}
            display = [labels_map.get(lbl, lbl) for lbl in conteo.index]
            valores = conteo.values
            colors = [('#2ecc71' if lbl=='Normal' else '#f1c40f' if lbl=='Precaution' else '#e74c3c') for lbl in conteo.index]

            fig, ax = plt.subplots(figsize=(4,3))
            sns.barplot(x=display, y=valores, palette=colors, ax=ax)
            ax.set_ylabel("Cantidad de muestras")
            ax.set_xlabel("")
            ax.spines[['top','right']].set_visible(False)
            for p in ax.patches:
                ax.annotate(int(p.get_height()),
                            (p.get_x()+p.get_width()/2, p.get_height()),
                            ha='center', va='bottom')
            st.pyplot(fig)
            st.markdown("🔍 Prioriza acciones en 🟡 Precaución y 🔴 Alerta.")

        # 2. Gráfico: Frecuencia de muestreo top 15
        with col2:
            n_top = min(15, df['Unit ID'].nunique())
            st.subheader(f"📊 Muestreos: Top {n_top} equipos")
            top_counts = df['Unit ID'].value_counts().head(n_top)
            fig2, ax2 = plt.subplots(figsize=(4,3))
            sns.barplot(x=top_counts.values, y=top_counts.index, palette='Blues_r', ax=ax2)
            ax2.set_xlabel("Número de muestras")
            ax2.set_ylabel("")
            ax2.spines[['top','right']].set_visible(False)
            for p in ax2.patches:
                ax2.annotate(int(p.get_width()),
                             (p.get_width()+0.5, p.get_y()+p.get_height()/2),
                             va='center')
            st.pyplot(fig2)

        # 3. Intervalo promedio de muestreo Top 15
        st.subheader("⏱️ Intervalo promedio de muestreo - Top 15 equipos")
        df_sorted = df.sort_values(['Unit ID','Date Reported'])
        mean_intervals = df_sorted.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
        top_units = top_counts.index
        mean_top = mean_intervals.loc[top_units].dropna()
        fig3, ax3 = plt.subplots(figsize=(6,3))
        sns.barplot(x=mean_top.values, y=mean_top.index, palette='mako', ax=ax3)
        ax3.set_xlabel('Días promedio')
        ax3.set_ylabel('Unit ID')
        ax3.spines[['top','right']].set_visible(False)
        for p in ax3.patches:
            ax3.annotate(f"{p.get_width():.1f}",
                         (p.get_width()+0.5, p.get_y()+p.get_height()/2),
                         va='center')
        st.pyplot(fig3)

        # Promedio global de muestreo
overall_mean = mean_intervals.mean()
        st.markdown(f"**Intervalo medio de muestreo de toda la flota:** {overall_mean:.1f} días")

    except Exception as e:
        st.error(f"❌ Error al procesar archivo: {e}")



