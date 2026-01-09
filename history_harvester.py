import requests
from bs4 import BeautifulSoup
import pandas as pd
import time

def harvest_ghanayello():
    base_url = "https://www.ghanayello.com/lottery/results/history"
    all_data = []
    
    # We will loop through the pages (GhanaYello uses ?page=1, ?page=2, etc.)
    # 2017 to 2026 is roughly 150-200 pages of results
    for page in range(1, 150):
        print(f"Harvesting Page {page}...")
        try:
            response = requests.get(f"{base_url}?page={page}", timeout=10)
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the results table or list
            # Note: GhanaYello structure usually puts results in 'results-list' or 'table'
            rows = soup.select('.results-list .item') # Adjusting based on common Yello patterns
            
            if not rows: break # Stop if no more data
            
            for row in rows:
                date = row.select_one('.date').text.strip()
                game = row.select_one('.game').text.strip()
                nums = row.select_one('.numbers').text.strip().replace(" ", "-")
                
                all_data.append({
                    'Date': date,
                    'Game': game,
                    'Winning_Numbers': nums,
                    'Machine_Numbers': "00-00-00-00-00", # Yello often misses machine nums
                    'Draw_ID': "Hist-" + date
                })
            time.sleep(1) # Be nice to their server
        except:
            break

    if all_data:
        df = pd.DataFrame(all_data)
        df.to_csv('nla_massive_dataset.csv', index=False)
        print(f"Successfully harvested {len(all_data)} historical draws!")

if __name__ == "__main__":
    harvest_ghanayello()
