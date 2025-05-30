import requests
from bs4 import BeautifulSoup
import re
import time
import pandas as pd
import sys
import argparse
import json


URL = "https://gateoverflow.in/tag-search-page"
GATE_HOST = "https://gateoverflow.in/"
RESULTS = []

def process_link(tag, i):
    return URL + f"?q={tag}%2B&start={10*i}"
    
def to_int(token: str) -> int:
    token = token.lower().replace(',', '').strip()
    match = re.fullmatch(r'(\d+(?:\.\d+)?)([km]?)', token)
    if not match:
        return 0
    num, suffix = match.groups()
    factor = dict(k=1_000, m=1_000_000).get(suffix, 1)
    return int(float(num) * factor)

def parse_card(card: BeautifulSoup) -> dict:
    try:
        votes = to_int(card.select_one("span.qa-netvote-count-data").text)
        views = to_int(card.select_one("div.qa-view-count span.item-view-text").text)
        user = card.select_one("span.qa-q-item-who-data a.qa-user-link").text.strip()
        title_elem = card.select_one("div.qa-q-item-title a")
        title = title_elem.text.strip()
        link = GATE_HOST + title_elem['href'].lstrip("./")
        asked_on_elem = card.select_one("span.qa-q-item-when-data")
        asked_on = asked_on_elem.text.strip() if asked_on_elem else "N/A"
        return {"title": str(title), "link": str(link), "upvotes": votes, "views": views, "user": user, "date": str(asked_on)}
    except Exception as e:
        return False
        
def addIn_csv(df, x):
    df.write(x["title"])
    df.write(",") 
    df.write(str(x["link"])) 
    df.write(",")
    df.write(str(x["votes"])) 
    df.write(",")
    df.write(str(x["views"])) 
    df.write(",")
    df.write(str(x["user"]))
    df.write(",")
    df.write(str(x["date"].replace(",", ""))) 
    df.write("\n")

def scrap_data(url):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    response = requests.get(url, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"Failed to load page {url}")
    
    soup = BeautifulSoup(response.content, "html.parser")
        
    #if search result are there
    header = soup.find("header", class_="qa-main-heading")
    if header:
        heading_text = header.get_text(strip=True).lower()        
        if heading_text.startswith("no results found for"):
            return False  # No results found    
    
    container = soup.select_one("div.qa-q-list.qa-q-list-vote-disabled")

    # Select all direct child divs (like qa-q-list-item)
    if container:
        children = container.find_all(recursive=False)  # Direct children
        for card in children:
            x = parse_card(card)
            if x:
                #print(x)
                RESULTS.append(x)
    return True
            

def runner(tag, i, size):
    if scrap_data(process_link(tag, i)) and i != size:
        runner(tag, i+1, size)
    return True

def ArgParser():
    parser = argparse.ArgumentParser(description='Data scraper')
    parser.add_argument('--tags', type=str, required=True, help='Tags to filter by')
    parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')

    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = ArgParser()
    runner(tag=args.tags, i=1, size = args.limit)
    with open(f"results.json", 'w') as fp:
        json.dump(RESULTS, fp)
    
