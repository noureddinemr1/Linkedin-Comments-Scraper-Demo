import pyautogui
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import time
import requests
import portpicker
import os
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from tqdm import tqdm
import pandas as pd
from datetime import datetime
import json

def sleep_with_progress(seconds, message="Waiting"):
    """Sleep with progress bar"""
    for _ in tqdm(range(seconds), desc=message, unit="s"):
        time.sleep(1)

def scroll_to_load(driver, scrolls=3, delay=2):
    """Scroll page to load dynamic content"""
    for i in range(scrolls):
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        print(f"📜 Scroll {i+1}/{scrolls}")
        time.sleep(delay)
    driver.execute_script("window.scrollTo(0, 0);")

class LinkedInScraper:
    def __init__(self):
        self.driver = None
        self.profile_path = os.path.join(os.getcwd(), "linkedin_profile")
        self.setup_driver()
        
    def setup_driver(self):
        """Setup Chrome driver with anti-detection measures"""
        options = webdriver.ChromeOptions()
        
        # Use persistent profile to save login session
        options.add_argument(f"--user-data-dir={self.profile_path}")
        options.add_argument("--profile-directory=Default")
        
        # Anti-detection settings
        options.add_argument("--start-maximized")
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-infobars')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option('excludeSwitches', ['enable-automation'])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Language and preferences
        options.add_experimental_option('prefs', {
            'intl.accept_languages': 'en,en_US',
            'profile.default_content_setting_values.notifications': 2
        })
        
        # Start driver
        port = portpicker.pick_unused_port()
        chromedriver_path = ChromeDriverManager().install()
        if not chromedriver_path.endswith('chromedriver.exe'):
            chromedriver_path = os.path.join(os.path.dirname(chromedriver_path), 'chromedriver.exe')
        
        self.driver = webdriver.Chrome(service=Service(chromedriver_path), options=options)
        
        # Remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        print("✅ Driver initialized")
    
    def login(self, email=None, password=None):
        """Login to LinkedIn (manual or automated)"""
        self.driver.get("https://www.linkedin.com/login")
        time.sleep(3)
        
        # Check if already logged in
        if "feed" in self.driver.current_url or "mynetwork" in self.driver.current_url:
            print("✅ Already logged in!")
            return True
        
        if email and password:
            try:
                # Enter email
                email_field = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "username"))
                )
                email_field.send_keys(email)
                time.sleep(1)
                
                # Enter password
                password_field = self.driver.find_element(By.ID, "password")
                password_field.send_keys(password)
                time.sleep(1)
                
                # Click login button
                login_button = self.driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                login_button.click()
                
                print("🔐 Logging in...")
                sleep_with_progress(10, "Waiting for login")
                
                # Check for verification or CAPTCHA
                if "challenge" in self.driver.current_url or "checkpoint" in self.driver.current_url:
                    print("⚠️ Verification required. Please complete it manually.")
                    input("Press Enter after completing verification...")
                
                return True
            except Exception as e:
                print(f"❌ Login error: {e}")
                return False
        else:
            print("🔐 Please login manually...")
            input("Press Enter after logging in...")
            return True
    
    def navigate_to_profile(self, profile_url=None):
        """Navigate to your LinkedIn profile"""
        if profile_url:
            self.driver.get(profile_url)
        else:
            # Click on "Me" icon to go to profile
            try:
                self.driver.get("https://www.linkedin.com/feed/")
                time.sleep(2)
                me_button = WebDriverWait(self.driver, 10).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, "a[href*='/in/']"))
                )
                profile_url = me_button.get_attribute('href')
                self.driver.get(profile_url)
                print(f"✅ Navigated to profile: {profile_url}")
            except Exception as e:
                print(f"❌ Error navigating to profile: {e}")
                return None
        
        time.sleep(3)
        return self.driver.current_url
    
    def get_recent_posts(self, max_posts=10):
        """Get URLs of recent posts from profile"""
        print(f"📝 Fetching up to {max_posts} recent posts...")
        
        # Scroll to load posts
        scroll_to_load(self.driver, scrolls=5, delay=2)
        
        post_urls = []
        try:
            # Find all post elements
            posts = self.driver.find_elements(By.CSS_SELECTOR, "div.feed-shared-update-v2")
            
            for post in posts[:max_posts]:
                try:
                    # Find the post link
                    link_element = post.find_element(By.CSS_SELECTOR, "a[href*='/feed/update/']")
                    post_url = link_element.get_attribute('href')
                    if post_url and post_url not in post_urls:
                        post_urls.append(post_url)
                        print(f"  ✓ Found post: {post_url[:60]}...")
                except NoSuchElementException:
                    continue
            
            print(f"✅ Found {len(post_urls)} posts")
            return post_urls
        except Exception as e:
            print(f"❌ Error finding posts: {e}")
            return []
    
    def scrape_comments_from_post(self, post_url):
        """Scrape all comments from a single post"""
        self.driver.get(post_url)
        sleep_with_progress(4, "Loading post")
        
        comments_data = []
        
        try:
            # Click "Show more comments" buttons if available
            try:
                show_more_buttons = self.driver.find_elements(By.CSS_SELECTOR, "button[aria-label*='more comment']")
                for button in show_more_buttons:
                    try:
                        self.driver.execute_script("arguments[0].click();", button)
                        time.sleep(1)
                    except:
                        continue
            except:
                pass
            
            # Scroll to load more comments
            scroll_to_load(self.driver, scrolls=3, delay=2)
            
            # Find all comment elements
            comments = self.driver.find_elements(By.CSS_SELECTOR, "article.comments-comment-item")
            
            print(f"  💬 Found {len(comments)} comments")
            
            for comment in comments:
                try:
                    # Extract commenter name
                    name_element = comment.find_element(By.CSS_SELECTOR, "span.comments-post-meta__name-text")
                    commenter_name = name_element.text.strip()
                    
                    # Extract comment text
                    text_element = comment.find_element(By.CSS_SELECTOR, "span.comments-comment-item__main-content")
                    comment_text = text_element.text.strip()
                    
                    # Extract timestamp
                    try:
                        time_element = comment.find_element(By.CSS_SELECTOR, "time")
                        timestamp = time_element.get_attribute('datetime')
                    except:
                        timestamp = None
                    
                    # Extract commenter profile URL
                    try:
                        profile_link = comment.find_element(By.CSS_SELECTOR, "a[href*='/in/']")
                        commenter_url = profile_link.get_attribute('href')
                    except:
                        commenter_url = None
                    
                    comments_data.append({
                        'post_url': post_url,
                        'commenter_name': commenter_name,
                        'commenter_url': commenter_url,
                        'comment_text': comment_text,
                        'timestamp': timestamp,
                        'scraped_at': datetime.now().isoformat()
                    })
                    
                except Exception as e:
                    print(f"    ⚠️ Error parsing comment: {e}")
                    continue
            
            print(f"  ✅ Scraped {len(comments_data)} comments from this post")
            
        except Exception as e:
            print(f"  ❌ Error scraping comments: {e}")
        
        return comments_data
    
    def scrape_all_comments(self, max_posts=10):
        """Scrape comments from recent posts"""
        print(f"\n{'='*60}")
        print("🚀 Starting LinkedIn Comment Scraper")
        print(f"{'='*60}\n")
        
        # Navigate to profile
        profile_url = self.navigate_to_profile()
        if not profile_url:
            print("❌ Failed to navigate to profile")
            return []
        
        # Get recent posts
        post_urls = self.get_recent_posts(max_posts=max_posts)
        
        if not post_urls:
            print("❌ No posts found")
            return []
        
        # Scrape comments from each post
        all_comments = []
        for i, post_url in enumerate(post_urls, 1):
            print(f"\n📄 Scraping post {i}/{len(post_urls)}")
            comments = self.scrape_comments_from_post(post_url)
            all_comments.extend(comments)
            time.sleep(2)  # Be respectful with requests
        
        print(f"\n✅ Total comments scraped: {len(all_comments)}")
        return all_comments
    
    def save_to_csv(self, comments, filename='linkedin_comments.csv'):
        """Save comments to CSV file"""
        if not comments:
            print("⚠️ No comments to save")
            return
        
        df = pd.DataFrame(comments)
        df.to_csv(filename, index=False, encoding='utf-8')
        print(f"💾 Saved {len(comments)} comments to {filename}")
    
    def save_to_json(self, comments, filename='linkedin_comments.json'):
        """Save comments to JSON file"""
        if not comments:
            print("⚠️ No comments to save")
            return
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(comments, f, indent=2, ensure_ascii=False)
        print(f"💾 Saved {len(comments)} comments to {filename}")
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            print("👋 Browser closed")


# === Main Execution ===
if __name__ == "__main__":
    scraper = LinkedInScraper()
    
    try:
        # Login (first time will require manual login)
        # For automated login, provide credentials:
        # scraper.login(email="your@email.com", password="yourpassword")
        scraper.login()
        
        # Scrape comments from your recent posts
        comments = scraper.scrape_all_comments(max_posts=10)
        
        # Save results
        if comments:
            scraper.save_to_csv(comments)
            scraper.save_to_json(comments)
            
            # Print summary
            print(f"\n{'='*60}")
            print("📊 SCRAPING SUMMARY")
            print(f"{'='*60}")
            print(f"Total comments: {len(comments)}")
            print(f"Unique commenters: {len(set(c['commenter_name'] for c in comments))}")
            print(f"Posts scraped: {len(set(c['post_url'] for c in comments))}")
            print(f"{'='*60}\n")
        
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    finally:
        scraper.close()