import { useRef, useState } from "react"
import { predict, explain, getHistoricValidation, getEconomicEvents, getPriceHistory } from "../api/api"

import PairSelector from "../components/PairSelector"
import DatePickerBox from "../components/DatePickerBox"
import PredictionButton from "../components/PredictionButton"
import PredictionCard from "../components/PredictionCard"
import HistoricalValidation from "../components/HistoricalValidation"
import TopDrivers from "../components/TopDrivers"
import EconomicEvents from "../components/EconomicEvents"
import ExplainButton from "../components/ExplainButton"
import PriceChart from "../components/PriceChart"

import "../styles/control-panel.css"
import "../styles/prediction-card.css"
import "../styles/historical-validation.css"
import "../styles/top-drivers.css"
import "../styles/economic-events.css"
import "../styles/price-chart.css"

function Dashboard() {
    const [pair, setPair] = useState("EURUSD")
    const [date, setDate] = useState("")
    const [result, setResult] = useState(null)
    const [explanation, setExplanation] = useState(null)
    const [explaining, setExplaining] = useState(false)
    const [showExplanation, setShowExplanation] = useState(false)
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)
    const [validation, setValidation] = useState(null)
    const [validationLoading, setValidationLoading] = useState(false)
    const [events, setEvents] = useState(null)
    const [priceHistory, setPriceHistory] = useState(null)
    const [chartDate, setChartDate] = useState(null)
    const [warning, setWarning] = useState(null)

    const predictionRequestId = useRef(0)

    async function handlePrediction() {
        if (!date) {
            setError("Please select a date first.")
            return
        }

        const requestId = predictionRequestId.current + 1
        predictionRequestId.current = requestId

        setLoading(true)
        setValidationLoading(true)
        setError(null)
        setWarning(null)
        setEvents(null)
        setValidation(null)
        setResult(null)
        setExplanation(null)
        setShowExplanation(false)

        setPriceHistory(null)
        setChartDate(null)

        try {
            const predData = await predict(pair, date)

            if (requestId !== predictionRequestId.current) return

            setResult(predData)
            setChartDate(date)
            if (predData.warning) setWarning(predData.warning)
        } catch (err) {
            if (requestId !== predictionRequestId.current) return

            setError(err.message)
            setLoading(false)
            setValidationLoading(false)
            return
        }

        setLoading(false)

        getHistoricValidation(pair, date)
            .then(d => {
                if (requestId === predictionRequestId.current) setValidation(d)
            })
            .catch(() => {
                if (requestId === predictionRequestId.current) setValidation(null)
            })
            .finally(() => {
                if (requestId === predictionRequestId.current) setValidationLoading(false)
            })

        getEconomicEvents(pair, date)
            .then(d => {
                if (requestId === predictionRequestId.current) setEvents(d)
            })
            .catch(() => {
                if (requestId === predictionRequestId.current) setEvents([])
            })

        getPriceHistory(pair, date)
            .then(d => {
                if (requestId === predictionRequestId.current) setPriceHistory(d)
            })
            .catch(() => {
                if (requestId === predictionRequestId.current) setPriceHistory([])
            })
    }

    async function handleExplain() {
        if (!date) {
            setError("Please select a date first.")
            return
        }

        setExplaining(true)
        setShowExplanation(false)
        setExplanation(null)
        setError(null)

        try {
            const data = await explain(pair, date)
            setExplanation(data.explanation)
            setShowExplanation(true)
        } catch (err) {
            setError(err.message)
        } finally {
            setExplaining(false)
        }
    }

    return (
        <main className="dashboard">
            <section className="control-panel-wrapper">
                <div className="control-panel">
                    <PairSelector pair={pair} setPair={setPair} />
                    <DatePickerBox date={date} setDate={setDate} />
                    <PredictionButton handlePrediction={handlePrediction} loading={loading} />
                    <ExplainButton onClick={handleExplain} loading={explaining} />
                </div>

                {error && (
                    <div className="error-strip">
                        <span>⚠</span>
                        <span>{error}</span>
                    </div>
                )}

                {warning && (
                    <div className="warning-strip">
                        <span>⚠</span>
                        <span>{warning}</span>
                    </div>
                )}

                {showExplanation && (
                    <div className="explanation-strip">
                        <span className="explanation-strip-label">✦</span>
                        <p className="explanation-strip-text">
                            {explanation}
                        </p>
                    </div>
                )}
            </section>

            <div className="cards-grid">
                <div className="cards-left">
                    <PredictionCard result={result} />

                    <HistoricalValidation
                        result={result}
                        validation={validation}
                        validationLoading={validationLoading}
                    />
                </div>

                <div className="cards-center">
                    <PriceChart
                        date={chartDate}
                        pair={pair}
                        priceHistory={priceHistory}
                    />
                </div>

                <div className="cards-right">
                    <TopDrivers drivers={result?.top_drivers} />
                    <EconomicEvents events={events} date={date} />
                </div>
            </div>
        </main>
    )
}

export default Dashboard