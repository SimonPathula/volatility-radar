import { useState, useEffect } from "react"
import {
    getOverview,
    getConfusionMatrix,
    getConfidenceCalibration,
    getAccuracyTrend,
    getFeatureImportance
} from "../api/api"

import PerformanceOverview from "../components/PerformanceOverview"
import ConfusionMatrix from "../components/ConfusionMatrix"
import ConfidenceCalibration from "../components/ConfidenceCalibration"
import AccuracyTrend from "../components/AccuracyTrend"
import FeatureImportance from "../components/FeatureImportance"

import "../styles/performance-overview.css"
import "../styles/confusion-matrix.css"
import "../styles/confidence-calibration.css"
import "../styles/accuracy-trend.css"
import "../styles/feature-importance.css"
import "../styles/analytics.css"

function Analytics() {

    const [overview, setOverview] = useState(null)
    const [confusionMatrix, setConfusionMatrix] = useState(null)
    const [calibration, setCalibration] = useState(null)
    const [trend, setTrend] = useState(null)
    const [featureImportance, setFeatureImportance] = useState(null)
    const [loading, setLoading] = useState(true)
    const [error, setError] = useState(null)

    useEffect(() => {
        let cancelled = false

        async function loadAnalytics() {
            setLoading(true)
            setError(null)

            try {
                const [ov, cm, cal, tr, fi] = await Promise.all([
                    getOverview(),
                    getConfusionMatrix(),
                    getConfidenceCalibration(),
                    getAccuracyTrend(),
                    getFeatureImportance()
                ])

                if (cancelled) return

                setOverview(ov)
                setConfusionMatrix(cm)
                setCalibration(cal)
                setTrend(tr)
                setFeatureImportance(fi)
            } catch (err) {
                if (!cancelled) setError(err.message)
            } finally {
                if (!cancelled) setLoading(false)
            }
        }

        loadAnalytics()

        return () => { cancelled = true }
    }, [])

    return (
        <main className="analytics-page">

            {error && (
                <div className="error-strip">
                    <span>⚠</span>
                    <span>{error}</span>
                </div>
            )}

            <PerformanceOverview data={overview} loading={loading} />

            <div className="analytics-grid">
                <ConfusionMatrix data={confusionMatrix} loading={loading} />
                <ConfidenceCalibration data={calibration} loading={loading} />
                <AccuracyTrend data={trend} loading={loading} />
                <FeatureImportance data={featureImportance} loading={loading} />
            </div>

        </main>
    )
}

export default Analytics
