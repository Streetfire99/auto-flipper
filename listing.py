import pandas as pd
import os

def clean_listing():
    try:
        # Ottieni il percorso della directory corrente
        current_dir = os.path.dirname(os.path.abspath(__file__))
        input_file = os.path.join(current_dir, 'listing.csv')
        output_file = os.path.join(current_dir, 'listing_clean.csv')
        output_zone = os.path.join(current_dir, 'zone_milano.csv')
        
        # Lista delle zone da mantenere
        zone_da_mantenere = [
            'DUOMO', 'PAGANO', 'TICINESE', 'GUASTALLA', 'BRERA', 
            'GARIBALDI REPUBBLICA', 'TRE TORRI', 'PARCO SEMPIONE', 'PORTELLO',
            'NAVIGLI', 'TORTONA', 'PORTA ROMANA', 'SCALO ROMANA',
            'BUENOS AIRES - VENEZIA', 'GIARDINI PORTA VENEZIA', 'CENTRALE',
            'SARPI', 'ISOLA', 'FARINI', 'GHISOLFA', 'QT 8', 'SACCO',
            'VILLAPIZZONE', 'GALLARATESE', 'BANDE NERE', 'SELINUNTE',
            'BARONA', 'S. CRISTOFORO', 'RONCHETTO DELLE RANE',
            'RONCHETTO SUL NAVIGLIO', 'GRATOSOGLIO - TICINELLO',
            'UMBRIA - MOLISE', 'ORTOMERCATO', 'XXII MARZO', 'ADRIANO',
            'PARCO LAMBRO - CIMIANO', 'BICOCCA', "NIGUARDA - CA' GRANDA",
            'PARCO NORD', 'WASHINGTON', 'DE ANGELI - MONTE ROSA', 'AFFORI',
            'BOVISA', 'COMASINA', 'S. SIRO', 'FIGINO', 'TRENNO',
            'QUARTO CAGNINO', 'QUINTO ROMANO', 'BAGGIO', 'RIPAMONTI',
            'QUINTOSOLE', 'CHIARAVALLE', 'PARCO FORLANINI - ORTICA',
            'MECENATE', "CITTA' STUDI", 'MACIACHINI - MAGGIOLINA',
            'GRECO', 'LAMBRATE'
        ]
        
        print(f"Cercando il file in: {input_file}")
        
        # Leggi il CSV originale
        df = pd.read_csv(input_file)
        
        # Seleziona solo le colonne che ci interessano
        colonne_da_mantenere = [
            'listing_url', 'name', 'neighbourhood_cleansed', 'room_type',
            'accommodates', 'bathrooms_text', 'bedrooms', 'price',
            'picture_url', 'availability_365', 'review_scores_rating'
        ]
        
        # Crea nuovo DataFrame con solo le colonne selezionate
        df_clean = df[colonne_da_mantenere].copy()
        
        # Rinomina le colonne per maggiore chiarezza
        df_clean = df_clean.rename(columns={
            'listing_url': 'Link Airbnb',
            'name': 'Nome Annuncio',
            'neighbourhood_cleansed': 'Zona',
            'room_type': 'Tipo Alloggio',
            'accommodates': 'Posti Letto',
            'bathrooms_text': 'Bagni',
            'bedrooms': 'Locali',
            'price': 'Prezzo per Notte',
            'picture_url': 'URL Foto',
            'availability_365': 'Giorni Disponibili Anno',
            'review_scores_rating': 'Rating'
        })
        
        # Filtra solo le zone specificate
        df_clean = df_clean[df_clean['Zona'].isin(zone_da_mantenere)]
        
        # Calcola l'occupancy rate
        df_clean['Occupancy Rate'] = 100 - (df_clean['Giorni Disponibili Anno'] / 365 * 100)
        
        # Pulisci il prezzo
        df_clean['Prezzo per Notte'] = df_clean['Prezzo per Notte'].str.replace('$', '').str.replace(',', '').astype(float)
        
        # Ordina per zona in ordine alfabetico
        df_clean = df_clean.sort_values('Zona')
        
        # Riorganizza le colonne nell'ordine desiderato
        colonne_ordinate = [
            'Zona',
            'Link Airbnb',
            'Nome Annuncio',
            'Tipo Alloggio',
            'Locali',
            'Bagni',
            'Posti Letto',
            'Prezzo per Notte',
            'Occupancy Rate',
            'Rating',
            'URL Foto'
        ]
        
        df_clean = df_clean[colonne_ordinate]
        
        # Crea e salva il file delle zone uniche effettivamente presenti
        zone_presenti = pd.DataFrame(df_clean['Zona'].unique(), columns=['Zone di Milano'])
        zone_presenti = zone_presenti.sort_values('Zone di Milano')
        zone_presenti.to_csv(output_zone, index=False)
        
        # Salva il file principale
        df_clean.to_csv(output_file, index=False)
        
        print(f"\nFile {output_file} creato con successo!")
        print(f"File {output_zone} creato con successo!")
        print("\nPrime righe del file pulito (ordinate per zona):")
        print(df_clean.head())
        print(f"\nNumero totale di annunci: {len(df_clean)}")
        
        print("\nRiepilogo annunci per zona:")
        zone_count = df_clean['Zona'].value_counts().sort_index()
        print(zone_count)
        print(f"\nNumero totale di zone: {len(zone_count)}")
        
    except Exception as e:
        print(f"Errore durante la pulizia del file: {str(e)}")

if __name__ == "__main__":
    clean_listing()
