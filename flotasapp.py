# flotasapp.py
# Autor: [Tu Nombre]
# Fecha de creación: 2025-07-20
# Descripción: Aplicación Streamlit para análisis de datos de flotas basado en formato Mobil Serv
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
# Encabezados esperados y mapeo de estados
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
# Variables disponibles para correlación e intervalos
# ---------------------------------------------
vars_correl = [
    'K (Potassium)', 'Na (Sodium)', 'Si (Silicon)', 'Water (Vol%)',
    'Al (Aluminum)', 'Cr (Chromium)', 'Cu (Copper)', 'Fe (Iron)', 'Mo (Molybdenum)',
    'Pb (Lead)', 'PQ Index', 'Oxidation (Ab/cm)', 'TBN (mg KOH/g)', 'Visc@100C (cSt)',
    'TAN (mg KOH/g)', 'Fuel Dilut. (Vol%)', 'Nitration (Ab/cm)', 'Particle Count  >4um',
    'Particle Count  >6um', 'Particle Count>14um', 'Visc@40C (cSt)', 'Soot (Wt%)'
]

# ---------------------------------------------
# Título e instrucciones
# ---------------------------------------------
st.title("📊 Análisis de Flotas - Mobil Serv")
# Mostrar información de autor
st.markdown(
    """
    **Autor:** Tu Nombre  \
    **Fecha de creación:** 2025-07-20
    """
)
st.markdown(
    """
    Esta aplicación permite analizar datos históricos de flotas.
    ✅ **Importante:** el archivo Excel debe estar filtrado (un único tipo de equipo) y seguir el formato **Mobil Serv**.
    """
)

# ---------------------------------------------
# Carga del archivo
# ---------------------------------------------
archivo = st.file_uploader("📁 Sube tu archivo Excel (.xlsx)", type=["xlsx"])
if not archivo:
    st.info("Espera a subir un archivo para comenzar el análisis.")
    st.stop()

