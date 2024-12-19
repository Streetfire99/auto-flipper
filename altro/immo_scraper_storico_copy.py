from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import pandas as pd
import time

# Inizializza il geocoder
geolocator = Nominatim(user_agent="backoffice/1.0 (https://backoffice.xeniamilano.com)")

# Aggiungi questo dizionario all'inizio del file, dopo gli import
zone_mapping = {
    "centro": "centro",
    "arco-della-pace": "arco-della-pace-arena-pagano",
    "ticinese": "genova-ticinese",
    "quadronno": "quadronno-palestro-guastalla",
    "garibaldi": "garibaldi-moscova-porta-nuova",
    "fiera-sempione": "fiera-sempione-city-life-portello",
    "navigli": "navigli",
    "porta-romana": "porta-romana-cadore-montenero",
    "porta-venezia": "porta-venezia-indipendenza",
    "centrale": "centrale-repubblica",
    "cenisio": "cenisio-sarpi-isola",
    "viale-certosa": "viale-certosa-cascina-merlata",
    "bande-nere": "bande-nere-inganni",
    "famagosta": "famagosta-barona",
    "abbiategrasso": "abbiategrasso-chiesa-rossa",
    "porta-vittoria": "porta-vittoria-lodi",
    "cimiano": "cimiano-crescenzago-adriano",
    "bicocca": "bicocca-niguarda",
    "solari": "solari-washington",
    "affori": "affori-bovisa",
    "san-siro": "san-siro-trenno",
    "bisceglie": "bisceglie-baggio-olmi",
    "ripamonti": "ripamonti-vigentino",
    "forlanini": "forlanini",
    "città-studi": "città-studi-susa",
    "maggiolina": "maggiolina-istria",
    "precotto": "precotto-turro",
    "udine": "udine-lambrate",
    "pasteur": "pasteur-rovereto",
    "ponte-lambro": "ponte-lambro-santa-giulia",
    "corvetto": "corvetto-rogoredo",
    "napoli": "napoli-soderini"
}

# Modifica la funzione get_coordinates per includere il nome esteso
def get_coordinates(zone):
    try:
        full_address = f"{zone}, Milano, Italy"
        print(f"Cercando: {full_address}")
        location = geolocator.geocode(full_address, timeout=10)
        if location:
            print(f"Trovato: {location.latitude}, {location.longitude}")
            return pd.Series({
                'zona_breve': zone,
                'zona_estesa': zone_mapping[zone],
                'latitude': location.latitude,
                'longitude': location.longitude
            })
        return pd.Series({
            'zona_breve': zone,
            'zona_estesa': zone_mapping[zone],
            'latitude': None,
            'longitude': None
        })
    except (GeocoderTimedOut, GeocoderServiceError):
        return pd.Series({
            'zona_breve': zone,
            'zona_estesa': zone_mapping[zone],
            'latitude': None,
            'longitude': None
        })
    finally:
        time.sleep(2)

# Lista delle zone di Milano
zone_milano = [
    "centro",
    "arco-della-pace",
    "ticinese",
    "quadronno",
    "garibaldi",
    "fiera-sempione",
    "navigli",
    "porta-romana",
    "porta-venezia",
    "centrale",
    "cenisio",
    "viale-certosa",
    "bande-nere",
    "famagosta",
    "abbiategrasso",
    "porta-vittoria",
    "cimiano",
    "bicocca",
    "solari",
    "affori",
    "san-siro",
    "bisceglie",
    "ripamonti",
    "forlanini",
    "città-studi",
    "maggiolina",
    "precotto",
    "udine",
    "pasteur",
    "ponte-lambro",
    "corvetto",
    "napoli"
]

# Crea una lista per memorizzare i risultati
results = []

# Geocodifica ogni zona
print("Iniziando la geocodifica delle zone...")
for n, zone in enumerate(zone_milano):
    print(f"Geocodificando zona {n+1} di {len(zone_milano)}: {zone}")
    result = get_coordinates(zone)
    results.append(result)

# Crea un DataFrame con i risultati
df_zone = pd.DataFrame(results)

# Rimuovi le righe dove non è stato possibile ottenere le coordinate
df_zone = df_zone.dropna(subset=['latitude', 'longitude'])

# Rimuovi la colonna zona_breve se vuoi solo i nomi estesi
df_zone = df_zone.drop('zona_breve', axis=1)

print(f"Geocodifica completata. Trovate coordinate per {len(df_zone)} zone.")

# Salva il dataframe
try:
    df_zone.to_csv('zone_milano_coordinates.csv', index=False)
    print("File salvato con successo!")
except Exception as e:
    print(f"Errore durante il salvataggio: {e}")
