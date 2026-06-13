function PerformanceOverview({ data, loading }) {

    const overallAccuracy = data?.overall_accuracy ?? null
    const macroF1 = data?.macro_f1 ?? null
    const precision = data?.precision ?? {}
    const total = data?.total_predictions ?? null

    const metrics = [
        { label: "Bullish Precision", value: precision.Bullish, color: "#22c55e" },
        { label: "Neutral Precision", value: precision.Neutral, color: "#888" },
        { label: "Bearish Precision", value: precision.Bearish, color: "#ef4444" },
        { label: "Macro F1 Score", value: macroF1, color: "#111" },
    ]

    return (
        <div className="po-card">
            <div className="po-primary">
                <span className="po-primary-label">Overall Accuracy</span>
                {loading ? (
                    <div className="po-skeleton po-skeleton-big" />
                ) : (
                    <span className="po-primary-value">
                        {overallAccuracy !== null ? `${overallAccuracy}%` : "—"}
                    </span>
                )}
                {total !== null && !loading && (
                    <span className="po-sample-size">based on {total} predictions</span>
                )}
            </div>

            <div className="po-divider" />

            <div className="po-metrics">
                {metrics.map(({ label, value, color }) => (
                    <div className="po-metric" key={label}>
                        <span className="po-metric-label">{label}</span>
                        {loading ? (
                            <div className="po-skeleton po-skeleton-small" />
                        ) : (
                            <span className="po-metric-value" style={{ color }}>
                                {value !== undefined && value !== null ? `${value}%` : "—"}
                            </span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    )
}

export default PerformanceOverview
