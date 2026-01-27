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
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import sender

URL = "https://www.ycombinator.com/companies"

def fetch_html(url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(url)
    driver.implicitly_wait(10)
    wait = WebDriverWait(driver, timeout=10)

    facets = wait.until(EC.presence_of_all_elements_located(
        (By.CLASS_NAME, "_facet_zhfs4_85")
    ))

    time.sleep(10)

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
    
    pages = []

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

    pages.append(driver.page_source)

    for label in batch_facet.find_elements(By.TAG_NAME, "label"):
        checkbox = label.find_element(By.TAG_NAME, "input")
        if not checkbox.is_selected():
            label.click()
            break

    time.sleep(1)

    unselected_count = 0

    for label in batch_facet.find_elements(By.TAG_NAME, "label"):
        checkbox = label.find_element(By.TAG_NAME, "input")
        if not checkbox.is_selected():
            unselected_count += 1
            if unselected_count == 2:
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

    pages.append(driver.page_source)

    driver.quit()
    return pages

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

def get_founder_info(company_url):
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--disable-gpu')
    options.add_argument('--window-size=1920,1080')

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    driver.get(company_url)
    time.sleep(2)

    founder_cards = WebDriverWait(driver, 10).until(
        EC.presence_of_all_elements_located(
            (By.CSS_SELECTOR, ".ycdc-card-new")
        )
    )

    print(f"Found {len(founder_cards)} founder cards")

    founders_data = []

    for i, card in enumerate(founder_cards):
            try:
                founder_info = {
                    'name': '',
                    'title': '',
                    'description': '',
                    'social_links': []
                }
                
                try:
                    name_element = card.find_element(By.CSS_SELECTOR, ".text-xl.font-bold")
                    founder_info['name'] = name_element.text.strip()
                except NoSuchElementException:
                    print(f"Could not find name for card {i+1}")
                
                try:
                    title_element = card.find_element(By.CSS_SELECTOR, ".text-gray-600")
                    founder_info['title'] = title_element.text.strip()
                except NoSuchElementException:
                    print(f"Could not find title for card {i+1}")
                
                try:
                    desc_element = card.find_element(By.CSS_SELECTOR, ".prose.max-w-full.whitespace-pre-line")
                    founder_info['description'] = desc_element.text.strip()
                except NoSuchElementException:
                    print(f"Could not find description for card {i+1}")
                
                try:
                    social_container = card.find_element(By.CSS_SELECTOR, ".mt-2.flex.gap-2")
                    social_links = social_container.find_elements(By.TAG_NAME, "a")
                    
                    for link in social_links:
                        try:
                            href = link.get_attribute('href')
                            aria_label = link.get_attribute('aria-label')
                            tooltip_content = link.get_attribute('data-tooltip-content')
                            
                            platform = 'unknown'
                            if 'linkedin.com' in href.lower():
                                platform = 'LinkedIn'
                            elif 'twitter.com' in href.lower() or 'x.com' in href.lower():
                                platform = 'Twitter/X'
                            elif 'github.com' in href.lower():
                                platform = 'GitHub'
                            elif 'instagram.com' in href.lower():
                                platform = 'Instagram'
                            elif tooltip_content:
                                platform = tooltip_content
                            elif aria_label:
                                platform = aria_label.replace(' profile', '')
                            
                            founder_info['social_links'].append({
                                'platform': platform,
                                'url': href
                            })
                        except Exception as e:
                            print(f"Error extracting link info: {e}")
                            
                except NoSuchElementException:
                    print(f"No social links found for card {i+1}")
                
                if founder_info['name'] and founder_info['title']: 
                    founders_data.append(founder_info)
                    print(f"Extracted: {founder_info['name']} - {founder_info['title']}")
                
            except Exception as e:
                print(f"Error processing founder card {i+1}: {e}")
                continue
            except TimeoutException:
                print("Timeout waiting for founder cards to load")
            except Exception as e:
                print(f"Error finding founder cards: {e}")
    
    return founders_data   

def format_founder_info_text(founder_data):
    if not founder_data:
        return "No founder information available"
    
    founder_lines = []
    for founder in founder_data:
        name_title = f"{founder['name']}"
        if founder['title']:
            name_title += f" ({founder['title']})"
        
        founder_lines.append(name_title)

        social_links = []
        for link in founder['social_links']:
            social_links.append(f"{link['platform']}: {link['url']}")
        
        if social_links:
            founder_lines.append("  Links: " + ", ".join(social_links))
    
    return "\n".join(founder_lines)

def format_founder_info_html(founder_data):
    if not founder_data:
        return "<p><em>No founder information available</em></p>"
    
    html_parts = []
    html_parts.append("<ul class='founders-list'>")
    
    for founder in founder_data:
        html_parts.append("<li>")

        name_html = f"<strong>{founder['name']}</strong>"
        if founder['title']:
            name_html += f" <em>({founder['title']})</em>"
        html_parts.append(name_html)
        
        if founder.get('description'):
            desc = founder['description']
            html_parts.append(f"<br><small>{desc}</small>")
        
        if founder['social_links']:
            links_html = []
            for link in founder['social_links']:
                links_html.append(f"<a href='{link['url']}' target='_blank'>{link['platform']}</a>")
            
            html_parts.append(f"<br>Links: {' | '.join(links_html)}")
        
        html_parts.append("</li>")
    
    html_parts.append("</ul>")
    return "".join(html_parts)

def create_detailed_company_summary(new_rows, founders_data):
    summary_lines = []
    
    for row in new_rows:
        company_name = row['company']
        summary_lines.append(f"\n--- {company_name} ---")
        summary_lines.append(f"Tagline: {row['tagline']}")
        summary_lines.append(f"URL: {row['url']}")
        
        company_founders = None
        for founder_entry in founders_data:
            if founder_entry['company'] == company_name:
                company_founders = founder_entry['founders']
                break
        
        summary_lines.append("Founders:")
        if company_founders:
            founder_text = format_founder_info_text(company_founders)
            summary_lines.append(founder_text)
        else:
            summary_lines.append("  No founder information available")
        
        summary_lines.append("") 
    
    return "\n".join(summary_lines)

def create_detailed_html_summary(new_rows, founders_data):
    html_parts = []
    html_parts.append("""
    <style>
        .company-card {
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 15px;
            margin-bottom: 20px;
            background-color: #f9f9f9;
        }
        .company-title {
            color: #2c5282;
            margin-bottom: 10px;
        }
        .company-tagline {
            font-style: italic;
            color: #4a5568;
            margin-bottom: 10px;
        }
        .founders-section {
            margin-top: 15px;
        }
        .founders-list {
            margin: 10px 0;
            padding-left: 20px;
        }
        .founders-list li {
            margin-bottom: 10px;
        }
        .founders-list a {
            color: #3182ce;
            text-decoration: none;
        }
        .founders-list a:hover {
            text-decoration: underline;
        }
    </style>
    """)
    
    html_parts.append(f"<h3>Found {len(new_rows)} new companies:</h3>")
    
    for row in new_rows:
        company_name = row['company']
        html_parts.append('<div class="company-card">')
        html_parts.append(f'<h3 class="company-title"><a href="{row["url"]}" target="_blank">{company_name}</a> - <span class="tagline-inline">{row["tagline"]}</span></h3>')
        
        company_founders = None
        for founder_entry in founders_data:
            if founder_entry['company'] == company_name:
                company_founders = founder_entry['founders']
                break
        
        html_parts.append('<div class="founders-section">')
        founder_html = format_founder_info_html(company_founders)
        html_parts.append(founder_html)
        html_parts.append('</div>')
        
        html_parts.append('</div>')
    
    return "".join(html_parts)

def main():
    existing_set = load_existing()

    html      = fetch_html(URL)

    all_companies = []
    for page in html:
        companies = parse_companies(page)
        all_companies.extend(companies)

    save_to_csv(all_companies)
    print(f"Saved {len(all_companies)} companies to companies.csv")

    new_rows = detect_new_rows(all_companies, existing_set)

    founders_data = []
    
    if new_rows:
        print(f"Found {len(new_rows)} new companies:")
        for row in new_rows:
            print(f"{row['company']}: {row['tagline']}")
            founder_data = get_founder_info(row['url'])
            if founder_data:
                founders_data.append({
                    'company': row['company'],
                    'founders': founder_data
                })
                print("Founders:")
                
            for founder in founder_data:
                name_title = f"  • {founder['name']}"
                if founder['title']:
                    name_title += f" ({founder['title']})"
                print(name_title)
                
                if founder['social_links']:
                    links = [f"{link['platform']}: {link['url']}" for link in founder['social_links']]
                    print(f"    Links: {', '.join(links)}")
        else:
            print("  No founder information found")
            
        text_summary = create_detailed_company_summary(new_rows, founders_data)
        html_summary = create_detailed_html_summary(new_rows, founders_data)
        
        sender.send_email(
            subject=f"Y Combinator Updates - {len(new_rows)} New Companies Found",
            body=f"Found {len(new_rows)} new companies with founder information:\n\n{text_summary}",
            html_body=html_summary
        )
        
        print(f"\nCollected founder data for {len(founders_data)} companies")
    else:
        print("No new companies found.")

if __name__ == "__main__":
    main()
