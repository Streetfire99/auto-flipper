import requests
import pandas as pd
from datetime import datetime
import time

# Lista dei quartieri di Milano
neighborhoods = [
    'centro',
    'arco-della-pace-arena-pagano',
    'genova-ticinese',
    'quadronno-palestro-guastalla',
    'garibaldi-moscova-porta-nuova',
    'fiera-sempione-city-life-portello',
    'navigli',
    'porta-romana-cadore-montenero',
    'porta-venezia-indipendenza',
    'centrale-repubblica',
    'cenisio-sarpi-isola',
    'viale-certosa-cascina-merlata',
    'bande-nere-inganni',
    'famagosta-barona',
    'abbiategrasso-chiesa-rossa',
    'porta-vittoria-lodi',
    'cimiano-crescenzago-adriano',
    'bicocca-niguarda',
    'solari-washington',
    'affori-bovisa',
    'san-siro-trenno',
    'bisceglie-baggio-olmi',
    'ripamonti-vigentino',
    'forlanini',
    'citta-studi-susa',
    'maggiolina-istria',
    'precotto-turro',
    'udine-lambrate',
    'pasteur-rovereto',
    'ponte-lambro-santa-giulia',
    'corvetto-rogoredo',
    'napoli-soderini'
]

def get_price_data(neighborhood):
    """Fetch price data for a specific neighborhood"""
    base_url = "https://www.immobiliare.it/api-next/city-guide/price-chart/1/"
    path = f"/mercato-immobiliare/lombardia/milano/{neighborhood}/"
    params = {
        '__lang': 'it',
        'path': path
    }
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        return data['labels'], data['values']
    except Exception as e:
        print(f"Error fetching data for {neighborhood}: {str(e)}")
        return None, None

def create_price_dataset():
    """Create a dataset with all neighborhoods' price data"""
    all_data = []
    
    for neighborhood in neighborhoods:
        print(f"Fetching data for {neighborhood}...")
        dates, prices = get_price_data(neighborhood)
        
        if dates and prices:
            # Create records for each date-price pair
            for date, price in zip(dates, prices):
                all_data.append({
                    'neighborhood': neighborhood,
                    'date': datetime.strptime(date, '%Y-%m-%d'),
                    'price_per_sqm': float(price)
                })
        
        # Add a small delay between requests
        time.sleep(1)
    
    # Create DataFrame
    df = pd.DataFrame(all_data)
    
    # Sort by neighborhood and date
    df = df.sort_values(['neighborhood', 'date'])
    
    return df

if __name__ == "__main__":
    # Create the dataset
    df = create_price_dataset()
    
    # Save to CSV
    df.to_csv('milano_real_estate_prices.csv', index=False)
    
    # Display some basic statistics
    print("\nDataset Summary:")
    print(f"Total records: {len(df)}")
    print("\nLatest prices by neighborhood:")
    latest_prices = df.sort_values('date').groupby('neighborhood').last()
    print(latest_prices[['price_per_sqm']])

    # Create a pivot table for easier analysis
    pivot_df = df.pivot(index='date', columns='neighborhood', values='price_per_sqm')
    pivot_df.to_csv('milano_real_estate_prices_pivot.csv')
