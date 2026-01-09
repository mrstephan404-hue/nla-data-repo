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
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")
    # Add a user-agent to look like a real browser
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    
    csv_filename = 'nla_massive_dataset.csv'
    
    # 1. LOAD DATA & CALCULATE DATES
    if os.path.exists(csv_filename):
        df = pd.read_csv(csv_filename)
        df['Date_DT'] = pd.to_datetime(df['Date'], errors='coerce')
        last_date = df['Date_DT'].max()
    else:
        df = pd.DataFrame()
        last_date = datetime.now() - timedelta(days=5)

    start_search = (last_date + timedelta(days=1)).strftime('%Y-%m-%d')
    end_search = datetime.now().strftime('%Y-%m-%d')
    
    print(f"Searching for new draws from {start_search} to {end_search}...")

    try:
        driver.get("https://www.nla.com.gh/winning-numbers")
        wait = WebDriverWait(driver, 20)

        # 2. WAIT FOR DATE INPUTS (More robust check)
        # We wait until at least 2 date inputs are present
        wait.until(lambda d: len(d.find_elements(By.XPATH, "//input[@type='date']")) >= 2)
        date_inputs = driver.find_elements(By.XPATH, "//input[@type='date']")

        # Inject dates
        driver.execute_script("arguments[0].value = arguments[1];", date_inputs[0], start_search)
        driver.execute_script("arguments[0].value = arguments[1];", date_inputs[1], end_search)
        
        # 3. CLICK SEARCH
        search_btn = wait.until(EC.element_to_be_clickable((By.XPATH, "//button[contains(text(), 'Search')]")))
        driver.execute_script("arguments[0].click();", search_btn)
        
        print("Search submitted. Waiting for results...")
        time.sleep(10) # Essential wait for NLA's slow results load

        # 4. DATA EXTRACTION
        containers = driver.find_elements(By.XPATH, "//div[contains(@class, 'flex') and contains(., 'Draw Number')]")
        new_results = []
        
        for container in containers:
            try:
                text = container.text.split('\n')
                # Find the circles/spans containing numbers
                spans = container.find_elements(By.XPATH, ".//span[string-length(text()) <= 2]")
                nums = [s.text.strip() for s in spans if s.text.strip().isdigit()]
                
                if len(nums) >= 5:
                    new_results.append({
                        'Date': text[0],
                        'Game': text[1],
                        'Winning_Numbers': "-".join(nums[:5]),
                        'Machine_Numbers': "-".join(nums[5:10]) if len(nums) >= 10 else "N/A",
                        'Draw_ID': text[-1]
                    })
            except: continue

        # 5. MERGE & SAVE
        if new_results:
            new_df = pd.DataFrame(new_results)
            # Remove helper column from old data before merging
            if 'Date_DT' in df.columns: df = df.drop(columns=['Date_DT'])
            
            final_df = pd.concat([new_df, df], ignore_index=True).drop_duplicates(subset=['Date', 'Game'])
            final_df.to_csv(csv_filename, index=False)
            print(f"✅ Success! Added {len(new_results)} new records.")
        else:
            print("No new draws found for these dates.")

    except Exception as e:
        print(f"❌ Error during scrape: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    scrape_nla_cloud_update()