# ---------------------------------------------
# Procesamiento principal
# ---------------------------------------------
try:
    # Leer y validar columnas
    df = pd.read_excel(archivo)
    falt = sorted(set(columnas_esperadas) - set(df.columns))
    if falt:
        st.error("❌ Faltan columnas en el archivo:")
        st.code("\n".join(falt))
        st.stop()

    # Convertir fechas
    df['Date Reported'] = pd.to_datetime(df['Date Reported'], errors='coerce')

    # Limpieza y conversión a numérico de variables de análisis
    for col in vars_correl:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                     .str.replace(r"[^0-9\.\-]", "", regex=True),
                errors='coerce'
            )

    # Mapear columnas RESULT_ a estados
    result_cols = [c for c in df.columns if c.startswith('RESULT_')]
    for c in result_cols:
        df[c + '_status'] = df[c].astype(str).str.strip().map(lambda x: status_map.get(x, 'Normal'))

    # Cálculo de métricas generales
    total = len(df)
    lubs = df['Tested Lubricant'].nunique()
    ops = df['Account Name'].nunique()
    fecha_min = df['Date Reported'].min().date()
    fecha_max = df['Date Reported'].max().date()
    equipos = df['Unit ID'].nunique()
    
    # Intervalo medio global
    df_sorted = df.sort_values(['Unit ID', 'Date Reported'])
    mean_int = df_sorted.groupby('Unit ID')['Date Reported'].apply(lambda x: x.diff().dt.days.mean())
    overall_mean = mean_int.mean()

    # ---------------------------------------------
    # Resumen general
    # ---------------------------------------------
    st.subheader("🔎 Resumen general")
    st.markdown(f"""
- Total muestras: **{total}**  
- Lubricantes distintos: **{lubs}**  
- Operaciones distintas: **{ops}**  
- Rango de fechas: **{fecha_min}** a **{fecha_max}**  
- Equipos distintos: **{equipos}**  
- Intervalo medio de muestreo: **{overall_mean:.1f}** días
""")

        # ---------------------------------------------
    # Opción de filtrado de equipos
    # ---------------------------------------------
    st.markdown("### Filtrado de equipos a analizar")
    unidades = df['Unit ID'].unique().tolist()
    modo = st.radio(
        "¿Deseas analizar todos los equipos o excluir algunos?", 
        ("Todos","Excluir algunos"),
        horizontal=True
    )
    if modo == "Excluir algunos":
        excl = st.multiselect("Selecciona equipos a excluir:", unidades)
        if excl:
            df = df[~df['Unit ID'].isin(excl)]
    
    # ---------------------------------------------
    # Gráficos fijos (3 filas x 2 columnas)
    # --------------------------------------------- (3 filas x 2 columnas)
    # ---------------------------------------------
    # Fila 1: Estados y frecuencia
    c1, c2 = st.columns(2)
    with c1:
        st.subheader("📈 Estados de muestras")
        vc = df['Report Status'].value_counts()
        orden = ['Normal', 'Caution', 'Alert']
        vals = [vc.get(o, 0) for o in orden]
        cols = ['#2ecc71', '#f1c40f', '#e74c3c']
        fig1, ax1 = plt.subplots(figsize=(4, 3))
        ax1.bar(orden, vals, color=cols)
        ax1.set_ylabel('Cantidad de muestras')
        for i, v in enumerate(vals): ax1.text(i, v + 2, str(v), ha='center')
        st.pyplot(fig1)
    with c2:
        st.subheader("📊 Frecuencia de muestreo (Top 15 equipos)")
        top15 = df['Unit ID'].value_counts().head(15)
        cols2 = sns.color_palette('viridis', len(top15))
        fig2, ax2 = plt.subplots(figsize=(4, 3))
        ax2.barh(top15.index, top15.values, color=cols2)
        ax2.set_xlabel('Número de muestras')
        for i, v in enumerate(top15.values): ax2.text(v + 1, i, str(v), va='center')
        st.pyplot(fig2)

    # Fila 2: Intervalos promedio y Pareto Alert
    c3, c4 = st.columns(2)
    with c3:
        st.subheader("⏱️ Intervalo promedio (Top 15 equipos)")
        mean_top = mean_int.loc[top15.index].dropna()
        fig3, ax3 = plt.subplots(figsize=(4, 3))
        ax3.barh(mean_top.index, mean_top.values, color=sns.color_palette('mako', len(mean_top)))
        ax3.set_xlabel('Días promedio')
        for i, v in enumerate(mean_top.values): ax3.text(v + 0.5, i, f"{v:.1f}", va='center')
        st.markdown(f"**Nota:** Promedio Top 15 = {mean_top.mean():.1f} días")
        st.pyplot(fig3)
    with c4:
        st.subheader("📋 Pareto: Alert por parámetro (Top 10)")
        alert_ser = pd.Series({
            c.replace('RESULT_', ''): (df[c + '_status'] == 'Alert').sum()
            for c in result_cols
        }).sort_values(ascending=False).head(10)
        cols4 = sns.color_palette('Reds', len(alert_ser))
        fig4, ax4 = plt.subplots(figsize=(4, 3))
        alert_ser.plot.barh(color=cols4, ax=ax4)
        ax4.invert_yaxis()
        ax4.set_xlabel('Número de Alertas')
        ax4.grid(axis='x', linestyle='--', alpha=0.5)
        for i, v in enumerate(alert_ser.values): ax4.text(v + 1, i, str(v), va='center')
        cum4 = alert_ser.cumsum() / alert_ser.sum() * 100
        ax4_line = ax4.twiny()
        ax4_line.plot(cum4.values, range(len(cum4)), '-o', color='black')
        ax4_line.set_xlabel('% acumulado')
        for i, pct in enumerate(cum4): ax4_line.text(pct + 2, i, f"{pct:.0f}%", va='center')
        st.pyplot(fig4)

    # Fila 3: Pareto Caution y combos Alert
    c5, c6 = st.columns(2)
    with c5:
        st.subheader("📋 Pareto: Caution por parámetro (Top 10)")
        caut_ser = pd.Series({
            c.replace('RESULT_', ''): (df[c + '_status'] == 'Caution').sum()
            for c in result_cols
        }).sort_values(ascending=False).head(10)
        cols5 = sns.color_palette('YlOrBr', len(caut_ser))
        fig5, ax5 = plt.subplots(figsize=(4, 3))
        caut_ser.plot.barh(color=cols5, ax=ax5)
        ax5.invert_yaxis()
        ax5.set_xlabel('Número de Cautions')
        ax5.grid(axis='x', linestyle='--', alpha=0.5)
        for i, v in enumerate(caut_ser.values): ax5.text(v + 1, i, str(v), va='center')
        cum5 = caut_ser.cumsum() / caut_ser.sum() * 100
        ax5_line = ax5.twiny()
        ax5_line.plot(cum5.values, range(len(cum5)), '-o', color='black')
        ax5_line.set_xlabel('% acumulado')
        for i, pct in enumerate(cum5): ax5_line.text(pct + 2, i, f"{pct:.0f}%", va='center')
        st.pyplot(fig5)
    with c6:
        st.subheader("🔗 Pareto: combos Alert (Top 10)")
        combos = {}
        for _, row in df.iterrows():
            alerts = [c.replace('RESULT_', '') for c in result_cols if row[c + '_status'] == 'Alert']
            if len(alerts) > 1:
                for a, b in combinations(alerts, 2):
                    key = f"{a} & {b}"
                    combos[key] = combos.get(key, 0) + 1
        comb_ser = pd.Series(combos).sort_values(ascending=False).head(10)
        cols6 = sns.color_palette('PuRd', len(comb_ser))
        fig6, ax6 = plt.subplots(figsize=(4, 3))
        comb_ser.plot.barh(color=cols6, ax=ax6)
        ax6.invert_yaxis()
        ax6.set_xlabel('Número de muestras')
        ax6.grid(axis='x', linestyle='--', alpha=0.5)
        for i, v in enumerate(comb_ser.values): ax6.text(v + 1, i, str(v), va='center')
        cum6 = comb_ser.cumsum() / comb_ser.sum() * 100
        ax6_line = ax6.twiny()
        ax6_line.plot(cum6.values, range(len(cum6)), '-o', color='black')
        ax6_line.set_xlabel('% acumulado')
        for i, pct in enumerate(cum6): ax6_line.text(pct + 2, i, f"{pct:.0f}%", va='center')
        st.pyplot(fig6)

    # ---------------------------------------------
    # Correlación de variables seleccionadas (Heatmap ajustado)
    # ---------------------------------------------
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    valid_vars = [v for v in vars_correl if v in numeric_cols]
    if not valid_vars:
        st.warning("No hay variables numéricas válidas para correlación.")
    else:
        st.markdown(
            """
            **Heatmap de correlación**: interpreta los coeficientes de Pearson.
            - **1.0** = correlación positiva perfecta
            - **0.0** = sin correlación lineal
            - **-1.0** = correlación negativa perfecta
            """
        )
        n = st.number_input(
            "¿Cuántas variables quieres correlacionar?", min_value=2,
            max_value=len(valid_vars), value=2, step=1
        )
        sel = st.multiselect(
            "Selecciona las variables:", valid_vars,
            default=valid_vars[:n]
        )
        if len(sel) == n:
            # limpiar y convertir
            for col in sel:
                df[col] = pd.to_numeric(
                    df[col].astype(str).str.replace(r"[^0-9\.\-]", "", regex=True),
                    errors='coerce'
                )
            corr = df[sel].corr()
            size = max(4, n * 0.6)
            annot_font = max(6, 14 - n)
            fig7, ax7 = plt.subplots(figsize=(size, size))
            sns.heatmap(
                corr, annot=True, fmt='.2f', cmap='coolwarm',
                annot_kws={'fontsize': annot_font}, linewidths=0.5,
                square=True, ax=ax7
            )
            ax7.set_xticklabels(ax7.get_xticklabels(), rotation=45, ha='right', fontsize=annot_font)
            ax7.set_yticklabels(ax7.get_yticklabels(), rotation=0, fontsize=annot_font)
            ax7.set_title('Heatmap de correlación', fontsize=annot_font+2)
            st.pyplot(fig7)
        else:
            st.warning(f"Selecciona exactamente {n} variables.")

    # ---------------------------------------------
    # Distribución por intervalos - Variable 1
    # ---------------------------------------------
    st.subheader("📊 Distribución por intervalos (Variable 1)")
    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    vars_int = [v for v in vars_correl if v in numeric_cols]
    var1 = st.selectbox("Variable 1:", vars_int, key="var1")
    n_int1 = st.number_input("Número de intervalos Variable 1:", min_value=2, max_value=50, value=5, step=1, key="n_int1")
    if var1:
        s1 = df[var1].dropna()
        bins1 = pd.interval_range(start=s1.min(), end=s1.max(), periods=n_int1)
        counts1 = [s1.between(iv.left, iv.right, inclusive='left').sum() for iv in bins1]
        labels1 = [f"< {bins1[0].right:.2f}"] + [f"{iv.left:.2f}-{iv.right:.2f}" for iv in bins1[1:]]
        col1a, col1r = st.columns(2)
        with col1a:
            st.markdown("**Frecuencia absoluta**: número de muestras en cada intervalo.")
            fig1a, ax1a = plt.subplots(figsize=(4,3))
            ax1a.bar(labels1, counts1, color=sns.color_palette('tab10', len(labels1)))
            ax1a.set_ylabel('Conteo')
            ax1a.set_xticklabels(labels1, rotation=45, ha='right')
            st.pyplot(fig1a)
        with col1r:
            st.markdown("**Frecuencia relativa (%)**: porcentaje de muestras en cada intervalo.")
            rel1 = [c/sum(counts1)*100 if sum(counts1)>0 else 0 for c in counts1]
            fig1r, ax1r = plt.subplots(figsize=(4,3))
            ax1r.bar(labels1, rel1, color=sns.color_palette('tab20', len(labels1)))
            ax1r.set_ylabel('Porcentaje')
            ax1r.set_xticklabels(labels1, rotation=45, ha='right')
            st.pyplot(fig1r)

    # ---------------------------------------------
    # Distribución por intervalos - Variable 2
    # ---------------------------------------------
    st.subheader("📊 Distribución por intervalos (Variable 2)")
    var2 = st.selectbox("Variable 2:", vars_int, key="var2")
    n_int2 = st.number_input("Número de intervalos Variable 2:", min_value=2, max_value=50, value=5, step=1, key="n_int2")
    if var2:
        s2 = df[var2].dropna()
        bins2 = pd.interval_range(start=s2.min(), end=s2.max(), periods=n_int2)
        counts2 = [s2.between(iv.left, iv.right, inclusive='left').sum() for iv in bins2]
        labels2 = [f"< {bins2[0].right:.2f}"] + [f"{iv.left:.2f}-{iv.right:.2f}" for iv in bins2[1:]]
        col2a, col2r = st.columns(2)
        with col2a:
            st.markdown("**Frecuencia absoluta**: número de muestras en cada intervalo.")
            fig2a, ax2a = plt.subplots(figsize=(4,3))
            ax2a.bar(labels2, counts2, color=sns.color_palette('tab10', len(labels2)))
            ax2a.set_ylabel('Conteo')
            ax2a.set_xticklabels(labels2, rotation=45, ha='right')
            st.pyplot(fig2a)
        with col2r:
            st.markdown("**Frecuencia relativa (%)**: porcentaje de muestras en cada intervalo.")
            rel2 = [c/sum(counts2)*100 if sum(counts2)>0 else 0 for c in counts2]
            fig2r, ax2r = plt.subplots(figsize=(4,3))
            ax2r.bar(labels2, rel2, color=sns.color_palette('tab20', len(labels2)))
            ax2r.set_ylabel('Porcentaje')
            ax2r.set_xticklabels(labels2, rotation=45, ha='right')
            st.pyplot(fig2r)

except Exception as e:
    st.error(f"❌ Error al procesar archivo: {e}")
    st.error(f"❌ Error al procesar archivo: {e}")
    st.error(f"❌ Error al procesar archivo: {e}")

except Exception as e:
    st.error(f"❌ Error al procesar archivo: {e}")
    st.error(f"❌ Error al procesar archivo: {e}")
