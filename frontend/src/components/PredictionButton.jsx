function PredictionButton({ handlePrediction, loading }) {
    return (
        <button 
            className="predict-btn" 
            onClick={handlePrediction}
            disabled={loading}
        >
            {loading ? "Predicting..." : "Predict"}
        </button>
    )
}

export default PredictionButton