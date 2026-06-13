function ConfidenceCalibration({ data, loading }) {

    const buckets = data ?? []
    const validBuckets = buckets.filter(b => b.accuracy !== null)

    // Simple "is calibration good" check: accuracy should trend upward with confidence
    const isWellCalibrated = (() => {
        if (validBuckets.length < 2) return null
        for (let i = 1; i < validBuckets.length; i++) {
            if (validBuckets[i].accuracy < validBuckets[i - 1].accuracy - 5) return false
        }
        return true
    })()

    return (
        <div className="cc-card">
            <h3 className="cc-title">Confidence vs Accuracy</h3>
            <p className="cc-subtitle">Does higher model confidence mean higher accuracy?</p>

            {loading ? (
                <div className="cc-skeleton" />
            ) : buckets.length === 0 ? (
                <div className="cc-empty">Not enough data yet</div>
            ) : (
                <>
                    <div className="cc-chart">
                        {buckets.map(({ bucket, accuracy, count }) => (
                            <div className="cc-col" key={bucket}>
                                <div className="cc-bar-area">
                                    {accuracy !== null ? (
                                        <div
                                            className="cc-bar"
                                            style={{
                                                height: `${accuracy}%`,
                                                background: accuracy >= 60 ? "#22c55e" : accuracy >= 45 ? "#f97316" : "#ef4444"
                                            }}
                                        >
                                            <span className="cc-bar-value">{accuracy}%</span>
                                        </div>
                                    ) : (
                                        <div className="cc-bar-empty">
                                            <span className="cc-bar-empty-label">n/a</span>
                                        </div>
                                    )}
                                </div>
                                <span className="cc-bucket-label">{bucket}</span>
                                <span className="cc-bucket-count">{count} preds</span>
                            </div>
                        ))}
                    </div>

                    {isWellCalibrated !== null && (
                        <div className={`cc-insight ${isWellCalibrated ? "good" : "warn"}`}>
                            {isWellCalibrated
                                ? "Accuracy generally increases with confidence — confidence scores are meaningful."
                                : "Accuracy does not consistently increase with confidence — confidence scores may be unreliable."}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}

export default ConfidenceCalibration
