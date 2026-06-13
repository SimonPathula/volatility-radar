function ExplainButton({ onClick, loading }) {
    return (
        <button
            className="explain-btn"
            onClick={onClick}
            disabled={loading}
        >
            {loading ? "Explaining..." : "✦ Explain Prediction"}
        </button>
    )
}

export default ExplainButton