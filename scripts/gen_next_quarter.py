import argparse
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
    parser = argparse.ArgumentParser("get_next_quarter")
    parser.add_argument("--target_date_int", nargs="?", help="Target quarter start date in integer format YYYYMMdd.", type=int)
    args = parser.parse_args()

    if args.target_date_int and args.target_date_int > 20240101 and args.target_date_int < 30240101:
        print(args.target_date_int)
    else:
        print(get_start_date_next_quarter())
