from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time

def scrape_horoscopes_ht(headless=True, timeout=3):
    """
    Scrape horoscope data from Hindustan Times astrology page.
    
    Args:
        headless (bool): Run Chrome in headless mode. Default is False.
        timeout (int): WebDriverWait timeout in seconds. Default is 3.
    
    Returns:
        dict: Dictionary with sun sign names as keys and horoscope content as values.
              Returns empty dict if scraping fails.
    
    Raises:
        Exception: Prints error messages but continues scraping other signs.
    """
    
    # Configure Chrome options
    options = webdriver.ChromeOptions()
    print("Headless mode:", headless)
    if headless:
        options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    horoscope_data = {}
    
    # List of sun signs to iterate through
    sun_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
                 "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    
    try:
        for sign_index, sign_name in enumerate(sun_signs):
            try:
                # Load the astrology page
                driver.get("https://www.hindustantimes.com/astrology")
                
                # Wait for the horoscope sun signs list to load
                wait = WebDriverWait(driver, timeout)
                horoscope_list = wait.until(
                    EC.presence_of_element_located((By.CLASS_NAME, "horoscopeSunSign"))
                )
                
                # Get all li elements (12 sun signs)
                li_elements = horoscope_list.find_elements(By.TAG_NAME, "li")
                
                # Click the specific li element by index
                if sign_index < len(li_elements):
                    li = li_elements[sign_index]
                    
                    # Extract sun sign name from span
                    span = li.find_element(By.TAG_NAME, "span")
                    sun_sign_name = span.text
                    
                    # Find and click the anchor tag
                    anchor = li.find_element(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", anchor)
                    
                    time.sleep(3)
                    
                    # Find the first prediction-card element
                    prediction_card = wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "prediction-card"))
                    )
                    
                    # Find and click the "READ FULL PREDICTION" link
                    read_link = prediction_card.find_element(By.TAG_NAME, "a")
                    driver.execute_script("arguments[0].click();", read_link)
                    
                    time.sleep(3)
                    
                    # Get all content elements
                    content_elements = driver.find_elements(By.CLASS_NAME, "content")
                    
                    # Collect text from all content elements
                    content_text = "\n".join([elem.text for elem in content_elements])
                    
                    # Store in dictionary
                    horoscope_data[sun_sign_name] = content_text
                    print(f"✓ Successfully processed {sun_sign_name}")
                
            except Exception as e:
                print(f"✗ Error processing sign at index {sign_index}: {str(e)}")
                
    finally:
        driver.quit()
    
    return horoscope_data


def scrape_horoscopes_vedicrishi(headless=True, timeout=3):
    """
    Scrape horoscope data from Vedic Rishi daily horoscope pages.
    
    Args:
        headless (bool): Run Chrome in headless mode. Default is False.
        timeout (int): WebDriverWait timeout in seconds. Default is 3.
    
    Returns:
        dict: Dictionary with sun sign names as keys and horoscope content as values.
              Returns empty dict if scraping fails.
    """
    
    # Configure Chrome options
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    horoscope_data = {}
    
    sun_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
                 "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    
    try:
        for sign_index, sign_name in enumerate(sun_signs):
            try:
                # Load the horoscope page for the current sign
                driver.get(f"https://vedicrishi.in/horoscope/{sign_name}-daily-horoscope")
                
                wait = WebDriverWait(driver, timeout)
                horoscope_section = wait.until(
                    EC.presence_of_element_located((By.CSS_SELECTOR, "#__next > div:nth-child(1) > div:nth-child(4) > div > section.w-full.bg-transparent.py-12 > div > div.lg\\:col-span-8 > div.flex.flex-col.gap-6.items-center.pb-10"))
                )
                
                # Extract the visible horoscope text
                content_text = horoscope_section.text.strip()
                horoscope_data[sign_name] = content_text
                print(f"✓ Successfully processed {sign_name}")
                
            except Exception as e:
                print(f"✗ Error processing sign at index {sign_index}: {str(e)}")
                
    finally:
        driver.quit()
    
    return horoscope_data


def scrape_horoscopes_indiatv(headless=True, timeout=3):
    """
    Scrape horoscope data from India TV daily horoscope pages.
    
    Args:
        headless (bool): Run Chrome in headless mode. Default is False.
        timeout (int): WebDriverWait timeout in seconds. Default is 3.
    
    Returns:
        dict: Dictionary with sun sign names as keys and horoscope content as values.
              Returns empty dict if scraping fails.
    """
    
    # Configure Chrome options
    options = webdriver.ChromeOptions()
    if headless:
        options.add_argument("--headless")
    
    driver = webdriver.Chrome(options=options)
    horoscope_data = {}
    
    sun_signs = ["aries", "taurus", "gemini", "cancer", "leo", "virgo", 
                 "libra", "scorpio", "sagittarius", "capricorn", "aquarius", "pisces"]
    
  
    try:
        # Load the horoscope page for the current sign
        driver.get(f"https://www.indiatvnews.com/astrology")
        
        wait = WebDriverWait(driver, timeout)
        today_horoscope_link = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "body > main > section:nth-child(2) > div > div > div.lhs > div.cat-top-news > ul > li.big-news > a"))
        )
        
        today_horoscope_link.click()
        time.sleep(3)   
        # Extract the visible horoscope text
        content_text = driver.find_element(By.ID, "content").text.strip()
        
        # in the context_text we have all horsocope for all signs, we need to split it into individual signs
        # The content_text is expected be in dictionary format with sign names as keys and horoscope text as values, we need to parse it accordingly
        # Assuming the content_text is in the format: "aries: horoscope text\n taurus: horoscope text\n ...", we can split it by newlines and then by colon to get the sign name and horoscope text
        lines = content_text.split("\n")
        if len(lines) < 12:
            raise Exception("Expected 12 lines of horoscope data, but got less.")
        
        for line in lines:
            # if the line contains any of the sun_signs create a new entry in the horoscope_data dictionary with the sign name as key and the horoscope text as value
            # if the line does not contain any of the sun_signs keep appending the horoscope text to the previous sign's horoscope text until we encounter the next sign name
            sign_match  =  False
            for sign in sun_signs:
                if sign in line.strip().lower():
                    sign_match = True
                    sign_name = sign.capitalize()
                    # horoscope_text = line.split(":", 1)[1].strip() if ":" in line else ""
                    horoscope_data[sign_name] = ""
                    last_sign = list(horoscope_data.keys())[-1]
                    break
            if not sign_match:
                # if the line does not contain any of the sun_signs, append the text to the previous sign's horoscope text
                if horoscope_data:
                    last_sign = list(horoscope_data.keys())[-1]
                    horoscope_data[last_sign] += " " + line.strip()

        print(f"✓ Successfully processed horoscopes for all signs")
        
    except Exception as e:
        print(f"✗ Error processing horoscopes: {str(e)}")
        
    finally:
        driver.quit()
    
    return horoscope_data