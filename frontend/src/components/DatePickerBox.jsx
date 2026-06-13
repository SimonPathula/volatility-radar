function DatePickerBox({ date, setDate }) {
    return (
        <div className="control-group">
            <input
                className="control-date"
                type="date"
                value={date}
                onChange={(e) => setDate(e.target.value)}
            />
        </div>
    )
}

export default DatePickerBox