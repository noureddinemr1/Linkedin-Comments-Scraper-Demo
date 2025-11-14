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

def clean_comment_text(text):
    """Clean comment text: remove emojis, special chars, keep only letters and numbers, convert to lowercase"""
    if not text:
        return ""

    # Remove emojis and special unicode characters
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

    # Remove emojis
    text = emoji_pattern.sub('', text)

    # Keep only letters and numbers, remove all other characters
    text = re.sub(r'[^a-zA-Z0-9\s]', '', text)

    # Convert to lowercase and normalize whitespace
    text = text.lower().strip()

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text)

    return text

load_dotenv()
auto_select_policy = [
    {
        "pattern": "https://www.linkedin.com",
        "filter": {
            "SUBJECT": {"CN": "PRONTOGOV PRODUTOS E SERVICOS LTDA:23090165000105"}
        }
    }
]

profile_path = os.path.join(os.getcwd(), "chrome_profile")
profile_url = os.getenv('LINKEDIN_PROFILE_URL')
email = os.getenv('LINKEDIN_EMAIL')
password = os.getenv('LINKEDIN_PASSWORD')
max_comments = 10

# Check if profile exists, if not we'll need to set up extensions
profile_exists = os.path.exists(profile_path) and os.listdir(profile_path)

# Always ensure extension file exists
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

# Always load the extension (it will auto-install on first run or after profile clear)
print("🔧 Loading NopeCha extension...")
options.add_extension('ext.crx')

if not profile_exists:
    print("ℹ️ New profile detected - extension will be installed automatically")

print("Starting Chrome browser...")
try:
    driver = webdriver.Chrome(options=options)
    print("✅ Chrome browser started successfully")
except Exception as e:
    print(f"❌ Failed to start Chrome: {e}")
    print("\nTroubleshooting:")
    print("1. Make sure Chrome is installed")
    print("2. Make sure chromedriver.exe is in your PATH or in the same directory")
    print("3. Download chromedriver from: https://chromedriver.chromium.org/downloads")
    exit(1)

try:
    driver.execute_cdp_cmd('Security.setIgnoreCertificateErrors', {'ignore': True})
    print("✅ Certificate errors will be ignored")
except Exception as e:
    print(f"⚠️ CDP command failed: {e}")


