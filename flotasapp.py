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
        req = set(columnas_esperadas)
        if not req.issubset(cols):
            faltantes = sorted(req - cols)
            st.error("❌ Archivo inválido: faltan columnas:")
            st.code("\n".join(faltantes))
            st.stop()

        # Convertir fechas
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

        # Gráficos en una sola fila
        col1, col2 = st.columns(2)

        # 1. Distribución de estados
        with col1:
            st.subheader("📈 Estados de muestras")
            conteo = df['Report Status'].value_counts()
            labels_map = {'Normal': 'Normal', 'Precaution': 'Precaución', 'Abnormal': 'Alerta'}
            valores = [conteo.get(k, 0) for k in ['Normal','Precaution','Abnormal']]
            etiquetas = ['🟢 Normal', '🟡 Precaución', '🔴 Alerta']
            fig, ax = plt.subplots(figsize=(4, 3))
            sns.barplot(x=etiquetas, y=valores, palette=['#2ecc71','#f1c40f','#e74c3c'], ax=ax)
            ax.set_ylabel("Cantidad")
            ax.set_xlabel("")
            ax.spines[['top','right']].set_visible(False)
            for p in ax.patches:
                ax.annotate(int(p.get_height()),
                            (p.get_x() + p.get_width()/2, p.get_height()),
                            ha='center', va='bottom')
            st.pyplot(fig)
            st.markdown("🔍 Prioriza acciones en 🟡 Precaución y 🔴 Alerta.")

        # 2. Frecuencia de muestreo top 15
        with col2:
            n_top = min(15, df['Unit ID'].nunique())
            st.subheader(f"📊 Muestreos: Top {n_top} equipos")
            top_counts = df['Unit ID'].value_counts().head(n_top)
            fig2, ax2 = plt.subplots(figsize=(4, 3))
            sns.barplot(x=top_counts.values, y=top_counts.index, palette='Blues_r', ax=ax2)
            ax2.set_xlabel("Número de muestras")
            ax2.set_ylabel("")
            ax2.spines[['top','right']].set_visible(False)
            for p in ax2.patches:
                ax2.annotate(int(p.get_width()),
                             (p.get_width()+0.5, p.get_y()+p.get_height()/2),
                             va='center')
            st.pyplot(fig2)

        # Intervalos de muestreo
        st.subheader("⏱️ Intervalos de muestreo (días)")
        df_sorted = df.sort_values(['Unit ID','Date Reported'])
        intervals = df_sorted.groupby('Unit ID')['Date Reported'].diff().dt.days.dropna()
        if not intervals.empty:
            fig3, ax3 = plt.subplots(figsize=(6, 3))
            sns.histplot(intervals, bins=20, ax=ax3)
            ax3.set_xlabel('Días entre muestras')
            ax3.set_ylabel('Frecuencia')
            ax3.spines[['top','right']].set_visible(False)
            st.pyplot(fig3)
        else:
            st.info("No hay suficientes datos de fecha para intervalos.")

        # Pareto de Precaución y Alerta
        st.subheader("📋 Pareto de Precaución + Alerta")
        df_p = df[df['Report Status'].isin(['Precaution','Abnormal'])]
        pareto = df_p['Unit ID'].value_counts()
        cumperc = pareto.cumsum()/pareto.sum()*100
        fig4, ax4 = plt.subplots(figsize=(6, 3))
        sns.barplot(x=pareto.values, y=pareto.index, color='#e74c3c', ax=ax4)
        ax4_t = ax4.twiny()
        ax4_t.plot(cumperc.values, cumperc.index, '-o', color='#3498db')
        ax4.set_xlabel('Número de muestras')
        ax4_t.set_xlabel('Porcentaje acumulado')
        ax4.spines[['top','right']].set_visible(False)
        ax4_t.spines[['top','right']].set_visible(False)
        for p in ax4.patches:
            ax4.annotate(int(p.get_width()),
                         (p.get_width()+0.5, p.get_y()+p.get_height()/2),
                         va='center')
        for x,y in zip(cumperc.values, cumperc.index):
            ax4_t.annotate(f"{x:.0f}%", (x, y), xytext=(5,-5), textcoords='offset points')
        st.pyplot(fig4)

    except Exception as e:
        st.error(f"❌ Error al procesar archivo: {e}")


