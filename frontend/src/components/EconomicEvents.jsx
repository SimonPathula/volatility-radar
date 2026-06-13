function EconomicEvents({ events, date }) {

    const impactColor = (impact) => {
        if (impact === "High") return "#ef4444"
        if (impact === "Medium") return "#f97316"
        return "#22c55e"
    }

    const displayDate = date || "—"
    const data = events  // null = not loaded, [] = no events

    return (
        <div className="ee-card">
            <h3 className="ee-title">Economic Events</h3>
            <p className="ee-date">for {displayDate}</p>

            <div className="ee-list">
                {data === null ? (
                    <div className="hv-empty">No prediction yet</div>
                ) : data.length === 0 ? (
                    <div className="hv-empty">No events for this date</div>
                ) : (
                    data.map((event, i) => (
                        <div className="ee-row" key={i}>
                            <div className="ee-currency-badge">
                                {event.currency}
                            </div>
                            <div className="ee-info">
                                <span className="ee-name">{event.currency} {event.event}</span>
                                <span
                                    className="ee-impact"
                                    style={{ color: impactColor(event.impact) }}
                                >
                                    [impact: {event.impact}]
                                </span>
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    )
}

export default EconomicEvents