import { useEffect, useRef } from "react"
import {
    createChart,
    CandlestickSeries,
    createSeriesMarkers
} from "lightweight-charts"

function PriceChart({ date, pair, priceHistory }) {
    const chartShellRef = useRef(null)
    const chartContainerRef = useRef(null)
    const overlayRef = useRef(null)
    const verticalLineRef = useRef(null)

    const chartRef = useRef(null)
    const seriesRef = useRef(null)
    const markersRef = useRef(null)
    const selectedDateRef = useRef(null)

    function updateSelectedDateOverlay() {
        const chart = chartRef.current
        const shell = chartShellRef.current
        const overlay = overlayRef.current
        const verticalLine = verticalLineRef.current
        const selectedDate = selectedDateRef.current

        if (!chart || !shell || !overlay || !verticalLine || !selectedDate) {
            if (overlay) overlay.style.display = "none"
            if (verticalLine) verticalLine.style.display = "none"
            return
        }

        const x = chart.timeScale().timeToCoordinate(selectedDate)

        if (x === null || x === undefined) {
            overlay.style.display = "none"
            verticalLine.style.display = "none"
            return
        }

        const shellWidth = shell.clientWidth
        const clampedX = Math.max(0, Math.min(x, shellWidth))

        verticalLine.style.display = "block"
        verticalLine.style.left = `${clampedX}px`

        overlay.style.display = "block"
        overlay.style.left = `${clampedX}px`
        overlay.style.width = `${Math.max(0, shellWidth - clampedX)}px`
    }

    useEffect(() => {
        selectedDateRef.current = date
        requestAnimationFrame(updateSelectedDateOverlay)
    }, [date])

    useEffect(() => {
        if (!chartShellRef.current || !chartContainerRef.current) return

        const shell = chartShellRef.current
        const container = chartContainerRef.current

        const chart = createChart(container, {
            width: shell.clientWidth,
            height: shell.clientHeight || 340,

            layout: {
                background: { color: "#ffffff" },
                textColor: "#888"
            },

            grid: {
                vertLines: { color: "#f0f0f0" },
                horzLines: { color: "#f0f0f0" }
            },

            rightPriceScale: {
                borderColor: "#f0f0f0"
            },

            timeScale: {
                borderColor: "#f0f0f0",
                timeVisible: true
            }
        })

        const candleSeries = chart.addSeries(CandlestickSeries, {
            upColor: "#22c55e",
            downColor: "#ef4444",
            borderUpColor: "#22c55e",
            borderDownColor: "#ef4444",
            wickUpColor: "#22c55e",
            wickDownColor: "#ef4444"
        })

        chartRef.current = chart
        seriesRef.current = candleSeries
        markersRef.current = createSeriesMarkers(candleSeries, [])

        const resizeObserver = new ResizeObserver(entries => {
            const { width, height } = entries[0].contentRect

            chart.applyOptions({
                width,
                height
            })

            requestAnimationFrame(updateSelectedDateOverlay)
        })

        const handleVisibleRangeChange = () => {
            requestAnimationFrame(updateSelectedDateOverlay)
        }

        resizeObserver.observe(shell)
        chart.timeScale().subscribeVisibleTimeRangeChange(handleVisibleRangeChange)

        return () => {
            resizeObserver.disconnect()
            chart.timeScale().unsubscribeVisibleTimeRangeChange(handleVisibleRangeChange)

            chart.remove()

            chartRef.current = null
            seriesRef.current = null
            markersRef.current = null
        }
    }, [])

    useEffect(() => {
        if (!seriesRef.current || !markersRef.current) return

        if (!priceHistory || priceHistory.length === 0) {
            seriesRef.current.setData([])
            markersRef.current.setMarkers([])
            selectedDateRef.current = null
            updateSelectedDateOverlay()
            return
        }

        const seen = new Set()

        const chartData = priceHistory
            .filter(row => {
                if (seen.has(row.date)) return false

                seen.add(row.date)
                return true
            })
            .map(row => ({
                time: row.date,
                open: row.open,
                high: row.high,
                low: row.low,
                close: row.close
            }))
            .sort((a, b) => a.time.localeCompare(b.time))

        seriesRef.current.setData(chartData)

        const selectedDateExists = Boolean(date) && chartData.some(d => d.time === date)
        selectedDateRef.current = selectedDateExists ? date : null

        const markers = selectedDateExists
            ? [
                {
                    time: date,
                    position: "aboveBar",
                    color: "#111",
                    shape: "circle",
                    text: "selected"
                }
            ]
            : []

        markersRef.current.setMarkers(markers)
        chartRef.current?.timeScale().fitContent()

        requestAnimationFrame(updateSelectedDateOverlay)
    }, [priceHistory, date])

    return (
        <div className="price-chart-card">
            <h3 className="price-chart-title">
                Price Chart {pair ? `- ${pair}` : ""}
            </h3>

            {!priceHistory && (
                <p className="price-chart-empty-message">
                    Run a prediction to load chart data
                </p>
            )}

            <div ref={chartShellRef} className="price-chart-container">
                <div ref={chartContainerRef} className="price-chart-canvas" />
                <div ref={overlayRef} className="price-chart-future-mask" />
                <div ref={verticalLineRef} className="price-chart-selected-line" />
            </div>
        </div>
    )
}

export default PriceChart