import { useEffect, useRef } from "react"
import { createChart, CandlestickSeries, createSeriesMarkers } from "lightweight-charts"

function PriceChart({ date, pair, priceHistory }) {

    const chartContainerRef = useRef(null)
    const chartRef = useRef(null)
    const seriesRef = useRef(null)

    useEffect(() => {
        if (!chartContainerRef.current) return
        const container = chartContainerRef.current

        const chart = createChart(container, {
            width: container.clientWidth,
            height: container.clientHeight || 340,
            layout: { background: { color: "#ffffff" }, textColor: "#888" },
            grid: { vertLines: { color: "#f0f0f0" }, horzLines: { color: "#f0f0f0" } },
            rightPriceScale: { borderColor: "#f0f0f0" },
            timeScale: { borderColor: "#f0f0f0", timeVisible: true },
        })

        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#22c55e",
            downColor: "#ef4444",
            borderUpColor: "#22c55e",
            borderDownColor: "#ef4444",
            wickUpColor: "#22c55e",
            wickDownColor: "#ef4444",
        })

        chartRef.current = chart
        seriesRef.current = candleSeries

        const resizeObserver = new ResizeObserver(entries => {
            const { width, height } = entries[0].contentRect
            chart.applyOptions({ width, height })
        })
        resizeObserver.observe(container)

        return () => {
            resizeObserver.disconnect()
            chart.remove()
            chartRef.current = null
            seriesRef.current = null
        }
    }, [])

    useEffect(() => {
        if (!seriesRef.current) return

        if (!priceHistory || priceHistory.length === 0) {
            seriesRef.current.setData([])
            return
        }

        const seen = new Set()
        const chartData = priceHistory
            .filter(d => {
                if (seen.has(d.date)) return false
                seen.add(d.date)
                return true
            })
            .map(d => ({
                time: d.date,
                open: d.open,
                high: d.high,
                low: d.low,
                close: d.close,
            }))
            .sort((a, b) => a.time.localeCompare(b.time))

        seriesRef.current.setData(chartData)

        if (date) {
            const dateExists = chartData.some(d => d.time === date)
            createSeriesMarkers(seriesRef.current, dateExists ? [{
                time: date,
                position: "aboveBar",
                color: "#111",
                shape: "circle",
                text: "selected",
            }] : [])
        }

        chartRef.current.timeScale().fitContent()

    }, [priceHistory, date])

    return (
        <div className="price-chart-card">
            <h3 className="price-chart-title">
                Price Chart {pair ? `· ${pair}` : ""}
            </h3>
            {!priceHistory && (
                <p style={{ fontSize: "13px", color: "#bbb", margin: "0 0 12px 0" }}>
                    Run a prediction to load chart data
                </p>
            )}
            <div ref={chartContainerRef} className="price-chart-container" />
        </div>
    )
}

export default PriceChart