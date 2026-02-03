import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def scrape_pool_hours():
    """
    Scrape Harvard Recreation pool hours and return as structured data.
    
    Returns:
        dict: {
            'schedule': [
                {
                    'date': '1/21',
                    'day': 'Wednesday',
                    'mac_pool': '7am - 5pm Small Pool CLOSED 12pm - 1pm',
                    'blodgett_pool': '12:30pm - 3pm; 5:30pm - 9pm'
                },
                ...
            ],
            'weather_alert': 'Weather update text if any',
            'last_updated': datetime object
        }
    """
    
    url = "https://recreation.gocrimson.com/sports/2021/5/14/facility-hours.aspx"
    
    result = {
        'schedule': [],
        'weather_alert': None,
        'last_updated': datetime.now()
    }
    
    try:
        # Fetch the page
        response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
        response.raise_for_status()
        
        # Parse with BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all tables
        tables = soup.find_all('table')
        
        for table in tables:
            # Check if this table contains pool schedule
            table_text = table.get_text()
            if 'MAC Pool' in table_text and 'Blodgett Pool' in table_text:
                
                # Get all rows
                rows = table.find_all('tr')
                
                # Process data rows (skip header)
                for row in rows[1:]:
                    cells = row.find_all(['th', 'td'])
                    if len(cells) >= 4:
                        date = cells[0].get_text(strip=True)
                        day = cells[1].get_text(strip=True)
                        mac_pool = cells[2].get_text(separator=' ', strip=True)
                        blodgett_pool = cells[3].get_text(separator=' ', strip=True)
                        
                        # Skip completely empty rows
                        if not any([date, day, mac_pool, blodgett_pool]):
                            continue
                        
                        # Clean up the text (remove excessive whitespace)
                        mac_pool = ' '.join(mac_pool.split())
                        blodgett_pool = ' '.join(blodgett_pool.split())
                        
                        result['schedule'].append({
                            'date': date,
                            'day': day,
                            'mac_pool': mac_pool,
                            'blodgett_pool': blodgett_pool
                        })
                
                break
        
        # Look for weather alerts
        page_text = soup.get_text()
        weather_match = re.search(r'Weather Update:.*?(?=\n\*|\*\*|$)', page_text, re.DOTALL)
        if weather_match:
            result['weather_alert'] = ' '.join(weather_match.group(0).split())
            
    except Exception as e:
        result['error'] = str(e)
    result = str(result)
    print(type(result))
    return result



if __name__ == "__main__":
    # Get the data
    pool_data = scrape_pool_hours()
    