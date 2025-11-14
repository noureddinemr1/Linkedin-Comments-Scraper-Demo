import os
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from dotenv import load_dotenv
import requests
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.keys import Keys
import json
import re
import csv
import urljoin

def clean_comment_text(text):
    if not text:
        return ""
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002700-\U000027BF"  # dingbats
        "\U0001f926-\U0001f937"  # gestures
        "\U00010000-\U0010ffff"  # other unicode
        "\u2640-\u2642"  # gender symbols
        "\u2600-\u2B55"  # misc symbols
        "\u200d"  # zero width joiner
        "\u23cf"  # eject symbol
        "\u23e9"  # fast forward
        "\u231a"  # watch
        "\ufe0f"  # variation selector
        "\u3030"  # wavy dash
        "]+",
        flags=re.UNICODE
    )
    text = emoji_pattern.sub('', text)
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)

    return text

load_dotenv()
auto_select_policy = [{"pattern": "https://www.linkedin.com","filter": {"SUBJECT": {"CN": "PRONTOGOV PRODUTOS E SERVICOS LTDA:23090165000105"}}}]

profile_path = os.path.join(os.getcwd(), "chrome_profile")
profile_url = os.getenv('LINKEDIN_PROFILE_URL')
email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')
max_comments = os.getenv('MAX_POSTS')
max_scroll = os.getenv('MAX_SCROLLS', 20)

profile_exists = os.path.exists(profile_path) and os.listdir(profile_path)

if not os.path.exists('ext.crx'):
    print("📥 Downloading NopeCha extension...")
    with open('ext.crx', 'wb') as f:
        f.write(requests.get('https://nopecha.com/f/ext.crx').content)
    print("✅ Extension downloaded")
else:
    print("✅ NopeCha extension already exists")


options = webdriver.ChromeOptions()

options.add_argument("--disable-plugins")
options.add_argument(f"--user-data-dir={profile_path}")
options.add_argument("--ignore-certificate-errors")
options.add_argument("--start-maximized")
options.add_argument('--no-sandbox')
options.add_argument('--disable-infobars')
options.add_argument('--disable-dev-shm-usage')
options.add_argument('--disable-blink-features=AutomationControlled')
options.add_experimental_option('excludeSwitches', ['enable-automation'])
options.add_experimental_option('useAutomationExtension', False)
options.add_experimental_option('prefs', {
    'intl.accept_languages': 'en,en_US',
    'AutoSelectCertificateForUrls': auto_select_policy
})
options.add_extension('ext.crx')


print("Starting Chrome browser...")
try:
    driver = webdriver.Chrome(options=options)
    print("✅ Chrome browser started successfully")
except Exception as e:
    print(f"Failed to start Chrome: {e}")
    print("1. Make sure Chrome is installed")
    print("2. Make sure chromedriver.exe is in your PATH or in the same directory")
    print("3. Download chromedriver from: https://chromedriver.chromium.org/downloads")
    exit(1)

try:
    driver.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
    print("✅ Certificate errors will be ignored")
except Exception as e:
    print(f"CDP command failed: {e}")


