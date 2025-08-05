from bs4 import BeautifulSoup
import re
import csv
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import sender

URL = "https://www.ycombinator.com/companies"

def fetch_html(url):
    options = Options()
    options.add_argument("--headless")
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, timeout=10)

    facets = wait.until(EC.presence_of_all_elements_located(
        (By.CLASS_NAME, "_facet_i9oky_85")
    ))

    batch_facet = None
    for f in facets:
        try:
            header = f.find_element(By.TAG_NAME, "h4")
            if header.text.strip() == "Batch":
                batch_facet = f
                break
        except:
            continue

    if not batch_facet:
        raise RuntimeError("Could not find the 'Batch' facet block")

    for label in batch_facet.find_elements(By.TAG_NAME, "label"):
        checkbox = label.find_element(By.TAG_NAME, "input")
        if not checkbox.is_selected():
            label.click()
            break

    wait.until(EC.url_contains("batch="))
    time.sleep(1)

    last_height = driver.execute_script("return document.body.scrollHeight")
    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            break
        last_height = new_height

    rendered_html = driver.page_source
    driver.quit()
    return rendered_html

def parse_companies(html):
    soup = BeautifulSoup(html, "html.parser")
    rows = []

    for card in soup.find_all("a", class_=re.compile(r"_company_")):
        name = card.find("span", class_=re.compile(r"^_coName_")).get_text(strip=True)
        href = "https://www.ycombinator.com" + card['href']
        desc_div = card.find("div", class_="mb-1.5 text-sm")

        if desc_div:
            span = desc_div.find("span")
            tagline = span.get_text(strip=True) if span else ""
        else:
            tagline = ""
        rows.append({"company": name, "tagline": tagline, "url": href})

    return rows

def save_to_csv(data, filename="companies.csv"):
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["company", "tagline", "url"])
        writer.writeheader()
        writer.writerows(data)

def load_existing(filename="companies.csv"):
    seen = set()
    with open(filename, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            seen.add(row["company"])
    return seen

def detect_new_rows(fresh_rows, existing_set):
    return [row for row in fresh_rows if row["company"] not in existing_set]

def main():
    existing_set = load_existing()

    html      = fetch_html(URL)
    companies = parse_companies(html)
    save_to_csv(companies)
    print(f"Saved {len(companies)} companies to companies.csv")

    new_rows = detect_new_rows(companies, existing_set)
    
    if new_rows:
        print(f"Found {len(new_rows)} new companies:")
        for row in new_rows:
            print(f"{row['company']}: {row['tagline']}")
            
        sender.send_email(
            subject="Y Combinator Updates",
            body=f"Found {len(new_rows)} new companies:\n" + "\n".join(
                f"{row['company']}: {row['tagline']}" for row in new_rows
            ),
            html_body = '<h2>Found {count} new companies:</h2>'.format(count=len(new_rows)) + '<ul>' + ''.join(
                f"<li><a href=\"{row['url']}\">{row['company']}</a>: {row['tagline']}</li>" for row in new_rows
            ) + '</ul>'
        )
    else:
        print("No new companies found.")

if __name__ == "__main__":
    main()
