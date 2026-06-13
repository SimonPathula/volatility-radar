function TopDrivers({ drivers }) {

    const placeholder = [
        { feature: "rolling_std_10", value: 0.248, shap_impact: 0.18 },
        { feature: "candle_body", value: 0.003, shap_impact: 0.09 },
        { feature: "max_surprise_z", value: 1.2, shap_impact: -0.07 },
        { feature: "rolling_std_20", value: 0.281, shap_impact: -0.11 },
        { feature: "atr_14", value: 0.006, shap_impact: -0.10 },
    ]

    const data = drivers || placeholder

    const maxImpact = Math.max(...data.map(r => Math.abs(r.shap_impact)))

    return (
        <div className="td-card">
            <h3 className="td-title">Top Drivers</h3>

            <div className="td-table">
                <div className="td-header">
                    <span>Feature</span>
                    <span>SHAP Impact</span>
                </div>

                {data.map((row, i) => {
                    const impact = row.shap_impact
                    const isPositive = impact > 0
                    const barWidth = Math.round((Math.abs(impact) / maxImpact) * 100)

                    return (
                        <div className="td-row" key={i}>
                            <div className="td-feature-col">
                                <span className="td-feature">{row.feature}</span>
                                <div className="td-bar-track">
                                    <div
                                        className="td-bar-fill"
                                        style={{
                                            width: `${barWidth}%`,
                                            background: isPositive ? "#22c55e" : "#ef4444"
                                        }}
                                    />
                                </div>
                            </div>
                            <span className={`td-impact ${isPositive ? "positive" : "negative"}`}>
                                {isPositive ? `+${impact.toFixed(3)}` : impact.toFixed(3)}
                            </span>
                        </div>
                    )
                })}
            </div>
        </div>
    )
}

export default TopDrivers