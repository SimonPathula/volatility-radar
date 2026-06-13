function AccuracyTrend({ data, loading }) {

    const trend = data ?? []

    const width = 600
    const height = 180
    const padding = { top: 20, right: 16, bottom: 28, left: 36 }
    const chartWidth = width - padding.left - padding.right
    const chartHeight = height - padding.top - padding.bottom

    const minAcc = 0
    const maxAcc = 100

    const points = trend.map((d, i) => {
        const x = trend.length === 1
            ? padding.left + chartWidth / 2
            : padding.left + (i / (trend.length - 1)) * chartWidth
        const y = padding.top + chartHeight - ((d.accuracy - minAcc) / (maxAcc - minAcc)) * chartHeight
        return { x, y, ...d }
    })

    const linePath = points.map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`).join(" ")
    const areaPath = points.length > 0
        ? `${linePath} L ${points[points.length - 1].x} ${padding.top + chartHeight} L ${points[0].x} ${padding.top + chartHeight} Z`
        : ""

    const avgAccuracy = trend.length > 0
        ? Math.round(trend.reduce((sum, d) => sum + d.accuracy, 0) / trend.length)
        : null

    const formatMonth = (monthKey) => {
        const [year, month] = monthKey.split("-")
        const date = new Date(parseInt(year), parseInt(month) - 1)
        return date.toLocaleString("default", { month: "short" })
    }

    return (
        <div className="at-card">
            <div className="at-header">
                <h3 className="at-title">Accuracy Over Time</h3>
                {avgAccuracy !== null && !loading && (
                    <span className="at-avg">Avg: {avgAccuracy}%</span>
                )}
            </div>

            {loading ? (
                <div className="at-skeleton" />
            ) : trend.length === 0 ? (
                <div className="at-empty">Not enough data yet</div>
            ) : (
                <svg viewBox={`0 0 ${width} ${height}`} className="at-svg" preserveAspectRatio="none">
                    {/* gridlines */}
                    {[0, 25, 50, 75, 100].map(val => {
                        const y = padding.top + chartHeight - (val / 100) * chartHeight
                        return (
                            <g key={val}>
                                <line x1={padding.left} x2={width - padding.right} y1={y} y2={y} stroke="#f0f0f0" strokeWidth="1" />
                                <text x={padding.left - 8} y={y + 4} textAnchor="end" fontSize="10" fill="#bbb">{val}%</text>
                            </g>
                        )
                    })}

                    {/* area fill */}
                    <path d={areaPath} fill="url(#at-gradient)" />

                    {/* line */}
                    <path d={linePath} fill="none" stroke="#111" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

                    {/* points */}
                    {points.map((p) => (
                        <g key={p.month}>
                            <circle cx={p.x} cy={p.y} r="4" fill="#fff" stroke="#111" strokeWidth="2.5" />
                            <text x={p.x} y={height - 6} textAnchor="middle" fontSize="11" fill="#888" fontWeight="600">
                                {formatMonth(p.month)}
                            </text>
                        </g>
                    ))}

                    <defs>
                        <linearGradient id="at-gradient" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="0%" stopColor="#111" stopOpacity="0.08" />
                            <stop offset="100%" stopColor="#111" stopOpacity="0" />
                        </linearGradient>
                    </defs>
                </svg>
            )}
        </div>
    )
}

export default AccuracyTrend
