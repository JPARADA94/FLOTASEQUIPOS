    # Fila 2: Pareto de fallas y estados de muestras
    r2c1, r2c2 = st.columns([3, 2])
    with r2c1:
        st.subheader("📋 Pareto de fallas (Top 15)")
        result_cols = [c for c in df.columns if c.startswith('RESULT_')]
        counts = {
            c.replace('RESULT_', ''): df[c + '_status'].isin(['Alert', 'Caution']).sum()
            for c in result_cols
        }
        top15 = pd.Series(counts).sort_values(ascending=False).head(15)
        fig_p, ax_p = plt.subplots(figsize=(8, 4))
        ax_p.barh(top15.index, top15.values, color='skyblue')
        ax_p.invert_yaxis()
        ax_p.set_xlabel('Número de fallas')
        for i, v in enumerate(top15.values):
            ax_p.text(v + top15.max()*0.01, i, str(v), va='center')
        cum = top15.cumsum() / top15.sum() * 100
        axp_line = ax_p.twiny()
        axp_line.plot(cum.values, range(len(cum)), '-o', color='black')
        axp_line.set_xlabel('% acumulado')
        for i, p in enumerate(cum):
            axp_line.text(p + 1, i, f"{p:.0f}%", va='center')
        fig_p.tight_layout()
        st.pyplot(fig_p)

    with r2c2:
        st.subheader("📊 Estados de muestras")
        status_order = ['Normal', 'Caution', 'Alert']
        cnt2 = df['Report Status'].value_counts().reindex(status_order, fill_value=0)
        cmap = {'Normal':'#2ecc71','Caution':'#f1c40f','Alert':'#e74c3c'}
        fig2, ax2 = plt.subplots(figsize=(8, 4))
        ax2.bar(cnt2.index, cnt2.values, color=[cmap[s] for s in cnt2.index])
        for i, v in enumerate(cnt2.values):
            ax2.text(i, v + cnt2.max()*0.01, str(v), ha='center')
        ax2.set_xlabel('Estado')
        ax2.set_ylabel('Cantidad de muestras')
        fig2.tight_layout()
        st.pyplot(fig2)
