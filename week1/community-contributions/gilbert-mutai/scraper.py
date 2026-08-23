from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

LEAGUES = {
    'EPL':        'https://www.flashscore.com/football/england/premier-league/results/',
    'La Liga':    'https://www.flashscore.com/football/spain/laliga/results/',
    'Bundesliga': 'https://www.flashscore.com/football/germany/bundesliga/results/',
}


def setup_driver(headless=True):
    options = Options()
    if headless:
        options.add_argument('--headless=new')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
    options.add_argument('--window-size=1920,1080')
    driver = webdriver.Chrome(
        service=ChromeService(ChromeDriverManager().install()),
        options=options,
    )
    return driver


def dismiss_cookie_banner(driver):
    try:
        WebDriverWait(driver, 5).until(
            EC.element_to_be_clickable((By.ID, 'onetrust-accept-btn-handler'))
        ).click()
        time.sleep(0.5)
    except Exception:
        pass


def scrape_league(driver, league_name, url):
    print(f'Scraping {league_name} ...')
    driver.get(url)

    dismiss_cookie_banner(driver)

    WebDriverWait(driver, 15).until(
        EC.presence_of_all_elements_located((By.CSS_SELECTOR, '[class*="event__match"]'))
    )

    rows = []
    matches = driver.find_elements(By.CSS_SELECTOR, '[class*="event__match"]')
    for match in matches:
        try:
            date  = match.find_element(By.CSS_SELECTOR, '.event__time').text
            home  = match.find_element(By.CSS_SELECTOR, '[class*="event__homeParticipant"] [class*="wcl-name"]').text
            away  = match.find_element(By.CSS_SELECTOR, '[class*="event__awayParticipant"] [class*="wcl-name"]').text
            goals = match.find_elements(By.CSS_SELECTOR, '[class*="event__score"]')
            score = f'{goals[0].text} - {goals[1].text}' if len(goals) >= 2 else 'vs'
            rows.append({'league': league_name, 'date': date, 'home_team': home, 'score': score, 'away_team': away})
        except Exception:
            continue

    print(f'  → {len(rows)} matches found')
    return rows


def scrape_all_leagues(headless=True):
    driver = setup_driver(headless=headless)
    all_rows = []
    try:
        for league_name, url in LEAGUES.items():
            all_rows.extend(scrape_league(driver, league_name, url))
    finally:
        driver.quit()
    return all_rows
