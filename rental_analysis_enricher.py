import requests
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import traceback



# URL centralizzato per l'analisi
IMMOBILIARE_URL = "https://www.immobiliare.it/annunci/111860595/?entryPoint=map"

# File paths
PREZZI_ZONE_FILE = 'prezzi_zone_milano_dettagliato.csv'
AIRBNB_FILE = 'listing_clean.csv'
OUTPUT_FILE = 'analisi_immobili_updated.txt'

# Aggiungi questo dizionario all'inizio del file
ZONE_MAPPING = {
    "centro": ["DUOMO"],
    "arco-della-pace-arena-pagano": ["PAGANO"],
    "genova-ticinese": ["TICINESE"],
    "quadronno-palestro-guastalla": ["GUASTALLA"],
    "garibaldi-moscova-porta-nuova": ["BRERA", "GARIBALDI REPUBBLICA"],
    "fiera-sempione-city-life-portello": ["TRE TORRI", "PARCO SEMPIONE", "PORTELLO"],
    "navigli": ["NAVIGLI", "TORTONA"],
    "porta-romana-cadore-montenero": ["PORTA ROMANA", "SCALO ROMANA"],
    "porta-venezia-indipendenza": ["BUENOS AIRES - VENEZIA", "GIARDINI PORTA VENEZIA"],
    "centrale-repubblica": ["CENTRALE"],
    "cenisio-sarpi-isola": ["SARPI", "ISOLA", "FARINI", "GHISOLFA"],
    "viale-certosa-cascina-merlata": ["QT 8", "SACCO", "VILLAPIZZONE", "GALLARATESE"],
    "bande-nere-inganni": ["BANDE NERE", "SELINUNTE"],
    "famagosta-barona": ["BARONA", "S. CRISTOFORO"],
    "abbiategrasso-chiesa-rossa": ["RONCHETTO DELLE RANE", "RONCHETTO SUL NAVIGLIO", "GRATOSOGLIO - TICINELLO"],
    "porta-vittoria-lodi": ["UMBRIA - MOLISE", "ORTOMERCATO", "XXII MARZO"],
    "cimiano-crescenzago-adriano": ["ADRIANO", "PARCO LAMBRO - CIMIANO"],
    "bicocca-niguarda": ["BICOCCA", "NIGUARDA - CA' GRANDA", "PARCO NORD"],
    "solari-washington": ["WASHINGTON", "DE ANGELI - MONTE ROSA"],
    "affori-bovisa": ["AFFORI", "BOVISA", "COMASINA"],
    "san-siro-trenno": ["S. SIRO", "FIGINO", "TRENNO", "QUARTO CAGNINO", "QUINTO ROMANO"],
    "bisceglie-baggio-olmi": ["BAGGIO"],
    "ripamonti-vigentino": ["RIPAMONTI", "QUINTOSOLE", "CHIARAVALLE"],
    "forlanini": ["PARCO FORLANINI - ORTICA", "MECENATE"],
    "città-studi-susa": ["CITTA' STUDI"],
    "maggiolina-istria": ["MACIACHINI - MAGGIOLINA"],
    "precotto-turro": ["GRECO"],
    "udine-lambrate": ["LAMBRATE"]
}

# Funzione per estrarre il valore dalle coppie dt/dd
def get_feature_value(soup, feature_title):
    item = soup.find("dt", string=feature_title)
    return item.find_next("dd").text.strip() if item else "N/A"

# Dizionario con i dati raccolti
response = requests.get(IMMOBILIARE_URL)
soup = BeautifulSoup(response.text, 'html.parser')

