from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
import time
import os
from datetime import datetime, timedelta

def scrape_nla_cloud_update():
    # 1. CLOUD SETTINGS: Essential for running on GitHub servers without a monitor
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    csv_filename = 'nla_massive_dataset.csv'
    all_data = []
    
    # 2. LOAD EXISTING DATA: Find the last date recorded in the CSV
    if os.path.exists(csv_filename):
        existing_df = pd.read_csv(csv_filename)
        existing_df['Date_Obj'] = pd.to_datetime(existing_df['Date'], errors='coerce')
        last_date = existing_df['Date_Obj'].max()
        print(f"Latest record in CSV: {last_date}")
    else:
        existing_df = pd.DataFrame()
        last_date = datetime.now() - timedelta(days=7) 

    try:
        driver.get("https://www.nla.com.gh/winning-numbers")
        time.sleep(5)

        # 3. SMART SEARCH: Scrape from the day after our last record to today
        start_search = last_date + timedelta(days=1)
        end_search = datetime.now()
        
        print(f"Scanning for new draws between {start_search.date()} and {end_search.date()}...")

        wait = WebDriverWait(driver, 15)
        date_inputs = wait.until(EC.presence_of_all_elements_located((By.XPATH, "//input[@type='date']")))
        
        # Inject search dates via Javascript
        driver.execute_script(f"arguments[0].value = '{start_search.strftime('%Y-%m-%d')}';", date_inputs[0])
        driver.execute_script(f"arguments[1].value = '{end_search.strftime('%Y-%m-%d')}';", date_inputs[1])
        driver.execute_script("arguments[0].dispatchEvent(new Event('change'));", date_inputs[0])
        driver.execute_script("arguments[1].dispatchEvent(new Event('change'));", date_inputs[1])
        
        search_btn = driver.find_element(By.XPATH, "//button[contains(text(), 'Search')]")
        driver.execute_script("arguments[0].click();", search_btn)
        time.sleep(8) 

        # 4. CAPTURE NEW DATA
        containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'flex') and contains(., 'Draw Number')]")
        
        for container in containers:
            try:
                lines = container.text.split('\n')
                if len(lines) < 2: continue
                
                spans = container.find_elements(By.XPATH, ".//span[string-length(text()) <= 2]")
                nums = [s.text.strip() for s in spans if s.text.strip().isdigit()]
                
                if len(nums) >= 5:
                    winning = "-".join(nums[:5])
                    machine = "-".join(nums[5:10]) if len(nums) >= 10 else "N/A"
                    
                    all_data.append({
                        'Date': lines[0], 
                        'Game': lines[1],
                        'Winning_Numbers': winning,
                        'Machine_Numbers': machine,
                        'Draw_ID': lines[-1]
                    })
            except Exception:
                continue

        # 5. MERGE AND SAVE
        if all_data:
            new_df = pd.DataFrame(all_data)
            final_df = pd.concat([new_df, existing_df.drop(columns=['Date_Obj'], errors='ignore')], ignore_index=True)
            final_df.drop_duplicates(subset=['Date', 'Game'], keep='first', inplace=True)
            
            # Sort newest on top
            final_df['Date_Temp'] = pd.to_datetime(final_df['Date'], errors='coerce')
            final_df = final_df.sort_values(by='Date_Temp', ascending=False).drop(columns=['Date_Temp'])
            
            final_df.to_csv(csv_filename, index=False)
            print(f"✅ SUCCESS: Added {len(all_data)} new draws.")
        else:
            print("No new draws found.")

    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_nla_cloud_update()
