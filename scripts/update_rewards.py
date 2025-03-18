import argparse
import json
import os
import requests
import re
import sys
from bs4 import BeautifulSoup
from datetime import datetime, timedelta

DISCOVER_ID = 1
CHASE_FREEDOM_ID = 2
CHASE_FREEDOM_FLEX_ID = 3
CITI_ID = 4

class Worker:
    def get_citi_rewards(self, target_date_int: int) -> list[str]:
        resp = requests.get("https://www.citi.com/credit-cards/dividend-quarterly-offer")
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        date_div = soup.find("div", class_ = "dividend-quarterly-offer-content__offer__labels__signup-label")
        signup_date = datetime.strptime(date_div.span.contents[1].string, "%m/%d/%Y").date()
        next_q_date_int = self.get_next_quarter_start(signup_date)
        if next_q_date_int != target_date_int:
            return []
        divs = soup.find_all("div", class_ = "dividend-quarterly-offer-content__offer__labels__title")
        return [self.process_item(div.h3.contents[0]) for div in divs]

    def get_chase_rewards_bak(self, target_date_int: int) -> list[str]:
        resp = requests.get("https://www.chase.com/personal/credit-cards/freedom/freedomfive")
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        date_range = soup.find("span", class_ = "mds-body-large")
        match = re.search(r"From (\w+ \d{1,2}) - \w+ \d{1,2}, (\d{4})", date_range.contents[0])
        date_integer = 0
        if match:
            month_day = match.group(1)  # "October 1"
            year = match.group(2)       # "2024"
            date_object = datetime.strptime(f"{month_day}, {year}", "%B %d, %Y")
            date_integer = date_object.year * 10000 + date_object.month * 100 + date_object.day
        if date_integer == target_date_int:
            spans = soup.find_all("span", class_ = "cux-padding-24")
            return [self.process_item(span.contents[0]) for span in spans]
        return []
    
    def get_chase_rewards(self, target_date_int: int) -> list[str]:
        resp = requests.get("https://www.chasebonus.com/")
        if resp.status_code != 200:
            return []
        soup = BeautifulSoup(resp.text, 'html.parser')
        date_range = soup.find("div", class_ = "descText")
        match = re.search(r"from (\d{1,2})/(\d{1,2})/(\d{4}) - \d{1,2}/\d{1,2}/\d{4}", date_range.text)
        date_integer = 0
        if match:
            month, day, year = match.group(1), match.group(2), match.group(3)
            date_integer = int(year) * 10000 + int(month) * 100 + int(day)
        if date_integer == target_date_int:
            categories = []
            category_items = soup.find_all("div", class_ = "category-item")
            for item in category_items:
                h2_tag = item.find('h2')
                # Extract only the top-level text nodes
                top_level_text = ''.join(h2_tag.find_all(string=True, recursive=False)).strip()
                # Replace <br> and normalize spaces
                top_level_text = top_level_text.replace('\n', ' ').replace('<br>', ' ').strip()
                categories.append(top_level_text.title())
            return categories
        return []

    def get_discover_rewards(self, target_date_int: int) -> list[str]:
        resp = requests.get("https://card.discover.com/cardissuer/public/rewards/offer/v1/offer-categories")
        if resp.status_code != 200:
            return []
        obj = resp.json()
        for q in obj["quarters"]:
            date_object = datetime.strptime(q['quarterLabelStartDate'], "%B %d, %Y")
            date_integer = date_object.year * 10000 + date_object.month * 100 + date_object.day
            if date_integer == target_date_int:
                items = q['title'].replace(", and ", ",").replace(" and ", ",").split(",")
                return [self.process_item(item) for item in items if item.strip()]
        return []
    
    def process_item(self, item: str) -> str:
        if "Gas" in item and "Electric" in item:
            return "Gas & EV Charging"
        elif "Gas" in item:
            return "Gas Stations"
        else:
            return item.strip()
    
    def update_rewards(self, file_path: str, startDateInt: int, rewards: list[tuple[int, list[str]]]) -> bool:
        with open(file_path, 'r') as f:
            data = json.load(f)

        if data[-1]["startDateInt"] >= startDateInt:
            return False

        data = data[-3:]

        new_entry = {
            "startDateInt": startDateInt,
            "items": []
        }
        for (cardId, categories) in rewards:
            new_entry["items"].append({
                "cardId": cardId,
                "categories": categories
            })
        data.append(new_entry)

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=4)
        return True
        
    def get_next_quarter_start(self, today = datetime.today()) -> int:
        # today = datetime.today()
        current_quarter = (today.month - 1) // 3 + 1
        if current_quarter == 4:
            next_quarter_start_month = 1
            next_quarter_start_year = today.year + 1
        else:
            next_quarter_start_month = (current_quarter * 3) + 1
            next_quarter_start_year = today.year
        return next_quarter_start_year * 10000 + next_quarter_start_month * 100 + 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser("update_rewards")
    parser.add_argument("--target_date_int", nargs="?", help="Target quarter start date in integer format YYYYMMdd.", type=int)
    args = parser.parse_args()

    worker = Worker()
    if args.target_date_int and args.target_date_int > 20240101 and args.target_date_int < 30240101:
        target_date_int = args.target_date_int
    else:
        target_date_int = worker.get_next_quarter_start()

    citi = worker.get_citi_rewards(target_date_int)
    chase = worker.get_chase_rewards(target_date_int)
    discover = worker.get_discover_rewards(target_date_int)

    if citi and chase and discover:
        rewards = [
            (DISCOVER_ID, discover),
            (CHASE_FREEDOM_ID, chase),
            (CHASE_FREEDOM_FLEX_ID, chase),
            (CITI_ID, citi)
        ]
        path = os.path.dirname(os.path.realpath(__file__))
        updated = worker.update_rewards(os.path.join(path, "../api/rewards.json"), target_date_int, rewards)
        if updated:
            print("updated rewards for", target_date_int)
        else:
            print("reward info has already been updated for", target_date_int)
    else:
        print("no rewards to update for", target_date_int)