try:
    print("Starting scraper")
    driver.get("https://www.linkedin.com/login")
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("At LinkedIn home")

    if driver.find_elements(By.ID, "username") or driver.find_elements(By.ID, "session_key"):
        print("Not logged in, logging in...")
        try:
            # Find email field (try both possible IDs)
            email_field = None
            try:
                email_field = driver.find_element(By.ID, "username")
            except:
                email_field = driver.find_element(By.ID, "session_key")
            
            # FORCE clear the field using multiple methods
            current_value = email_field.get_attribute("value")
            if current_value:
                print(f"Clearing cached email: {current_value}")
            
            # Method 1: Clear with Selenium
            email_field.clear()
            time.sleep(0.3)
            
            # Method 2: Select all and delete with keyboard
            email_field.send_keys(Keys.CONTROL + "a")
            email_field.send_keys(Keys.DELETE)
            time.sleep(0.3)
            
            # Method 3: Force with JavaScript
            driver.execute_script("arguments[0].value = '';", email_field)
            time.sleep(0.3)
            
            # Now enter the email
            email_field.send_keys(email)
            print(f"Email entered: {email_field.get_attribute('value')}")

            time.sleep(1)
            
            # Find password field (try both possible IDs)
            password_field = None
            try:
                password_field = driver.find_element(By.ID, "password")
            except:
                password_field = driver.find_element(By.ID, "session_password")
            
            # FORCE clear the field using multiple methods
            current_value = password_field.get_attribute("value")
            if current_value:
                print("Clearing cached password")
            
            # Method 1: Clear with Selenium
            password_field.clear()
            time.sleep(0.3)
            
            # Method 2: Select all and delete with keyboard
            password_field.send_keys(Keys.CONTROL + "a")
            password_field.send_keys(Keys.DELETE)
            time.sleep(0.3)
            
            # Method 3: Force with JavaScript
            driver.execute_script("arguments[0].value = '';", password_field)
            time.sleep(0.3)
            
            # Now enter the password
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

    # Go to the profile with English language preference
    time.sleep(5)
    driver.get(profile_url + '?locale=en_US')
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("At profile (English locale)")

    # Try direct URL to recent activity comments with English locale
    activity_url = profile_url.rstrip('/') + '/recent-activity/comments/?locale=en_US'
    print(f"Going directly to: {activity_url}")
    driver.get(activity_url)
    time.sleep(2)

    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("At comments activity page")

    comments = []
    last_height = driver.execute_script("return document.body.scrollHeight")

    scroll_count = 0
    while len(comments) < max_comments and scroll_count < 10:  # Limit scrolls
        print(f"Scroll {scroll_count + 1}")

        # Find comment containers (parent elements that contain all comment data)
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

                # Extract author name (LinkedIn specific selectors)
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
                        if author_name and len(author_name) > 1:  # Ensure it's not just initials
                            break
                    except:
                        continue

                # Extract timestamp (prioritize English/ISO format)
                time_selectors = [
                    ".//time",  # Look for time elements first
                    ".//span[contains(@class, 'time')]",
                    ".//span[contains(@class, 'timestamp')]",
                    ".//span[contains(@class, 'feed-shared-actor__sub-description')]"
                ]

                timestamp = ""
                for selector in time_selectors:
                    try:
                        time_elem = container.find_element(By.XPATH, selector)
                        # First priority: datetime attribute (ISO format)
                        datetime_attr = time_elem.get_attribute("datetime")
                        if datetime_attr:
                            timestamp = datetime_attr
                            print(f"Found datetime attribute: {datetime_attr}")
                            break
                        # Second priority: text content that's likely English
                        text_content = time_elem.text.strip()
                        if text_content:
                            # Check if it looks like English time format (contains numbers and common English words)
                            english_indicators = ['ago', 'hour', 'day', 'week', 'month', 'year', 'm', 'h', 'd', 'w']
                            has_english = any(indicator in text_content.lower() for indicator in english_indicators)
                            has_numbers = any(char.isdigit() for char in text_content)
                            # If it has English indicators or just numbers (like "2h ago"), prefer it
                            if has_english or (has_numbers and len(text_content.split()) <= 3):
                                timestamp = text_content
                                print(f"Found English-like timestamp: {timestamp}")
                                break
                            # If no English found yet, use as fallback
                            elif not timestamp:
                                timestamp = text_content
                                print(f"Using fallback timestamp: {timestamp}")
                    except:
                        continue

                # If still no timestamp, try to find any element with datetime attribute
                if not timestamp:
                    try:
                        datetime_elem = container.find_element(By.XPATH, ".//*[@datetime]")
                        timestamp = datetime_elem.get_attribute("datetime")
                        print(f"Found datetime attribute in any element: {timestamp}")
                    except:
                        print("No timestamp found for this comment")
                        pass

                # Extract comment text
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

                # Clean the comment text
                cleaned_text = clean_comment_text(comment_text)

                # Only add if we have meaningful cleaned text
                if cleaned_text and len(cleaned_text) > 3:  # Minimum 3 characters
                    comment_data = {
                        "author": author_name,
                        "timestamp": timestamp,
                        "original_text": comment_text,
                        "cleaned_text": cleaned_text,
                        "text_length": len(cleaned_text),
                        "scraped_at": time.strftime("%Y-%m-%d %H:%M:%S")
                    }

                    # Avoid duplicates based on cleaned text
                    if not any(c["cleaned_text"] == cleaned_text for c in comments):
                        comments.append(comment_data)
                        print(f"✓ Collected comment {len(comments)}: {cleaned_text[:50]}...")

            except Exception as e:
                print(f"Error processing comment container: {e}")
                continue

        # Scroll down to load more
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        time.sleep(3)

        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("No more content to load")
            break
        last_height = new_height
        scroll_count += 1

    print(f"Total comments collected: {len(comments)}")

    # Save to CSV file
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

        # Add metadata to each comment
        for comment in comments:
            comment_row = comment.copy()
            comment_row['profile_url'] = profile_url
            comment_row['max_comments_requested'] = max_comments
            comment_row['comments_collected'] = len(comments)
            comment_row['session_scraped_at'] = time.strftime("%Y-%m-%d %H:%M:%S")
            writer.writerow(comment_row)

    print(f"📄 Comments saved to {output_file}")

    # Print summary
    for i, comment in enumerate(comments[:max_comments], 1):
        print(f"{i}. [{comment['author']}] {comment['cleaned_text']}")

finally:
    driver.quit()