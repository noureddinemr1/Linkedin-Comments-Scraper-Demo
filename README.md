# LinkedIn Comments Scraper Demo

This project demonstrates how to scrape comments from a LinkedIn profile's posts using Selenium.

## Setup

1. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

2. Set up your LinkedIn credentials in `.env`:
   ```
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   LINKEDIN_PROFILE_URL=https://www.linkedin.com/in/yourprofile/
   MAX_POSTS=10
   SCROLL_DELAY=2
   REQUEST_DELAY=3
   ```

3. Run the scraper:
   ```
   python main.py
   ```

The script will open Chrome, navigate to the profile, scroll through posts, load comments, and print the first 10 comments found.

## Note

- The script uses a persistent Chrome profile to avoid re-login.
- XPaths may need adjustment based on LinkedIn's current structure.
- Ensure you have Chrome installed and webdriver-manager handles the driver.
