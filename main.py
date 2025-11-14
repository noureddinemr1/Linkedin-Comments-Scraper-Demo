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

print("🔧 Loading NopeCha extension...")
options.add_extension('ext.crx')

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
            email_field = driver.find_element(By.ID, "username") or driver.find_element(By.ID, "session_key")
            email_field.send_keys(email)
            password_field = driver.find_element(By.ID, "password") or driver.find_element(By.ID, "session_password")
            password_field.send_keys(password)
            login_button = driver.find_element(By.XPATH, "//button[@type='submit' and (contains(text(), 'Sign in') or contains(text(), \"S'identifier\"))]")
            login_button.click()
            #solve captcha if presented

            WebDriverWait(driver, 30).until(EC.url_contains("feed"))
            print("Logged in")
        except Exception as e:
            print(f"Login failed: {e}")
            driver.quit()
            exit()
    else:
        print("Already logged in")

    # Go to the profile
    driver.implicitly_wait(10)
    driver.get(profile_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    print("At profile")

    # Try direct URL to recent activity comments
    activity_url = profile_url.rstrip('/') + '/recent-activity/comments/'
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
        
        # Try multiple XPaths to find comment text elements
        comment_elements = driver.find_elements(By.XPATH, "//span[contains(@class, 'comment-text')] | //span[contains(@class, 'break-words')] | //div[contains(@class, 'feed-shared-update-v2__commentary')]//span[@dir='ltr'] | //div[contains(@class, 'update-components-text')]//span")
        print(f"Found {len(comment_elements)} potential comment texts")

        # Debug: Print all found texts to see what we're getting
        for i, elem in enumerate(comment_elements[:5]):  # Print first 5
            try:
                text = elem.text.strip()
                print(f"Debug - Element {i}: '{text[:100]}...' (len={len(text)})")
            except:
                pass

        for elem in comment_elements:
            if len(comments) >= max_comments:
                break
            try:
                text = elem.text.strip()
                # Lower minimum length to 5 characters
                if text and len(text) > 5 and text not in comments:  # Avoid duplicates and very short texts
                    comments.append(text)
                    print(f"✓ Collected comment {len(comments)}: {text[:50]}...")
            except Exception as e:
                print(f"Error getting comment text: {e}")
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
    # Print the comments
    for i, comment in enumerate(comments[:max_comments], 1):
        print(f"{i}. {comment}")

finally:
    driver.quit()
