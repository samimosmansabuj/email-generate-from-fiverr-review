from bs4 import BeautifulSoup
from email_validation import EmailGenerate
from dotenv import load_dotenv
import time
import pandas as pd

load_dotenv()
import os


def load_csv_file(csv_file):
    if os.path.exists(csv_file):
        df = pd.read_csv(csv_file)
    else:
        df = pd.DataFrame(columns=["username", "email", "repeated", "country", "price_tag", "proficiency", "time_text", "count", "category", "review_description"])
        df.to_csv(csv_file, index=False)
    return df

def scrapping_all_reviews(html, type=None):
    soup = BeautifulSoup(html, "html.parser")
    if type and type.lower() == "profile":
        all_reviews = soup.find_all("span", class_="freelancer-review-item-wrapper")
    else:
        all_reviews = soup.find_all("li", class_="review-item-component")

    total_reviews = len(all_reviews)
    print("Total reviews found:", total_reviews)
    return all_reviews

def safe_get_text(parent, tag, class_name=None):
    if parent:
        element = parent.find(tag, class_=class_name) if class_name else parent.find(tag)
        if element:
            return element.get_text(strip=True)
    return "N/A"

def get_review_data(review, type=None) -> dict:
    data = {}
    if type and type.lower() == "profile":
        data["username"] = safe_get_text(review, "p", "l6pj4a1eb")
        data["repeated"] = safe_get_text(review.find("div", class_="l6pj4a11o"), "p")
        data["country"] = safe_get_text(review.find("div", class_="country"), "p")
        data["time_text"] = safe_get_text(review, "time")
        data["review_description"] = safe_get_text(review.find("div", class_="reliable-review-description review-description"), "p")
        price_tag = review.find("p", string=lambda text: text and "US$" in text)
        data["price_tag"] = price_tag.get_text(strip=True) if price_tag else "N/A"
    else:
        data["username"] = safe_get_text(review, "p", "_66nk381cr")
        data["repeated"] = safe_get_text(review.find("div", class_="_66nk38109"), "p")
        data["country"] = safe_get_text(review.find("div", class_="country"), "p")
        data["time_text"] = safe_get_text(review, "time")
        data["review_description"] = safe_get_text(review.find("div", class_="reliable-review-description review-description"), "p")
        price_tag = review.find("p", string=lambda text: text and "US$" in text)
        data["price_tag"] = price_tag.get_text(strip=True) if price_tag else "N/A"
    
    return data

def check_username_for_exist(username, load_df) -> bool:
    try:
        if username in load_df["username"].str.strip().values:
            load_df.loc[load_df["username"] == username, "count"] += 1
            return True
        else:
            return False
    except:
        return False

def get_generate_email(username: str):
    email = f"{username}@gmail.com"
    email_validation = EmailGenerate(email)
    status, msg = email_validation.full_email_check()
    if status:
        print(msg)
        return email
    else:
        print(msg)
        return None

def get_price_proficiency(price_str):
    price_str = price_str.replace(",", "")
    
    print(price_str)
    
    if "Up to" in price_str:
        price = float(price_str.split("US$")[1])
    elif "and above" in price_str:
        price = float(price_str.split("US$")[1].split()[0])
    else:
        price = float(price_str.split("US$")[1].split("-")[0])

    # mapping
    if price <= 50:
        return "Very Low"
    elif price <= 200:
        return "Low"
    elif price <= 600:
        return "Medium"
    elif price <= 1000:
        return "High"
    elif price <= 2000:
        return "Very High"
    elif price <= 4000:
        return "Important"
    else:
        return "Most Important"

def data_saved(data: dict, load_df, success_count: int, failed_count: int):
    category = os.environ.get("category")
    try:
        load_df.loc[len(load_df)] = [
            data["username"],
            data["email"],
            data["repeated"],
            data["country"],
            data["price_tag"],
            get_price_proficiency(data["price_tag"]) if data["price_tag"] != "N/A" else "Medium",
            data["time_text"],
            0,
            category,
            data["review_description"],
        ]
        success_count += 1
    except Exception as e:
        print("Get issues add new row!: ", str(e))
        failed_count += 1
    
    return success_count, failed_count

def has_email(data):
    return "email" in data and bool(data["email"])

def main(html, csv_file):
    load_df = load_csv_file(csv_file)
    review_type = os.environ.get("review_type", None)

    success_count = 0
    not_found_count = 0
    duplicated_count = 0
    failed_count = 0
    
    reviews = scrapping_all_reviews(html, review_type)

    for i, review in enumerate(reviews, start=1):
        data = get_review_data(review, review_type)
        # data = get_review_data(review)
        print(f"---------- Start For Review #{i}: {data["username"]}----------")
                
        # CSV/Data Frame------------------------------------------------------
        username_check = check_username_for_exist(data["username"], load_df)
        if username_check:
            print("❌ username already Exist!")
            duplicated_count += 1
        else:
            # Email Generate & Check Email Valid or Not-----------------------
            generate_email = get_generate_email(data["username"])
            if generate_email is None:
                print("❌ Get not Email by This username!")
                not_found_count += 1 
            else:
                data["email"] = generate_email
                # Data Save-----------------------------------------------------------
                if has_email(data):
                    success_count, failed_count = data_saved(data, load_df, success_count, failed_count)
                else:
                    not_found_count += 1 
        
        print(f"---------- End For Review #{i}: {data["username"]}----------")
        print("=============================================================")
        time.sleep(2)
        
        # if i > 1:
        #     break
  
    # ============End For Loop==============
    
    # CSV/Excel File Saved-------------
    load_df.to_csv(csv_file, index=False, encoding="utf-8-sig")
    
    return {
        "success_count": success_count,
        "not_found_count": not_found_count,
        "duplicated_count": duplicated_count,
        "failed_count": failed_count,
    }



if __name__ == "__main__":
    html_path = os.environ.get("html_template")
    csv_file = os.environ.get("csv_file")
    
    if not html_path or not csv_file:
        raise SystemExit("Missing one or more env vars: html_template, csv_file, category")

    with open(html_path, "rb") as f:
        html_bytes = f.read()
    html = html_bytes
    response = main(html, csv_file)
    
    print("✅ Data saved to", csv_file)
    print("✅ Successfull: ", response["success_count"])
    print("✅ Not Found Email: ", response["not_found_count"])
    print("✅ Duplicated: ", response["duplicated_count"])
    print("✅ Failed: ", response["failed_count"])




