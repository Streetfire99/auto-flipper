import requests
from bs4 import BeautifulSoup
import csv
import time
from typing import List, Dict
import re
import pandas as pd
import numpy as np
from geopy.geocoders import Nominatim
from geopy.extra.rate_limiter import RateLimiter
from geopy.exc import GeocoderTimedOut, GeocoderServiceError

zone_mapping = {
    'centro': 'Centro Storico',
    'navigli': 'Navigli',
    'affori-bovisa': 'Affori',
    'porta-vittoria-lodi': 'Porta Vittoria',
    'citta-studi-susa': 'Città Studi',
    'porta-romana-cadore-montenero': 'Porta Romana',
    'bicocca-niguarda': 'Bruzzano',
    'cenisio-sarpi-isola': 'Chinatown',
    'centrale-repubblica': 'Centro Direzionale',
    'famagosta-barona': 'Zona 6',
    'maggiolina-istria': 'Zona 2',
    'ponte-lambro-santa-giulia': 'Calvairate',
    'abbiategrasso-chiesa-rossa': 'Zona 5',
    'udine-lambrate': 'Zona 3',
    'ripamonti-vigentino': 'Zona 4',
    'viale-certosa-cascina-merlata': 'Zona 8',
    'arco-della-pace-arena-pagano': 'Brera',
    'garibaldi-moscova-porta-nuova': 'Brera',
    'genova-ticinese': 'Brera',
    'quadronno-palestro-guastalla': 'Brera',
    'fiera-sempione-city-life-portello': 'Brera',
    'solari-washington': 'Brera',
    'porta-venezia-indipendenza': 'Brera',
    'bisceglie-baggio-olmi': 'Baggio',
    'bande-nere-inganni': 'Baggio',
    'forlanini': 'Baggio',
    'cimiano-crescenzago-adriano': 'Affori',
    'corvetto-rogoredo': 'Porta Romana',
    'precotto-turro': 'Zona 3',
    'pasteur-rovereto': 'Zona 2',
    'napoli-soderini': 'Zona 5'
}

zones = [
    "Corvetto, Rogoredo",
    "Precotto, Turro",
    "Pasteur, Rovereto",
    "Ripamonti, Vigentino",
    "Citta Studi, Susa",
    "Solari, Washington",
    "San Siro, Trenno",
    "Porta Romana, Cadore, Montenero",
    "Porta Venezia, Indipendenza",
    "Fiera, Sempione, City Life, Portello",
    "Navigli",
    "Garibaldi, Moscova, Porta Nuova",
    "Quadronno, Palestro, Guastalla",
    "Genova, Ticinese",
    "Arco della Pace, Arena, Pagano",
    "Centrale, Repubblica",
    "Bicocca, Niguarda",
    "Cenisio, Sarpi, Isola",
    "Affori, Bovisa",
    "Viale Certosa, Cascina Merlata",
    "Bisceglie, Baggio, Olmi",
    "Bande Nere, Inganni",
    "Forlanini",
    "Famagosta, Barona",
    "Maggiolina, Istria",
    "Abbiategrasso, Chiesa Rossa",
    "Udine, Lambrate",
    "Porta Vittoria, Lodi",
    "Ponte Lambro, Santa Giulia",
    "Cimiano, Crescenzago, Adriano",
    "Napoli, Soderini",
    "Centro"
]
zones = [zone.replace(", ", "-").replace(" ", "-").lower() for zone in zones]

geolocator = Nominatim(user_agent="backoffice/1.0 (https://backoffice.xeniamilano.com)")

def get_coordinates(address):
    try:
        location = geolocator.geocode(address, timeout=10)
        if location:
            return pd.Series({'latitude': location.latitude, 'longitude': location.longitude})
        return pd.Series({'latitude': None, 'longitude': None})
    except (GeocoderTimedOut, GeocoderServiceError):
        print("Error getting coordinates")
        return pd.Series({'latitude': None, 'longitude': None})
    finally:
        # Aggiungi un piccolo delay per rispettare i limiti di rate del servizio
        time.sleep(0.5)