data = {
    "ADDRESS": soup.find("h1", class_="re-title__title").text if soup.find("h1") else "",
    "LINK": IMMOBILIARE_URL,
    "DESCRIPTION": soup.find("div", class_="in-readAll").get_text(separator=" ", strip=True) if soup.find("div", class_="in-readAll") else "",
    "TIPOLOGIA": get_feature_value(soup, "Tipologia"),
    "BEDROOMS": get_feature_value(soup, "Camere da letto"),
    "BATHROOMS": get_feature_value(soup, "Bagni"),
    "GARAGE": get_feature_value(soup, "Box, posti auto"),
    "LOCALi": get_feature_value(soup, "Locali"),
    "SQFTS": get_feature_value(soup, "Superficie"),
    "YEAR_BUILT": get_feature_value(soup, "Anno di costruzione"),
    "ENERGY_CLASS": soup.find("span", {"data-energy-class": True})["data-energy-class"] if soup.find("span", {"data-energy-class": True}) else "N/A",
    "PURCHASE_PRICE": soup.find("div", class_="re-overview__price").text.strip() if soup.find("div", class_="re-overview__price") else "",
    "MONTHLY_MAINTENANCE": get_feature_value(soup, "Spese condominio"),
    "ENERGY_CONSUMPTION": soup.find("p", string=lambda x: x and "kWh/m²" in x).text.split()[0] if soup.find("p", string=lambda x: x and "kWh/m²" in x) else "N/A"
}

# Creazione della tabella pandas
df = pd.DataFrame([data])

# Stampa la tabella
print(df)

def stima_componenti_da_locali(n_locali):
    """
    Stima il numero di componenti basandosi sul numero di locali
    
    Args:
        n_locali (int): Numero di locali dell'immobile
    
    Returns:
        int: Numero stimato di componenti
    """
    if n_locali <= 2:  # Monolocale o bilocale
        return 1
    elif n_locali == 3:  # Trilocale
        return 2
    elif n_locali == 4:  # Quadrilocale
        return 3
    else:  # 5 o più locali
        return 4

def calcola_tari(mq, n_componenti=1, tariffa_fissa=1.10, quota_provinciale=0.05):
    """
    Calcola la TARI annuale basata sui parametri forniti
    
    Args:
        mq (float): Metri quadri dell'immobile
        n_componenti (int): Numero di componenti del nucleo familiare
        tariffa_fissa (float): Tariffa al mq (varia per comune)
        quota_provinciale (float): Percentuale della quota provinciale
    
    Returns:
        float: Importo annuale TARI
    """
    # Tabella esempio delle tariffe variabili per numero componenti
    tariffe_variabili = {
        1: 90.00,    # single
        2: 130.00,   # coppia
        3: 163.27,   # famiglia di tre
        4: 190.00,   # famiglia di quattro
        5: 210.00,   # famiglia di cinque
        6: 230.00    # famiglia di sei o più
    }
    
    # Calcolo parte fissa
    parte_fissa = tariffa_fissa * mq
    
    # Calcolo parte variabile
    parte_variabile = tariffe_variabili.get(n_componenti, tariffe_variabili[1])
    
    # Calcolo quota provinciale
    imponibile = parte_fissa + parte_variabile
    quota_prov = imponibile * quota_provinciale
    
    # Totale TARI
    totale = parte_fissa + parte_variabile + quota_prov
    
    return totale

def get_market_data_url(soup):
    """Estrae l'URL della pagina con i dati di mercato della zona"""
    # Aggiungiamo più selettori per trovare il link dei prezzi
    selectors = [
        ("a", {"class_": "nd-list__link", "string": lambda x: "Prezzi mq" in str(x)}),
        ("a", {"string": lambda x: "Prezzi mq" in str(x)}),
        ("a", {"href": lambda x: "prezzi-mq" in str(x)}),
        ("a", {"class_": "in-zone__link"})
    ]
    
    for selector, attrs in selectors:
        market_link = soup.find(selector, **attrs)
        if market_link and market_link.get('href'):
            print(f"Found market URL: {market_link['href']}")
            return market_link['href']
    
    print("No market URL found")
    return None

def get_price_range(market_soup, type='vendita'):
    """Estrae il range dei prezzi (vendita o affitto) dalla pagina di mercato"""
    stats = market_soup.find_all("p", class_="cg-buildingPricesStats__highlighted-subtext")
    if not stats:
        return None, None
    
    # Il primo elemento è per vendita, il secondo per affitto
    target_stats = stats[0] if type == 'vendita' else stats[1]
    if not target_stats:
        return None, None
    
    # Estrai i numeri dal testo
    text = target_stats.text
    numbers = re.findall(r'[\d.,]+', text.replace('.', ''))
    if len(numbers) >= 2:
        return float(numbers[0]), float(numbers[1])
    return None, None

