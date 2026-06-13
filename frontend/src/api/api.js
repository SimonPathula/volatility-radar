const BASE_URL = "http://localhost:8000"

export async function predict(pair, date) {
    const response = await fetch(`${BASE_URL}/predict`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pair, date })
    })

    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Prediction failed")
    }

    return response.json()
}

export async function explain(pair, date) {
    const response = await fetch(`${BASE_URL}/explain`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pair, date })
    })

    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Explanation failed")
    }

    return response.json()
}

export async function getHistoricValidation(pair, date) {
    const response = await fetch(`${BASE_URL}/historic_validation`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pair, date })
    })

    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Historic validation failed")
    }

    return response.json()
}

export async function getEconomicEvents(pair, date) {
    const response = await fetch(`${BASE_URL}/events?pair=${pair}&date=${date}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch events")
    }
    return response.json()
}

export async function getOhlcData(pair, date) {
    const response = await fetch(`${BASE_URL}/ohlcdata`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ pair, date })
    })
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "OHLC fetch failed")
    }
    return response.json()
}

export async function getPriceHistory(pair, fromDate) {
    const response = await fetch(`${BASE_URL}/prices/${pair}?from_date=${fromDate}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Price history fetch failed")
    }
    return response.json()
}

// === ADD TO api.js ===

export async function getOverview(lookbackDays = 180) {
    const response = await fetch(`${BASE_URL}/analytics/overview?lookback_days=${lookbackDays}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch overview")
    }
    return response.json()
}

export async function getConfusionMatrix(lookbackDays = 180) {
    const response = await fetch(`${BASE_URL}/analytics/confusion_matrix?lookback_days=${lookbackDays}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch confusion matrix")
    }
    return response.json()
}

export async function getConfidenceCalibration(lookbackDays = 180) {
    const response = await fetch(`${BASE_URL}/analytics/confidence_calibration?lookback_days=${lookbackDays}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch confidence calibration")
    }
    return response.json()
}

export async function getAccuracyTrend(lookbackDays = 180) {
    const response = await fetch(`${BASE_URL}/analytics/accuracy_trend?lookback_days=${lookbackDays}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch accuracy trend")
    }
    return response.json()
}

export async function getFeatureImportance(lookbackDays = 180) {
    const response = await fetch(`${BASE_URL}/analytics/feature_importance?lookback_days=${lookbackDays}`)
    if (!response.ok) {
        const err = await response.json()
        throw new Error(err.detail || "Failed to fetch feature importance")
    }
    return response.json()
}