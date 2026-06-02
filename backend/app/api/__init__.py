from fastapi import APIrouter

router = APIrouter()

@router.get("/pairs")
def get_paris():
    return [
        "EURUSD",
        "GBPUSD",
        "USDJPY"
    ]