function HistoricalValidation({ result, validation, validationLoading }) {

    const prediction = result?.prediction || "—"
    const confidence = result ? Math.round(result.confidence * 100) : null

    // actual result — null if future prediction
    const actual = result?.actual || null
    const correct = result?.correct ?? null
    const isFuture = result && actual === null

    // backtest stats
    const accuracy = validation?.accuracy ?? null
    const correct30 = validation?.correct_predictions ?? null
    const total30 = validation?.total_predictions ?? 30
    const incorrect30 = correct30 !== null ? total30 - correct30 : null

    return (
        <div className="hv-card">

            {/* Section 1 — Prediction */}
            <div className="hv-section">
                <div className="hv-section-title">Prediction</div>
                <div className="hv-divider" />
                {result ? (
                    <>
                        <div className={`hv-signal ${prediction.toLowerCase()}`}>
                            {prediction}
                        </div>
                        <div className="hv-confidence">
                            Confidence: {confidence}%
                        </div>
                    </>
                ) : (
                    <div className="hv-empty">No prediction yet</div>
                )}
            </div>

            {/* Section 2 — Historical Validation */}
            <div className="hv-section">
                <div className="hv-section-title">Historical Validation</div>
                <div className="hv-divider" />
                {validationLoading ? (
                    <div className="hv-loader-wrapper">
                        <div className="hv-spinner" />
                        <span className="hv-empty">Calculating...</span>
                    </div>
                ) : validation ? (
                    <>
                        <div className="hv-stat-label">Last {total30} Predictions</div>
                        <div className="hv-accuracy">Accuracy: {accuracy}%</div>
                        <div className="hv-stat-row">
                            <span className="hv-correct">✓ {correct30} Correct</span>
                            <span className="hv-incorrect">✗ {incorrect30} Incorrect</span>
                        </div>
                    </>
                ) : (
                    <div className="hv-empty">No validation data</div>
                )}
            </div>

            {/* Section 3 — Actual Result */}
            <div className="hv-section">
                <div className="hv-section-title">Actual Result</div>
                <div className="hv-divider" />
                {!result ? (
                    <div className="hv-empty">No prediction yet</div>
                ) : isFuture ? (
                    <div className="hv-empty">N/A (future prediction)</div>
                ) : (
                    <>
                        <div className="hv-row">
                            <span className="hv-label">Prediction:</span>
                            <span className="hv-value">{prediction}</span>
                        </div>
                        <div className="hv-row">
                            <span className="hv-label">Actual:</span>
                            <span className="hv-value">{actual}</span>
                        </div>
                        <div className={`hv-verdict ${correct ? "correct" : "incorrect"}`}>
                            {correct ? "✅ Correct" : "❌ Incorrect"}
                        </div>
                    </>
                )}
            </div>

        </div>
    )
}

export default HistoricalValidation