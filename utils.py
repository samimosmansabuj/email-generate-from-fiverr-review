from dotenv import load_dotenv
import pandas as pd
from datetime import datetime
load_dotenv()
import os

def load_url_csv_file(csv_file):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=["freelancer_username", "url", "scrapping_date"])
        df.to_csv(csv_file, index=False)
    return df

def check_url_and_profile(url_link, freelancer_username):
    load_url_csv = load_url_csv_file(os.environ.get("url_list_csv"))
    shortlist = load_url_csv.loc[load_url_csv["freelancer_username"] == freelancer_username]
    if url_link in shortlist["url"].str.strip().values:
        load_url_csv
        return True
    else:
        return False

def update_url_csv(url_link, freelancer_username):
    path = os.environ.get("url_list_csv")
    load_url_csv = load_url_csv_file(os.environ.get("url_list_csv"))
    time = datetime.now().date()
    try:
        load_url_csv.loc[len(load_url_csv)] = [
            freelancer_username,
            url_link,
            time
        ]
    except Exception as e:
        print("Get issues add new row!: ", str(e))
    
    load_url_csv.to_csv(path, index=False, encoding="utf-8-sig")
    
    