def get_airbnb_zone(zona_immobiliare):
    """
    Converte la zona dell'immobile nelle corrispondenti zone Airbnb
    """
    return ZONE_MAPPING.get(zona_immobiliare.lower(), [])

def analizza_airbnb_data(zona_immobiliare: str, num_locali: int, num_bagni: int, num_camere: int, df_airbnb: pd.DataFrame):
    """
    Analizza i dati Airbnb per una specifica zona e caratteristiche dell'immobile
    """
    try:
        if not zona_immobiliare:
            print("Zona immobiliare non specificata")
            return {
                'Rendita_Annua_Airbnb': 0,
                'Numero_Annunci_Airbnb_Simili': 0,
                'Appartamenti_Simili': []
            }

        # Ottieni le zone Airbnb corrispondenti
        zone_airbnb = get_airbnb_zone(zona_immobiliare)
        print(f"Cerco immobili nelle zone Airbnb: {zone_airbnb}")
        
        # Filtra il DataFrame per le zone di interesse
        df_zona = df_airbnb[df_airbnb['Zona'].isin(zone_airbnb)].copy()
        print(f"Trovati {len(df_zona)} immobili nella zona")
        
        # Converti e pulisci i dati
        df_zona['Locali'] = pd.to_numeric(df_zona['Locali'], errors='coerce')
        df_zona['Bagni'] = df_zona['Bagni'].str.extract(r'(\d+)').astype(float)
        
        # Applica i filtri per caratteristiche simili
        df_filtered = df_zona[
            (df_zona['Locali'].fillna(0) == float(num_locali)) &
            (df_zona['Bagni'].fillna(0) == float(num_bagni))
        ]
        print(f"Trovati {len(df_filtered)} immobili con caratteristiche simili")
        
        if len(df_filtered) == 0:
            return {
                'Rendita_Annua_Airbnb': 0,
                'Numero_Annunci_Airbnb_Simili': 0,
                'Appartamenti_Simili': []
            }
        
        # Calcola il prezzo medio per notte degli immobili filtrati
        prezzo_medio_notte = df_filtered['Prezzo per Notte'].mean()
        print(f"Prezzo medio per notte: €{prezzo_medio_notte:.2f}")
        
        # Trova i 5 appartamenti con il prezzo più simile alla media
        df_filtered['Differenza_Prezzo'] = abs(df_filtered['Prezzo per Notte'] - prezzo_medio_notte)
        top_5 = df_filtered.nsmallest(5, 'Differenza_Prezzo')
        
        # Calcola la rendita annua con occupancy del 70%
        occupancy_rate = 0.70  # 70% di occupazione
        rendita_annua = prezzo_medio_notte * 365 * occupancy_rate
        
        # Prepara la lista degli appartamenti simili
        appartamenti_simili = []
        for _, row in top_5.iterrows():
            appartamento = {
                'Nome': row['Nome Annuncio'],
                'Prezzo per Notte': f"€ {row['Prezzo per Notte']:.2f}",
                'Occupancy Rate': f"{row['Occupancy Rate']:.1f}%",
                'Rating': row.get('Rating', 'N/A'),
                'Link': row['Link Airbnb']
            }
            appartamenti_simili.append(appartamento)
        
        print(f"Rendita annua Airbnb stimata: €{rendita_annua:.2f}")
        
        return {
            'Rendita_Annua_Airbnb': rendita_annua,
            'Numero_Annunci_Airbnb_Simili': len(df_filtered),
            'Appartamenti_Simili': appartamenti_simili
        }
        
    except Exception as e:
        print(f"Errore nell'analisi dei dati Airbnb: {str(e)}")
        traceback.print_exc()
        return None

