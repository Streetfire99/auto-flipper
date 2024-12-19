#!/usr/bin/env python
"""
Questo script elabora numeri e calcola le statistiche del flusso di cassa.

REF: https://www.biggerpockets.com/renewsblog/2010/06/30/introduction-to-real-estate-analysis-investing/
"""
from __future__ import division
import os
import re
import sys
import math
import yaml

if len(sys.argv) >= 2:
    file_dati = sys.argv[1]
else:
    file_dati = 'file_dati.yml'

PREFISSO_OUTPUT = 'https://raw.githubusercontent.com/xiaotdl/rental_property_deal_analysis/master/'
CARTELLA_OUTPUT = 'risultato'
SCRIVI_NELLA_CARTELLA_OUTPUT = False
if len(sys.argv) >= 3 and sys.argv[2]:
    SCRIVI_NELLA_CARTELLA_OUTPUT = True

DATI = None
print("input: %s" % PREFISSO_OUTPUT + file_dati)
with open(file_dati, 'r') as f:
    try:
        DATI = yaml.load(f, Loader=yaml.SafeLoader)
    except yaml.YAMLError as e:
        print("ERRORE: %s" % e)

def arrotonda_in_alto(f):
    return int(math.ceil(f))

def arrotonda_in_basso(f):
    return int(f)

def mostra(classe, debug=False, stream=sys.stdout):
    stream.write("== %s ==\n" % getattr(classe, "_%s__nome" % classe.__name__))
    if classe.__dict__.get("_%s__ordine_attributi" % classe.__name__) and not debug:
        attributi = getattr(classe, "_%s__ordine_attributi" % classe.__name__)
    else:
        attributi = sorted(classe.__dict__.keys())
    for attr in attributi:
        if not attr.startswith('__') and not attr.startswith("_"+classe.__name__):
            valore = getattr(classe, attr)
            if not callable(valore):
                if not debug:
                    attr = re.sub(r"^_", "", attr)
                    attr = re.sub(r"_FMT$", "", attr)
                stream.write("%s: %s\n" % (attr, valore))
    stream.write("\n")

def calcola_pagamento_mutuo_mensile(prestito, anni, tasso):
    MESI_PER_ANNO = 12
    c = tasso / MESI_PER_ANNO
    n = MESI_PER_ANNO * anni
    pagamento_mensile = prestito * (c * (1 + c)**n) / ((1 + c)**n - 1)
    return arrotonda_in_alto(pagamento_mensile)

def calcola_saldo_mutuo(prestito, anni, tasso, anni_trascorsi):
    MESI_PER_ANNO = 12
    c = tasso / MESI_PER_ANNO
    n = MESI_PER_ANNO * anni
    p = MESI_PER_ANNO * anni_trascorsi
    saldo = prestito * ((1 + c)**n - (1 + c)**p) / ((1 + c)**n - 1)
    return arrotonda_in_alto(saldo)

class Proprietà(object):
    __nome = 'PROPRIETÀ'
    __sorgente = ['venditore', 'catasto']
    __ordine_attributi = ['INDIRIZZO', 'LINK', 'DESCRIZIONE', 'CAMERE', 'BAGNI', 'UNITÀ', 'METRI_QUADRATI']

    INDIRIZZO = DATI["PROPERTY"]["ADDRESS"]
    LINK = DATI["PROPERTY"]["LINK"]
    DESCRIZIONE = DATI["PROPERTY"]["DESCRIPTION"]
    CAMERE = DATI["PROPERTY"]["BEDROOMS"]
    BAGNI = DATI["PROPERTY"]["BATHROOMS"]
    UNITÀ = DATI["PROPERTY"]["UNITS"]
    METRI_QUADRATI = DATI["PROPERTY"]["SQFTS"]

class Acquisto(object):
    __nome = 'ACQUISTO'
    __ordine_attributi = ['PREZZO_ACQUISTO', 'COSTO_RISTRUTTURAZIONE', 'COSTO_CHIUSURA', 'TOTALE_COSTO']

    PREZZO_ACQUISTO = DATI["PURCHASE"]["PURCHASE_PRICE"]
    COSTO_RISTRUTTURAZIONE = DATI["PURCHASE"]["IMPROVEMENT_COST"]
    COSTO_CHIUSURA = DATI["PURCHASE"]["CLOSING_COST"]
    TOTALE_COSTO = PREZZO_ACQUISTO + COSTO_RISTRUTTURAZIONE + COSTO_CHIUSURA

class Reddito(object):
    __nome = 'REDDITO'
    __ordine_attributi = ['AFFITTO_MENSILE', '_TASSO_VUOTO_FMT', '_AFFITTO_NETTO_MENSILE', '_REDDITO_ANNUALE']

    AFFITTO_MENSILE = DATI["INCOME"]["MONTHLY_RENT"]
    TASSO_VUOTO = DATI["INCOME"]["VACANCY_RATE"]
    _TASSO_VUOTO_FMT = "%.2f%%" % (TASSO_VUOTO * 100)
    _AFFITTO_NETTO_MENSILE = arrotonda_in_alto(AFFITTO_MENSILE * (1 - TASSO_VUOTO))
    _REDDITO_ANNUALE = _AFFITTO_NETTO_MENSILE * 12

class Spese(object):
    __nome = 'SPESE'
    __ordine_attributi = ['GESTIONE_PROPRIETÀ_FMT', '_SPESE_TOT_MENSILI', '_SPESE_TOT_ANNUALI']

    GESTIONE_PROPRIETÀ = DATI["EXPENSES"]["PROPERTY_MANAGEMENT_FEE_RATE"]
    GESTIONE_PROPRIETÀ_FMT = "%.2f%%" % (GESTIONE_PROPRIETÀ * 100)
    _SPESE_TOT_ANNUALI = arrotonda_in_alto(GESTIONE_PROPRIETÀ * Reddito._REDDITO_ANNUALE)
    _SPESE_TOT_MENSILI = arrotonda_in_alto(_SPESE_TOT_ANNUALI / 12)

class Metriche(object):
    __nome = 'METRICHE'
    __ordine_attributi = ['COSTO_UNITARIO', 'NOI', 'FLUSSO_DI_CASSA']

    COSTO_UNITARIO = arrotonda_in_alto(Acquisto.TOTALE_COSTO / Proprietà.UNITÀ)
    NOI = Reddito._REDDITO_ANNUALE - Spese._SPESE_TOT_ANNUALI
    FLUSSO_DI_CASSA = NOI

def principale():
    stream = sys.stdout
    if SCRIVI_NELLA_CARTELLA_OUTPUT:
        nome_file_output = os.path.splitext(os.path.basename(file_dati))[0] + '.txt'
        file_output = os.path.join(CARTELLA_OUTPUT, nome_file_output)
        stream = open(file_output, 'w')
        print("output: %s" % PREFISSO_OUTPUT+file_output)

    mostra(Proprietà, stream=stream)
    mostra(Acquisto, stream=stream)
    mostra(Reddito, stream=stream)
    mostra(Spese, stream=stream)
    mostra(Metriche, stream=stream)

    if SCRIVI_NELLA_CARTELLA_OUTPUT:
        stream.close()

    sys.exit(0)

if __name__ == '__main__':
    principale()
