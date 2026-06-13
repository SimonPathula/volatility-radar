// function PredictionCard({ result }) {

//     // Placeholder data when no result yet
//     const data = result ? {
//         pair: result.pair,
//         date: result.date || result.prediction_for,
//         signal: result.prediction,
//         probabilities: {
//             bullish: Math.round(result.bullish_probability * 100),
//             neutral: Math.round(result.neutral_probability * 100),
//             bearish: Math.round(result.bearish_probability * 100),
//         },
//         confidence: Math.round(result.confidence * 100),
//     } : {
//         pair: "EURUSD",
//         date: "2026-06-04",
//         signal: "Bullish",
//         probabilities: { bullish: 68, neutral: 20, bearish: 12 },
//         confidence: 46,
//     }

//     const { pair, date, signal, probabilities, confidence } = data

//     const signalColor =
//         signal === "Bullish" ? "#22c55e" :
//         signal === "Bearish" ? "#ef4444" :
//         "#888"

//     const primaryProbability =
//     signal === "Bullish" ? probabilities.bullish :
//     signal === "Bearish" ? probabilities.bearish :
//     probabilities.neutral

//     const primaryBarColor = signalColor

//     return (
//         <div className="prediction-card">

//             {/* Header row */}
//             <div className="pc-header">
//                 <span className="pc-pair">{pair}</span>
//                 <span className="pc-date">{date}</span>
//             </div>

//             {/* Big signal label */}
//             <div className="pc-signal" style={{ color: signalColor }}>
//                 {signal}
//             </div>

//             {/* Primary probability bar */}
//             <div className="pc-primary-bar-row">
//                 <span className="pc-primary-label" style={{ background: signalColor }}>
//                     {signal}
//                 </span>
//                 <div className="pc-bar-track">
//                     <div
//                         className="pc-bar-fill"
//                         style={{ width: `${primaryProbability}%`, background: signalColor }}
//                     />
//                 </div>
//                 <span className="pc-pct">{primaryProbability}%</span>
//             </div>

//             {/* Breakdown bars */}
//             <div className="pc-breakdown">
//                 {[
//                     { label: "Bullish", value: probabilities.bullish, color: "#22c55e" },
//                     { label: "Neutral", value: probabilities.neutral, color: "#888" },
//                     { label: "Bearish", value: probabilities.bearish, color: "#ef4444" },
//                 ].map(({ label, value, color }) => (
//                     <div className="pc-breakdown-row" key={label}>
//                         <span className="pc-breakdown-label">{label}: {value}%</span>
//                         <div className="pc-bar-track">
//                             <div
//                                 className="pc-bar-fill"
//                                 style={{ width: `${value}%`, background: color }}
//                             />
//                         </div>
//                     </div>
//                 ))}
//             </div>

//             {/* Confidence meter */}
//             <div className="pc-confidence">
//                 <span className="pc-confidence-label">Confidence Meter:</span>
//                 <div className="pc-confidence-row">
//                     <div className="pc-bar-track">
//                         <div
//                             className="pc-bar-fill"
//                             style={{ width: `${confidence}%`, background: "#aaa" }}
//                         />
//                     </div>
//                     <span className="pc-pct">{confidence}%</span>
//                 </div>
//             </div>

//         </div>
//     )
// }

// export default PredictionCard

function PredictionCard({ result }) {

    const data = result ? {
        pair: result.pair,
        date: result.date || result.prediction_for,
        signal: result.prediction,
        probabilities: {
            bullish: Math.round(result.bullish_probability * 100),
            neutral: Math.round(result.neutral_probability * 100),
            bearish: Math.round(result.bearish_probability * 100),
        },
        confidence: Math.round(result.confidence * 100),
    } : {
        pair: "EURUSD",
        date: "2026-06-04",
        signal: "Bullish",
        probabilities: { bullish: 68, neutral: 20, bearish: 12 },
        confidence: 46,
    }

    const { pair, date, signal, probabilities, confidence } = data

    const signalColor =
        signal === "Bullish" ? "#22c55e" :
        signal === "Bearish" ? "#ef4444" :
        "#888"

    const primaryProbability =
        signal === "Bullish" ? probabilities.bullish :
        signal === "Bearish" ? probabilities.bearish :
        probabilities.neutral

    // Donut arc calculation
    const radius = 36
    const circumference = 2 * Math.PI * radius
    const offset = circumference - (primaryProbability / 100) * circumference

    return (
        <div className="prediction-card">

            {/* Header row */}
            <div className="pc-header">
                <span className="pc-pair">{pair}</span>
                <span className="pc-date">{date}</span>
            </div>

            {/* Signal + donut row */}
            <div className="pc-signal-row">
                <div className="pc-signal" style={{ color: signalColor }}>
                    {signal}
                </div>

                {/* Donut */}
                <div className="pc-donut-wrapper">
                    <svg width="88" height="88" viewBox="0 0 88 88">
                        <circle
                            cx="44" cy="44" r={radius}
                            fill="none"
                            stroke="#f0f0f0"
                            strokeWidth="8"
                        />
                        <circle
                            cx="44" cy="44" r={radius}
                            fill="none"
                            stroke={signalColor}
                            strokeWidth="8"
                            strokeDasharray={circumference}
                            strokeDashoffset={offset}
                            strokeLinecap="round"
                            transform="rotate(-90 44 44)"
                            style={{ transition: "stroke-dashoffset 0.6s ease" }}
                        />
                    </svg>
                    <div className="pc-donut-label">
                        <span className="pc-donut-pct">{primaryProbability}%</span>
                    </div>
                </div>
            </div>

            {/* Breakdown bars */}
            <div className="pc-breakdown">
                {[
                    { label: "Bullish", value: probabilities.bullish, color: "#22c55e" },
                    { label: "Neutral", value: probabilities.neutral, color: "#aaa" },
                    { label: "Bearish", value: probabilities.bearish, color: "#ef4444" },
                ].map(({ label, value, color }) => (
                    <div className="pc-breakdown-row" key={label}>
                        <span className="pc-breakdown-label">{label}</span>
                        <div className="pc-bar-track">
                            <div
                                className="pc-bar-fill"
                                style={{ width: `${value}%`, background: color }}
                            />
                        </div>
                        <span className="pc-breakdown-pct">{value}%</span>
                    </div>
                ))}
            </div>

            {/* Confidence meter */}
            <div className="pc-confidence">
                <div className="pc-confidence-header">
                    <span className="pc-confidence-label">Confidence</span>
                    <span className="pc-confidence-pct">{confidence}%</span>
                </div>
                <div className="pc-bar-track">
                    <div
                        className="pc-bar-fill"
                        style={{
                            width: `${confidence}%`,
                            background: confidence > 65 ? "#22c55e" : confidence > 40 ? "#f97316" : "#ef4444"
                        }}
                    />
                </div>
            </div>

        </div>
    )
}

export default PredictionCard