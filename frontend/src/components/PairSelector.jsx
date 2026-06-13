function PairSelector({ pair, setPair }) {
    return (
        <div className="control-group">
            <select
                className="control-select"
                value={pair}
                onChange={(e) => setPair(e.target.value)}
            >
                <option value="EURUSD">EURUSD</option>
                <option value="GBPUSD">GBPUSD</option>
                <option value="USDJPY">USDJPY</option>
            </select>
        </div>
    )
}

export default PairSelector