class ImmobiliareScraper:
    def __init__(self):
        self.base_url = "https://www.immobiliare.it/vendita-case/milano/"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

    def get_page(self,zone: str, page: int = 1) -> str:
        """Fetch a single page from immobiliare.it"""
        params = {
            "criterio": "data",
            "ordine": "desc",
            "pag": str(page)
        }
        
        response = requests.get(self.base_url+"/"+zone+"?localiMinimo=1&localiMassimo=2", params=params, headers=self.headers)
        response.raise_for_status()
        return response.text

    def extract_listing_data(self, listing) -> Dict:
        """Extract relevant data from a single listing"""
        try:
            # Extract price
            price_elem = listing.find("div", class_="in-listingCardPrice")
            price = price_elem.text.strip() if price_elem else "N/A"
            
            # Extract title and link
            title_elem = listing.find("a", class_="in-listingCardTitle")
            title = title_elem.text.strip() if title_elem else "N/A"
            link = title_elem["href"] if title_elem else "N/A"
            
            # Extract first image
            img_elem = listing.find("img")
            image_url = img_elem["src"] if img_elem else "N/A"
            
            # Extract features
            features = listing.find_all("div", class_="in-listingCardFeatureList__item")
            
            # Initialize default values
            rooms = meters = bathrooms = floor = elevator = "N/A"
            
            for feature in features:
                text = feature.text.strip()
                if "locali" in text:
                    rooms = text.replace("locali", "").strip()
                elif "m²" in text:
                    meters = text.replace("m²", "").strip()
                elif "bagni" in text:
                    bathrooms = text.replace("bagni", "").strip()
                elif "Piano" in text:
                    floor = text.replace("Piano", "").strip()
                elif "Ascensore" in text:
                    elevator = "Sì"
            return {
                "prezzo": price,
                "titolo": title,
                "link": link,
                "foto": image_url,
                "n_locali": rooms,
                "metratura": meters,
                "bagni": bathrooms,
                "piano": floor,
                "ascensore": elevator
            }
            
        except Exception as e:
            print(f"Error extracting listing data: {e}")
            return {}

    def scrape_listings(self, zone: str, max_pages: int = 1) -> List[Dict]:
        """Scrape multiple pages of listings"""
        all_listings = []
        
        for page in range(1, max_pages + 1):
            try:
                print(f"Scraping page {page}...")
                html = self.get_page(zone,page)
                soup = BeautifulSoup(html, 'html.parser')
                
                listings = soup.find_all("div", class_="nd-mediaObject--colToRow")
                
                for listing in listings:
                    data = self.extract_listing_data(listing)
                    if data:
                        all_listings.append(data)
                
                time.sleep(0.2)  # Be nice to the server
                
            except Exception as e:
                print(f"Error scraping page {page}: {e}")
                continue
        listings_with_zone = [{**listing, "zona": zone} for listing in all_listings]
        return listings_with_zone

    def save_to_csv(self, listings: List[Dict], filename: str = "immobiliare_listings.csv"):
        """Save listings to CSV file"""
        if not listings:
            print("No listings to save")
            return
            
        fieldnames = [
            "prezzo", "titolo", "link", "foto", "n_locali", 
            "metratura", "bagni", "piano", "ascensore", "zona"
        ]
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(listings)
            print(f"Successfully saved {len(listings)} listings to {filename}")
            
        except Exception as e:
            print(f"Error saving to CSV: {e}")

    def process_data(self, filename: str = "immobiliare_listings.csv") -> pd.DataFrame:
        """Process and clean the scraped data"""
        try:
            # Read the CSV files
            df = pd.read_csv(filename)
            airdna_df = pd.read_csv('airdna.csv')
            
            # Clean price column
            def clean_price(price_str):
                try:
                    price_str = price_str.replace('€', '').strip()
                    if 'da' in price_str.lower():
                        price_str = price_str.lower().replace('da', '').strip()
                    price_str = price_str.replace('.', '').replace(',00', '').strip()
                    return int(price_str)
                except:
                    return np.nan
            
            df['prezzo'] = df['prezzo'].apply(clean_price)
            
            # Map zones to standardized names
            df['zona_standard'] = df['zona'].map(zone_mapping)
            
            # Function to determine which revenue/occupancy/adr to use
            def get_metrics(row):
                if pd.notna(row['n_locali']):
                    try:
                        rooms = int(row['n_locali'])
                    except:
                        rooms = None
                    if rooms is not None and rooms <= 2:
                        return pd.Series({
                            'Revenue Potential': row['revenue_2'],
                            'occupancy': row['occupancy_2'],
                            'adr': row['adr_2']
                        })
                    else:
                        return pd.Series({
                            'Revenue Potential': row['revenue_4'],
                            'occupancy': row['occupancy_4'],
                            'adr': row['adr_4']
                        })
        
                elif pd.notna(row['metratura']):
                    try:
                        meters = int(row['metratura'])
                    except:
                        meters = None
                    if meters is not None and meters <= 60:
                        return pd.Series({
                            'Revenue Potential': float(row['revenue_2']),
                            'occupancy': float(row['occupancy_2']),
                            'adr': float(row['adr_2'])
                        })
                    else:
                        return pd.Series({
                            'Revenue Potential': float(row['revenue_4']),
                            'occupancy': float(row['occupancy_4']),
                            'adr': float(row['adr_4'])
                        })
                else:
                    return pd.Series({
                        'Revenue Potential': np.nan,
                        'occupancy': np.nan,
                        'adr': np.nan
                    })
            
            # Merge with Airdna data
            df = df.merge(airdna_df, left_on='zona_standard', right_on='Zone', how='left')
            
            # Apply the metrics selection
            metrics_df = df.apply(get_metrics, axis=1)
            df['Revenue Potential'] = metrics_df['Revenue Potential']
            df['occupancy'] = metrics_df['occupancy']
            df['adr'] = metrics_df['adr']
            
            # Clean occupancy (remove % symbol and convert to float)
            df['occupancy'] = df['occupancy']/100
            
            # Calculate annual yield
            df['annual_yield'] = (df['Revenue Potential'] / df['prezzo']) * 100
            
            # Split title into address and listing type
            def extract_title_info(title):
                parts = title.split(' ', 1)
                listing_type = parts[0].strip()
                address = parts[1].strip() if len(parts) > 1 else ''
                return pd.Series({'tipo_immobile': listing_type, 'indirizzo': address})
            
            # Create new columns from title
            df[['tipo_immobile', 'indirizzo']] = df['titolo'].apply(extract_title_info)
            
            # Convert ascensore to boolean
            df['ascensore'] = df['ascensore'].map({'Sì': True, 'N/A': False})
            
            # Convert numeric columns
            df['n_locali'] = pd.to_numeric(df['n_locali'], errors='coerce')
            df['metratura'] = pd.to_numeric(df['metratura'], errors='coerce')
            df['bagni'] = pd.to_numeric(df['bagni'], errors='coerce')
            
            # Clean piano column
            def clean_floor(floor_str):
                try:
                    if pd.isna(floor_str) or floor_str == 'N/A':
                        return np.nan
                    # Convert text like "Piano terra" to 0
                    if 'terra' in floor_str.lower():
                        return 0
                    # Extract the number
                    return int(''.join(filter(str.isdigit, floor_str)))
                except:
                    return np.nan
            
            df['piano'] = df['piano'].apply(clean_floor)
            
            # Reorder columns
            columns_order = [
                'prezzo', 'tipo_immobile', 'indirizzo', 'metratura', 
                'n_locali', 'bagni', 'piano', 'ascensore', 'zona',
                'zona_standard', 'Revenue Potential', 'occupancy', 'adr', 'annual_yield',
                'link', 'foto'
            ]
            df = df[columns_order]
            
            # Save processed data
            processed_filename = 'immobiliare_listings_processed.csv'
            df.to_csv(processed_filename, index=False)
            print(f"Processed data saved to {processed_filename}")
            
            return df
            
        except Exception as e:
            print(f"Error processing data: {e}")
            return pd.DataFrame()

def main():
    scraper = ImmobiliareScraper()
    all_listings = []
    
    # Collect listings from all zones
    for zone in zones:  # [:5] for testing, remove slice for all zones
        print(f"\nScraping zone: {zone}")
        listings = scraper.scrape_listings(zone, max_pages=3)
        # Add zone information to each listing
        for listing in listings:
            listing['zona'] = zone
        all_listings.extend(listings)
    
    # Save raw data
    scraper.save_to_csv(all_listings, "immobiliare_listings_all_zones.csv")
    
    # Process all data
    processed_df = scraper.process_data("immobiliare_listings_all_zones.csv")
    
    # Save processed data with zones
    if not processed_df.empty:
        processed_df.to_csv('immobiliare_listings_all_zones_processed.csv', index=False)
        print("All zones processed data saved successfully!")
    

if __name__ == "__main__":
    main()
