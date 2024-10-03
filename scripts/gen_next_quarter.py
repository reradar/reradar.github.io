from datetime import datetime

def get_start_date_next_quarter():
    today = datetime.today()
    current_quarter = (today.month - 1) // 3 + 1
    if current_quarter == 4:
        next_quarter_start_month = 1
        next_quarter_start_year = today.year + 1
    else:
        next_quarter_start_month = (current_quarter * 3) + 1
        next_quarter_start_year = today.year
    return next_quarter_start_year * 10000 + next_quarter_start_month * 100 + 1

if __name__ == "__main__":
    print(get_start_date_next_quarter())