try:
    print("Starting scraper")
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

    if driver.find_elements(By.ID, "username") or driver.find_elements(By.ID, "session_key"):
        print("Not logged in, logging in...")
        try:
            email_field = None
            try:
                email_field = driver.find_element(By.ID, "username")
            except:
                email_field = driver.find_element(By.ID, "session_key")
            current_value = email_field.get_attribute("value")
            if current_value:
                print(f"Clearing cached email: {current_value}")  
                email_field.send_keys(Keys.CONTROL + "a")
                email_field.send_keys(Keys.DELETE)
                time.sleep(0.3) 
            email_field.send_keys(email)
            print(f"Email entered: {email_field.get_attribute('value')}")

            time.sleep(1)
            
            password_field = None
            try:
                password_field = driver.find_element(By.ID, "password")
            except:
                password_field = driver.find_element(By.ID, "session_password")
            current_value = password_field.get_attribute("value")
            if current_value:
                print("Clearing cached password")
                password_field.send_keys(Keys.CONTROL + "a")
                password_field.send_keys(Keys.DELETE)
                time.sleep(0.3)

            password_field.send_keys(password)
            print("Password entered")          
            time.sleep(5)
            
            login_button = driver.find_element(By.XPATH, "//button[@type='submit' and (contains(text(), 'Sign in') or contains(text(), \"S'identifier\"))]")
            login_button.click()
            print("Login button clicked")

            WebDriverWait(driver, 50).until(EC.url_contains("feed"))
            print("Logged in successfully")
        except Exception as e:
            print(f"Login failed: {e}")
            driver.quit()
            exit()
    else:
        print("Already logged in")

    time.sleep(5)
    comments_url = urljoin(profile_url,"recent-activity/comments/")
    print("Going to :",comments_url)
    driver.get(comments_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("At profile")

    time.sleep(2)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("At comments activity page")
    comments = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    scroll_count = 0
    while len(comments) < max_comments and scroll_count < max_scroll:  
        print(f"Scroll {scroll_count + 1}")

        comment_containers = driver.find_elements(By.XPATH,
            "//div[contains(@class, 'comments-comment-item')] | "
            "//div[contains(@class, 'comment-item')] | "
            "//article[contains(@class, 'comment')] | "
            "//div[contains(@class, 'feed-shared-comment-item')]"
        )
        print(f"Found {len(comment_containers)} comment containers")

        for container in comment_containers:
            if len(comments) >= max_comments:
                break
            try:
                comment_data = {}
                author_selectors = [
                    ".//span[contains(@class, 'comments-comment-meta__name')]",
                    ".//a[contains(@class, 'comments-comment-meta__name')]",
                    ".//span[contains(@class, 'comment-author-text')]",
                    ".//a[contains(@class, 'comment-author-text')]",
                    ".//span[contains(@class, 'feed-shared-actor__name')]",
                    ".//a[contains(@class, 'feed-shared-actor__name')]",
                    ".//span[contains(@class, 'actor-name')]",
                    ".//a[contains(@class, 'actor-name')]",
                    ".//div[contains(@class, 'comments-comment-meta')]//span[1]",
                    ".//div[contains(@class, 'comments-comment-meta')]//a[1]"
                ]

                author_name = ""
                for selector in author_selectors:
                    try:
                        author_elem = container.find_element(By.XPATH, selector)
                        author_name = author_elem.text.strip()
                        if author_name and len(author_name) > 1:
                            break
                    except:
                        continue

                time_selectors = [
                    ".//time", 
                    ".//span[contains(@class, 'time')]",
                    ".//span[contains(@class, 'timestamp')]",
                    ".//span[contains(@class, 'feed-shared-actor__sub-description')]"
                ]

                timestamp = ""
                for selector in time_selectors:
                    try:
                        time_elem = container.find_element(By.XPATH, selector)
                        datetime_attr = time_elem.get_attribute("datetime")
                        if datetime_attr:
                            timestamp = datetime_attr
                            print(f"Found datetime attribute: {datetime_attr}")
                            break
                        text_content = time_elem.text.strip()
                        if text_content:timestamp = text_content
                    except:
                        continue

                if not timestamp:
                    try:
                        datetime_elem = container.find_element(By.XPATH, ".//*[@datetime]")
                        timestamp = datetime_elem.get_attribute("datetime")
                        print(f"Found datetime attribute in any element: {timestamp}")
                    except:
                        print("No timestamp found for this comment")
                        pass

                text_selectors = [
                    ".//span[contains(@class, 'comment-text')]",
                    ".//span[contains(@class, 'break-words')]",
                    ".//div[contains(@class, 'feed-shared-update-v2__commentary')]//span[@dir='ltr']",
                    ".//div[contains(@class, 'update-components-text')]//span",
                    ".//div[contains(@class, 'comment-item__content')]//span",
                    ".//div[contains(@class, 'feed-shared-comment-item__content')]//span"
                ]

                comment_text = ""
                for selector in text_selectors:
                    try:
                        text_elem = container.find_element(By.XPATH, selector)
                        comment_text = text_elem.text.strip()
                        if comment_text:
                            break
                    except:
                        continue

                cleaned_text = clean_comment_text(comment_text)

                if cleaned_text and len(cleaned_text) > 1:  
                    comment_data = {
                        "author": author_name,
                        "timestamp": timestamp,
                        "original_text": comment_text,
                        "cleaned_text": cleaned_text,
                        "text_length": len(cleaned_text),
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    if not any(c["cleaned_text"] == cleaned_text for c in comments):
                        comments.append(comment_data)
                        print(f"Collected comment {len(comments)}: {cleaned_text[:50]}...")

            except Exception as e:
                print(f"Error processing comment container: {e}")
                continue

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("No more content to load")
            break
        last_height = new_height
        scroll_count += 1

    print(f"Total comments collected: {len(comments)}")

    output_file = "linkedin_comments.csv"
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        fieldnames = [
            'author',
            'timestamp',
            'original_text',
            'cleaned_text',
            'text_length',
            'scraped_at',
            'profile_url',
            'max_comments_requested',
            'comments_collected',
            'session_scraped_at'
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()

        for comment in comments:
            comment_row = comment.copy()
            comment_row['profile_url'] = profile_url
            comment_row['max_comments_requested'] = max_comments
            comment_row['comments_collected'] = len(comments)
            comment_row['session_scraped_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(comment_row)

    print(f"Comments saved to {output_file}")

    for i, comment in enumerate(comments[:max_comments], 1):
        print(f"{i}. [{comment['author']}] {comment['cleaned_text']}")

finally:
    driver.quit()