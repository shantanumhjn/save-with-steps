from datetime import date, timedelta

def fetch_data(start_date: date, end_date: date):
    diff = end_date - start_date
    if diff.days < 0:
        return {"activities-steps": []}
    if diff.days == 0:
        return {"activities-steps": [{"dateTime": start_date.isoformat(), "value": "0"}]}

    step_data = [{"dateTime": (start_date + timedelta(days=i)).isoformat(), "value": "0"} for i in range(diff.days + 1)]
    return {"activities-steps": step_data}

if __name__ == "__main__":
    start_date = date(2023, 1, 2)
    end_date = date(2023, 1, 1)
    data = fetch_data(start_date, end_date)
    print(data)