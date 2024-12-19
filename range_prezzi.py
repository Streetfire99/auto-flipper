import requests
from bs4 import BeautifulSoup
import pandas as pd
import time
import re

def extract_price_range(text):
    """Estrae i valori min e max dal testo del range di prezzi"""
    if not text:
        return None, None
    numbers = re.findall(r'[\d.,]+', text.replace('.', '').replace(',', '.'))
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    return None, None

def get_zone_prices(zone):
    """Estrae i prezzi per una specifica zona e le sue vie"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3'
    }
    
    url = f"https://www.immobiliare.it/mercato-immobiliare/lombardia/milano/{zone}/"
    
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        results = []
        
        # Estrai dati della zona principale
        price_stats = soup.find_all("p", class_="cg-buildingPricesStats__highlighted-subtext")
        if len(price_stats) >= 2:
            vendita_min, vendita_max = extract_price_range(price_stats[0].text)
            vendita_medio = (vendita_min + vendita_max) / 2 if vendita_min and vendita_max else None
            affitto_min, affitto_max = extract_price_range(price_stats[1].text)
            affitto_medio = (affitto_min + affitto_max) / 2 if affitto_min and affitto_max else None
            
            results.append({
                'tipo': 'zona',
                'zona': zone,
                'indirizzo': 'TOTALE ZONA',
                'vendita_min': vendita_min,
                'vendita_max': vendita_max,
                'vendita_medio': vendita_medio,
                'affitto_min': affitto_min,
                'affitto_max': affitto_max,
                'affitto_medio': affitto_medio
            })
        
        # Estrai dati delle singole vie/piazze
        rows = soup.find_all("tr", class_="nd-table__row")
        for row in rows:
            try:
                link = row.find("a", class_="nd-table__url")
                if not link:
                    continue
                    
                cells = row.find_all("td", class_="nd-table__cell")
                if len(cells) >= 3:
                    indirizzo = link.text.strip()
                    vendita = float(cells[1].text.strip().replace('.', '').replace(',', '.'))
                    affitto = float(cells[2].text.strip().replace('.', '').replace(',', '.'))
                    
                    results.append({
                        'tipo': 'via',
                        'zona': zone,
                        'indirizzo': indirizzo,
                        'vendita_min': None,
                        'vendita_max': None,
                        'vendita_medio': vendita,
                        'affitto_min': None,
                        'affitto_max': None,
                        'affitto_medio': affitto
                    })
            except Exception as e:
                print(f"Errore nell'elaborazione di una riga per {zone}: {str(e)}")
                continue
                
        return results
            
    except Exception as e:
        print(f"Errore per la zona {zone}: {str(e)}")
        return [{
            'tipo': 'zona',
            'zona': zone,
            'indirizzo': 'TOTALE ZONA',
            'vendita_min': None,
            'vendita_max': None,
            'vendita_medio': None,
            'affitto_min': None,
            'affitto_max': None,
            'affitto_medio': None
        }]

# Lista delle zone
zones = [
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

# Raccolta dati
all_results = []
for zone in zones:
    print(f"Elaborazione zona: {zone}")
    results = get_zone_prices(zone)
    all_results.extend(results)
    time.sleep(2)  # Pausa tra le richieste

# Creazione DataFrame e salvataggio CSV
df = pd.DataFrame(all_results)

# Riorganizza le colonne per una migliore leggibilità
df = df[['tipo', 'zona', 'indirizzo', 
         'vendita_min', 'vendita_max', 'vendita_medio',
         'affitto_min', 'affitto_max', 'affitto_medio']]

# Salva il CSV
df.to_csv('prezzi_zone_milano_dettagliato.csv', index=False)
print("File CSV creato con successo!")

# Stampa alcune statistiche
print("\nStatistiche:")
print(f"Totale zone analizzate: {len(df[df['tipo'] == 'zona'])}")
print(f"Totale vie/piazze analizzate: {len(df[df['tipo'] == 'via'])}")
