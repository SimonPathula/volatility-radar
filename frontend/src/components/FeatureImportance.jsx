function FeatureImportance({ data, loading }) {

    const features = data ?? []
    const maxImpact = features.length > 0
        ? Math.max(...features.map(f => f.avg_abs_impact))
        : 1

    return (
        <div className="fi-card">
            <h3 className="fi-title">Top Features Driving Predictions</h3>
            <p className="fi-subtitle">Average absolute SHAP impact across recent predictions</p>

            {loading ? (
                <div className="fi-skeleton" />
            ) : features.length === 0 ? (
                <div className="fi-empty">Not enough data yet</div>
            ) : (
                <div className="fi-list">
                    {features.map(({ feature, avg_abs_impact, appearances }) => {
                        const barWidth = Math.round((avg_abs_impact / maxImpact) * 100)
                        return (
                            <div className="fi-row" key={feature}>
                                <div className="fi-row-top">
                                    <span className="fi-feature">{feature}</span>
                                    <span className="fi-value">{avg_abs_impact.toFixed(3)}</span>
                                </div>
                                <div className="fi-bar-track">
                                    <div className="fi-bar-fill" style={{ width: `${barWidth}%` }} />
                                </div>
                                <span className="fi-appearances">appeared in top drivers {appearances}x</span>
                            </div>
                        )
                    })}
                </div>
            )}
        </div>
    )
}

export default FeatureImportance
