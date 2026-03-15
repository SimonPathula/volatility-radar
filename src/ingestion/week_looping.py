from datetime import datetime, timedelta

def weeks_from_then_tonow(year, month, date):
    start_date = datetime(year, month, date)
    end_date = datetime.today()

    while start_date <= end_date:
        print(start_date.strftime("%b%#d.%Y").lower())
        start_date += timedelta(days= 7)