def analizza_immobile(data):
    """Analizza un singolo immobile partendo dal dizionario esistente"""
    global DATI
    
    def clean_price(price_str):
        if not price_str or price_str == "N/A":
            return 0
        return float(price_str.replace("€ ", "").replace(".", "").replace("/mese", ""))
    
    def clean_sqm(sqm_str):
        if not sqm_str or sqm_str == "N/A":
            return 0
        return float(sqm_str.replace(" m²", ""))
    
    mq = clean_sqm(data["SQFTS"])
    n_locali = int(data["LOCALi"]) if data["LOCALi"] != "N/A" else 1
    n_componenti = stima_componenti_da_locali(n_locali)
    
    DATI = {
        "PROPERTY": {
            "ADDRESS": data["ADDRESS"],
            "LINK": data["LINK"],
            "DESCRIPTION": data["DESCRIPTION"],
            "TIPOLOGIA": data["TIPOLOGIA"],
            "LOCALI": int(data["LOCALi"]) if data["LOCALi"] != "N/A" else 1,
            "MQ": clean_sqm(data["SQFTS"]),
            "ANNO_COSTRUZIONE": data["YEAR_BUILT"],
            "CLASSE_ENERGETICA": data["ENERGY_CLASS"],
            "GARAGE": data["GARAGE"]
        },
        "ACQUISTO": {
            "PREZZO_ACQUISTO": clean_price(data["PURCHASE_PRICE"]),
            "COSTI_RISTRUTTURAZIONE": 0,  # Da stimare
            "SPESE_NOTARILI": clean_price(data["PURCHASE_PRICE"]) * 0.03,  # 3% del prezzo
            "PROVVIGIONE_AGENZIA": clean_price(data["PURCHASE_PRICE"]) * 0.03,  # 3% del prezzo
            "IMPOSTA_REGISTRO": clean_price(data["PURCHASE_PRICE"]) * 0.02,  # 2% prima casa, 9% seconda
            "IVA": clean_price(data["PURCHASE_PRICE"]) * 0.04  # 4% prima casa da costruttore, 10% seconda casa
        },
        "FINANZIAMENTO": {
            "PERCENTUALE_ANTICIPO": 0.2,  # 20% di anticipo
            "DURATA_ANNI": 25,
            "TASSO_INTERESSE": 0.035,  # 3.5% tasso
            "SPESE_ISTRUTTORIA": 500,
            "PERIZIA": 300
        },
        "RENDITA": {
            "AFFITTO_MENSILE": clean_price(data["PURCHASE_PRICE"]) * 0.004,  # Stima 4.8% annuo
            "TASSO_SFITTO": 0.08,  # 8% tasso di sfitto
            "CEDOLARE_SECCA": 0.21  # 21% regime ordinario, 10% canone concordato
        },
        "SPESE": {
            "IMU": clean_price(data["PURCHASE_PRICE"]) * 0.0106,  # 1.06% medio
            "TARI": calcola_tari(
                mq=mq,
                n_componenti=n_componenti,
                tariffa_fissa=1.10,
                quota_provinciale=0.05
            ),
            "ASSICURAZIONE": clean_price(data["PURCHASE_PRICE"]) * 0.001,  # 0.1% annuo
            "SPESE_CONDOMINIALI": clean_price(data["MONTHLY_MAINTENANCE"]),
            "MANUTENZIONE": clean_price(data["PURCHASE_PRICE"]) * 0.01,  # 1% annuo
            "GESTIONE_AFFITTO": 0.08  # 8% del canone se in gestione
        },
        "MISC": {
            "RIVALUTAZIONE_ANNUA": 0.02  # 2% annuo
        }
    }
    
    # Calcoliamo le metriche
    risultati = {
        'indirizzo': data['ADDRESS'],
        'prezzo': clean_price(data["PURCHASE_PRICE"]),
        'mq': clean_sqm(data["SQFTS"]),
        'prezzo_mq': clean_price(data["PURCHASE_PRICE"]) / clean_sqm(data["SQFTS"]) if clean_sqm(data["SQFTS"]) > 0 else 0,
        'locali': data["LOCALi"],
        'spese_cond': clean_price(data["MONTHLY_MAINTENANCE"]),
        'rendita_lorda': (DATI["RENDITA"]["AFFITTO_MENSILE"] * 12) / clean_price(data["PURCHASE_PRICE"]),
        'rendita_netta': ((DATI["RENDITA"]["AFFITTO_MENSILE"] * 12) * (1 - DATI["RENDITA"]["CEDOLARE_SECCA"]) - 
                         DATI["SPESE"]["IMU"] - DATI["SPESE"]["TARI"] - 
                         DATI["SPESE"]["ASSICURAZIONE"] - 
                         (DATI["SPESE"]["SPESE_CONDOMINIALI"] * 12) - 
                         DATI["SPESE"]["MANUTENZIONE"]) / clean_price(data["PURCHASE_PRICE"]),
        'cash_flow_mensile': DATI["RENDITA"]["AFFITTO_MENSILE"] - 
                            (DATI["SPESE"]["IMU"] + DATI["SPESE"]["TARI"] + 
                             DATI["SPESE"]["ASSICURAZIONE"] + 
                             DATI["SPESE"]["MANUTENZIONE"]) / 12 - 
                            DATI["SPESE"]["SPESE_CONDOMINIALI"]
    }
    
    return risultati

