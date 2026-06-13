function ConfusionMatrix({ data, loading }) {

    const labels = data?.labels ?? ["Bearish", "Neutral", "Bullish"]
    const matrix = data?.matrix ?? null

    const maxValue = matrix
        ? Math.max(...labels.flatMap(actual => labels.map(pred => matrix[actual][pred])))
        : 1

    const cellColor = (value, isDiagonal) => {
        if (maxValue === 0) return "#f7f7f7"
        const intensity = value / maxValue
        if (isDiagonal) {
            // green scale for correct predictions
            const lightness = 95 - intensity * 50
            return `hsl(142, 60%, ${lightness}%)`
        }
        // red scale for confusions
        const lightness = 97 - intensity * 35
        return `hsl(0, 75%, ${lightness}%)`
    }

    const textColor = (value, isDiagonal) => {
        if (maxValue === 0) return "#bbb"
        const intensity = value / maxValue
        if (intensity > 0.6) return "#fff"
        return isDiagonal ? "#15803d" : "#b91c1c"
    }

    // Find the biggest off-diagonal confusion pair for the insight line
    const buildInsight = () => {
        if (!matrix) return null

        let topConfusion = null
        for (const actual of labels) {
            for (const pred of labels) {
                if (actual === pred) continue
                const value = matrix[actual][pred]
                if (!topConfusion || value > topConfusion.value) {
                    topConfusion = { actual, pred, value }
                }
            }
        }

        if (!topConfusion || topConfusion.value === 0) return null

        return `Model most often confuses ${topConfusion.actual} as ${topConfusion.pred} (${topConfusion.value} cases).`
    }

    const insight = buildInsight()

    return (
        <div className="cm-card">
            <h3 className="cm-title">Confusion Matrix</h3>

            {loading ? (
                <div className="cm-skeleton" />
            ) : (
                <>
                    <div className="cm-grid">
                        <div className="cm-corner" />
                        <div className="cm-axis-label cm-axis-top">Predicted</div>
                        <div className="cm-axis-label cm-axis-left">Actual</div>

                        <div className="cm-table">
                            <div className="cm-header-row">
                                <div className="cm-header-cell cm-row-label-spacer" />
                                {labels.map(label => (
                                    <div className="cm-header-cell" key={label}>{label}</div>
                                ))}
                            </div>
                            {labels.map(actual => (
                                <div className="cm-row" key={actual}>
                                    <div className="cm-row-label">{actual}</div>
                                    {labels.map(pred => {
                                        const value = matrix ? matrix[actual][pred] : 0
                                        const isDiagonal = actual === pred
                                        return (
                                            <div
                                                className="cm-cell"
                                                key={pred}
                                                style={{
                                                    background: cellColor(value, isDiagonal),
                                                    color: textColor(value, isDiagonal)
                                                }}
                                            >
                                                {value}
                                            </div>
                                        )
                                    })}
                                </div>
                            ))}
                        </div>
                    </div>

                    {insight && (
                        <div className="cm-insight">
                            <span className="cm-insight-icon">⚠</span>
                            <span>{insight}</span>
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default ConfusionMatrix