def salva_analisi_formattata(data, output_file='analisi_immobili_updated.txt'):
    """
    Salva i dati dell'analisi in un formato leggibile
    """
    with open(output_file, 'w', encoding='utf-8') as f:
        # Prima scrivi tutti i dati principali
        for key, value in data.items():
            if key != 'Appartamenti_Simili':  # Saltiamo temporaneamente gli appartamenti simili
                if isinstance(value, float):
                    if 'prezzo' in key.lower() or 'rendita' in key.lower() or 'maintenance' in key.lower():
                        value = f"€ {value:,.2f}"
                    elif 'percentuale' in key.lower() or 'delta' in key.lower():
                        value = f"{value:.1f}%"
                
                f.write(f"{key}:\n{value}\n\n")
        
        # Poi scrivi i dettagli degli appartamenti simili su Airbnb
        if 'Appartamenti_Simili' in data and data['Appartamenti_Simili']:
            f.write("\nAPPARTAMENTI SIMILI SU AIRBNB:\n")
            f.write("=" * 40 + "\n\n")
            
            for i, app in enumerate(data['Appartamenti_Simili'], 1):
                f.write(f"Appartamento {i}:\n")
                for k, v in app.items():
                    f.write(f"{k}: {v}\n")
                f.write("\n")

def get_zone_data(listing_url):
    """
    Estrae i dati della zona partendo dall'URL dell'annuncio
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'it-IT,it;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Cache-Control': 'max-age=0'
    }
    
    try:
        # Aggiungi un delay per evitare di sovraccaricare il server
        time.sleep(2)
        
        session = requests.Session()
        response = session.get(listing_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Verifica se siamo stati reindirizzati a una pagina di errore
        if "error" in response.url.lower() or len(response.history) > 2:
            print("Possibile blocco o reindirizzamento")
            return None
            
        # Resto del codice...
        
    except requests.exceptions.RequestException as e:
        print(f"Errore nella richiesta HTTP: {str(e)}")
        return None
    except Exception as e:
        print(f"Errore generico: {str(e)}")
        return None

# Test
url = "https://www.immobiliare.it/annunci/111133703/?entryPoint=map"  # sostituisci con il tuo URL
result = get_zone_data(url)
print(f"\nRisultato: {result}")
    
def estrai_indirizzo_da_url(url_annuncio):
    """
    Non abbiamo bisogno di estrarre l'indirizzo dall'URL perché lo abbiamo già nei dati
    """
    return data['ADDRESS']

def estrai_nome_via(indirizzo):
    """
    Estrae il nome della via dall'indirizzo completo
    """
    # Converti in minuscolo e splitta per virgola
    parti = indirizzo.lower().split(',')[0]
    
    # Rimuovi prefissi comuni
    prefissi = ['trilocale', 'bilocale', 'quadrilocale', 'appartamento', 'attico']
    for prefisso in prefissi:
        if parti.startswith(prefisso):
            parti = parti.replace(prefisso, '').strip()
    
    # Per viale/piazza, prendi il nome dopo
    if "viale" in parti:
        # Splitta per "viale" e prendi la parte dopo
        nome = parti.split("viale")[1].strip()
        # Prendi solo la prima parola (il nome del viale)
        nome = nome.split()[0]
        return nome
    
    if "piazza" in parti:
        nome = parti.split("piazza")[1].strip()
        nome = nome.split()[0]
        return nome
    
    # Per via, prendi il cognome
    if "via" in parti:
        nome = parti.split("via")[1].strip()
        return nome.split()[-1]
    
    return None

def trova_corrispondenza_via(nome_via):
    """
    Trova la corrispondenza migliore per il nome della via
    """
    # Dizionario delle vie con le loro zone
    vie_zone = {
        'viale stelvio': 'Viale Stelvio',
        # ... altre vie ...
    }
    
    # Cerca corrispondenza esatta
    if nome_via in vie_zone:
        return (vie_zone[nome_via], 100.0)
    
    return None

def trova_zona_da_via(via):
    """
    Trova la zona di Milano corrispondente alla via
    """
    # Mappa delle vie alle zone
    mappa_vie_zone = {
        'Viale Stelvio': {'zona': 'cenisio-sarpi-isola', 'sottozona': 'isola'},
        # ... altre vie ...
    }
    
    return mappa_vie_zone.get(via)

def analizza_prezzi_zona(url_annuncio, df_prezzi_zone, data):
    """
    Analizza i prezzi della zona partendo dall'URL dell'annuncio
    """
    try:
        # Debug: stampa le chiavi disponibili
        print("Chiavi disponibili in data:", data.keys())
        print("Contenuto di data:", data)

        # Calcola il prezzo al metro quadro usando i nomi corretti delle chiavi
        mq_totali = float(data.get('MQ', 0))  # o 'SQFTS' a seconda del nome reale
        prezzo_totale = float(data.get('PURCHASE_PRICE', 0))
        prezzo_mq = prezzo_totale / mq_totali if mq_totali > 0 else 0
        spese_mensili = float(data.get('MONTHLY_MAINTENANCE', '0').replace('€', '').replace(',', '').strip()) if data.get('MONTHLY_MAINTENANCE') != 'N/A' else 0
        
        # Estrai l'indirizzo
        indirizzo = data['ADDRESS']
        print(f"Indirizzo trovato: {indirizzo}")
        
        # Estrai il nome della via
        nome_via = estrai_nome_via(indirizzo)
        print(f"Nome via estratto: {nome_via}")
        
        # Cerca la via nel DataFrame delle zone
        zona_trovata = None
        if nome_via:
            mask = df_prezzi_zone['indirizzo'].str.contains(nome_via, case=False, na=False)
            if mask.any():
                zona_trovata = df_prezzi_zone[mask].iloc[0]
        
        # Se non trovi la via, usa la zona
        if zona_trovata is None:
            parti = indirizzo.split(',')
            if len(parti) > 1:
                zona = parti[1].strip().lower()
                mask = df_prezzi_zone['zona'].str.contains(zona, case=False, na=False)
                if mask.any():
                    zona_trovata = df_prezzi_zone[mask].iloc[0]
        
        if zona_trovata is not None:
            prezzo_medio = float(zona_trovata['vendita_medio'])
            affitto_medio = float(zona_trovata['affitto_medio'])
            
            prezzo_teorico = mq_totali * prezzo_medio
            delta_prezzo = ((prezzo_totale - prezzo_teorico) / prezzo_teorico) * 100
            
            # Calcolo rendita
            affitto_mensile_teorico = mq_totali * affitto_medio
            rendita_annua_lorda = affitto_mensile_teorico * 12
            rendita_percentuale_lorda = (rendita_annua_lorda / prezzo_totale) * 100
            
            # Calcolo rendita netta
            spese_annue = spese_mensili * 12
            tasse_rendita = rendita_annua_lorda * 0.21  # cedolare secca 21%
            rendita_annua_netta = rendita_annua_lorda - spese_annue - tasse_rendita
            rendita_percentuale_netta = (rendita_annua_netta / prezzo_totale) * 100
            
            return {
                'Zona di Milano': zona_trovata['zona'],
                'Prezzo/m²': prezzo_mq,
                'Prezzo medio/m²': prezzo_medio,
                'Delta % su prezzo zona': delta_prezzo,
                'Prezzo teorico zona': prezzo_teorico,
                'Affitto medio/m²': affitto_medio,
                'Rendita annua lorda': rendita_annua_lorda,
                'Rendita % annua lorda': rendita_percentuale_lorda,
                'Rendita % annua netta': rendita_percentuale_netta
            }
            
        return None
        
    except Exception as e:
        print(f"Errore nell'analisi dei prezzi: {str(e)}")
        traceback.print_exc()
        return None

def aggiorna_analisi_immobile(csv_input, output_file, df_prezzi_zone, df_airbnb):
    try:
        # Leggi il CSV usando pandas invece di farlo manualmente
        data = pd.read_csv(csv_input, encoding='utf-8-sig').iloc[0].to_dict()
        
        # Debug: stampa i dati letti
        print("\nDati letti dal CSV:")
        print(data)
        
        # Analizza i prezzi della zona
        analisi = analizza_prezzi_zona(IMMOBILIARE_URL, df_prezzi_zone, data)
        
        # Aggiungi analisi Airbnb usando il nome corretto della chiave per la zona
        analisi_airbnb = analizza_airbnb_data(
            zona_immobiliare=data.get('Zona di Milano'),  # Usa il nome corretto della chiave
            num_locali=int(data.get('LOCALI', 0)),
            num_bagni=int(data.get('BATHROOMS', 0)),
            num_camere=int(data.get('BEDROOMS', 0)),
            df_airbnb=df_airbnb
        )
        
        if analisi_airbnb:
            data.update({
                'Rendita_Annua_Airbnb': analisi_airbnb.get('Rendita_Annua_Airbnb', 0),
                'Numero_Annunci_Airbnb_Simili': analisi_airbnb.get('Numero_Annunci_Simili', 0)
            })
        else:
            data.update({
                'Rendita_Annua_Airbnb': 0,
                'Numero_Annunci_Airbnb_Simili': 0
            })
        
        # Salva i dati nel nuovo formato
        salva_analisi_formattata(data, output_file)
        
        print(f"\nFile {output_file} aggiornato con successo!")
        
    except Exception as e:
        print(f"Errore nell'aggiornamento del file: {str(e)}")
        traceback.print_exc()

def main():
    try:
        print(f"\n=== ANALISI IMMOBILE ===")
        print(f"URL: {IMMOBILIARE_URL}")
        
        # Carica i dati delle zone
        df_prezzi_zone = pd.read_csv(PREZZI_ZONE_FILE)
        print("Dati zone caricati con successo")
        
        # Carica i dati Airbnb
        try:
            df_airbnb = pd.read_csv(AIRBNB_FILE)
            print(f"Dati Airbnb caricati con successo: {len(df_airbnb)} record trovati")
        except FileNotFoundError:
            print(f"ATTENZIONE: File {AIRBNB_FILE} non trovato")
            df_airbnb = pd.DataFrame()
        except Exception as e:
            print(f"Errore nel caricamento dei dati Airbnb: {str(e)}")
            df_airbnb = pd.DataFrame()
        
        # Leggi il file CSV dell'immobile
        data = pd.read_csv('analisi_immobili.csv', encoding='utf-8-sig').iloc[0].to_dict()
        
        # Debug: stampa i dati letti
        print("\nDati immobile:")
        print(data)
        
        # Analisi Airbnb
        if not df_airbnb.empty:
            print("Avvio analisi Airbnb...")
            analisi_airbnb = analizza_airbnb_data(
                zona_immobiliare=data.get('Zona di Milano'),
                num_locali=int(data.get('LOCALI', 0)),
                num_bagni=int(data.get('BATHROOMS', 0)),
                num_camere=int(data.get('BEDROOMS', 0)),
                df_airbnb=df_airbnb
            )
            
            if analisi_airbnb:
                print("Analisi Airbnb completata con successo")
                data.update(analisi_airbnb)
            else:
                print("Nessun dato Airbnb trovato per questa zona/tipologia")
        else:
            print("Analisi Airbnb saltata: nessun dato disponibile")
        
        # Salva i risultati
        salva_analisi_formattata(data, OUTPUT_FILE)
        print(f"\nAnalisi salvata in {OUTPUT_FILE}")
        
    except Exception as e:
        print(f"\nErrore durante l'esecuzione: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()
  