#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Questo script analizza i numeri relativi ad un investimento immobiliare
e calcola diversi indicatori di flusso di cassa, redditività ed altri parametri utili.

Le analisi sono state adattate al contesto del mercato immobiliare italiano.
Ad esempio, si considerano costi come spese notarili, tasse di registro, IMU, TARI 
e l'eventuale cedolare secca sugli affitti.
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
    file_dati = 'data_file.yml'

PREFISSO_OUTPUT = 'https://raw.githubusercontent.com/xiaotdl/rental_property_deal_analysis/master/'
CARTELLA_OUTPUT = 'result'
SCRIVI_IN_CARTELLA_OUTPUT = False
if len(sys.argv) >= 3 and sys.argv[2]:
    SCRIVI_IN_CARTELLA_OUTPUT = True

DATI = None
print("Input: %s" % (PREFISSO_OUTPUT + file_dati))
with open(file_dati, 'r') as f:
    try:
        DATI = yaml.load(f, Loader=yaml.SafeLoader)
    except yaml.YAMLError as e:
        print("ERRORE nella lettura del file YAML: %s" % e)


def arrotonda_alto(f):
    return int(math.ceil(f))

def arrotonda_basso(f):
    return int(f)

def mostra(classe, debug=False, stream=sys.stdout):
    stream.write("== %s ==\n" % getattr(classe, "_%s__nome" % classe.__name__))
    if classe.__dict__.get("_%s__ordine_attributi" % classe.__name__) and not debug:
        attributi = getattr(classe, "_%s__ordine_attributi" % classe.__name__)
    else:
        attributi = sorted(classe.__dict__.keys())
    for attributo in attributi:
        if not attributo.startswith('__') and not attributo.startswith("_" + classe.__name__):
            valore = getattr(classe, attributo)
            if not callable(valore):
                if not debug:
                    attributo = re.sub(r"^_", "", attributo)
                    attributo = re.sub(r"_FMT$", "", attributo)
                stream.write("%s: %s\n" % (attributo, valore))
    stream.write("\n")

def calcola_rata_mensile_mutuo(importo, anni, tasso_apr):
    """
    Calcola la rata mensile del mutuo (quota capitale e interessi).
    Formula standard per ammortamento a rata costante.
    """
    MESI_PER_ANNO = 12
    c = tasso_apr / MESI_PER_ANNO
    n = MESI_PER_ANNO * anni
    rata_mensile = importo * (c * (1 + c)**n) / ((1 + c)**n - 1)
    return arrotonda_alto(rata_mensile)

def calcola_debito_residuo_mutuo(importo, anni, tasso_apr, anni_passati):
    """
    Calcola il debito residuo del mutuo dopo un certo numero di anni.
    """
    MESI_PER_ANNO = 12
    c = tasso_apr / MESI_PER_ANNO
    n = MESI_PER_ANNO * anni
    p = MESI_PER_ANNO * anni_passati
    debito = importo * ((1 + c)**n - (1 + c)**p) / ((1 + c)**n - 1)
    return arrotonda_alto(debito)


class Immobile(object):
    """
    DETTAGLI IMMOBILE: Informazioni sulle caratteristiche dell'immobile 
    (indirizzo, descrizione, numero di vani, superficie, ecc.)
    """
    __nome = 'IMMOBILE'
    __fonte = ['venditore', 'Catasto/Conservatoria locale']
    __ordine_attributi = [
        'INDIRIZZO',
        'LINK',
        'DESCRIZIONE',
        'CAMERE',
        'BAGNI',
        'UNITA',
        'MQ',
    ]

    INDIRIZZO = DATI["PROPERTY"]["ADDRESS"]
    LINK = DATI["PROPERTY"]["LINK"]
    DESCRIZIONE = DATI["PROPERTY"]["DESCRIPTION"]
    CAMERE = DATI["PROPERTY"]["BEDROOMS"]
    BAGNI = DATI["PROPERTY"]["BATHROOMS"]
    UNITA = DATI["PROPERTY"]["UNITS"]
    MQ = DATI["PROPERTY"]["SQFTS"]


class Acquisto(object):
    """
    DETTAGLI DELL'ACQUISTO: Costi relativi all'acquisto, 
    come prezzo, spese di ristrutturazione, notarili, registro, agenzia, ecc.
    """
    __nome = 'ACQUISTO'
    __fonte = ['venditore', 'controllo tecnico', 'notaio']
    __ordine_attributi = [
        'PREZZO_ACQUISTO',
        'COSTO_RISTRUTTURAZIONE',
        'COSTO_CHIUSURA',
        'SPESE_NOTARILI',
        'PROVVIGIONE_AGENZIA',
        'TASSA_REGISTRO',
        '_COSTO_TOTALE',
    ]

    PREZZO_ACQUISTO = DATI["PURCHASE"]["PURCHASE_PRICE"]
    COSTO_RISTRUTTURAZIONE = DATI["PURCHASE"]["IMPROVEMENT_COST"]
    COSTO_CHIUSURA = DATI["PURCHASE"]["CLOSING_COST"]
    SPESE_NOTARILI = DATI["PURCHASE"].get("NOTARY_FEES", 0)
    PROVVIGIONE_AGENZIA = DATI["PURCHASE"].get("AGENCY_FEES", 0)
    TASSA_REGISTRO = DATI["PURCHASE"].get("REGISTRATION_TAX", 0)

    COSTO_POSSESSO_PRE_AFFITTO = 0 # Eventuali costi prima di affittare

    _COSTO_TOTALE = (PREZZO_ACQUISTO + COSTO_RISTRUTTURAZIONE + COSTO_CHIUSURA 
                     + SPESE_NOTARILI + PROVVIGIONE_AGENZIA + TASSA_REGISTRO 
                     + COSTO_POSSESSO_PRE_AFFITTO)


class Finanziamento(object):
    """
    FINANZIAMENTO: Dettagli del mutuo (importo, anticipo, tasso, durata).
    """
    __nome = 'FINANZIAMENTO'
    __fonte = ['banca', 'broker mutuo']
    __ordine_attributi = [
        '_PERCENTUALE_ANTICIPO_MUTUO_FMT',
        '_IMPORTO_ANTICIPO_MUTUO',
        '_IMPORTO_MUTUO',
        'ANNI_MUTUO',
        '_TASSO_MUTUO_FMT',
        '_RATA_MENSILE_MUTUO',
        '_ESBORSO_TOTALE_CONTANTI',
    ]

    PERCENTUALE_ANTICIPO_MUTUO = DATI["FINANCING"]["MORTGAGE_LOAN_DOWNPAY_PERCENTAGE"]
    _PERCENTUALE_ANTICIPO_MUTUO_FMT = "%.2f%%" % (PERCENTUALE_ANTICIPO_MUTUO * 100)
    _IMPORTO_ANTICIPO_MUTUO = arrotonda_alto(Acquisto.PREZZO_ACQUISTO * PERCENTUALE_ANTICIPO_MUTUO)

    _IMPORTO_MUTUO = arrotonda_alto(Acquisto.PREZZO_ACQUISTO * (1 - PERCENTUALE_ANTICIPO_MUTUO))
    ANNI_MUTUO = DATI["FINANCING"]["MORTGAGE_LOAN_YRS"]
    TASSO_MUTUO = DATI["FINANCING"]["MORTGAGE_LOAN_APR"]
    _TASSO_MUTUO_FMT = "%.2f%%" % (TASSO_MUTUO * 100) 
    _RATA_MENSILE_MUTUO = calcola_rata_mensile_mutuo(_IMPORTO_MUTUO, ANNI_MUTUO, TASSO_MUTUO)
    _RATA_ANNUALE_MUTUO = _RATA_MENSILE_MUTUO * 12

    _ESBORSO_TOTALE_CONTANTI = (_IMPORTO_ANTICIPO_MUTUO + Acquisto.COSTO_RISTRUTTURAZIONE 
                                + Acquisto.COSTO_CHIUSURA + Acquisto.SPESE_NOTARILI 
                                + Acquisto.PROVVIGIONE_AGENZIA + Acquisto.TASSA_REGISTRO)


class Reddito(object):
    """
    REDDITO: Entrate generate dall'immobile (affitto, altre entrate),
    tenendo conto del tasso di sfitto (vacancy rate).
    """
    __nome = "REDDITO"
    __fonte = ['stima pro-forma', 'agenzia / amministratore']
    __ordine_attributi = [
        'AFFITTO_MENSILE',
        '_TASSO_SFITTO_FMT',
        '_AFFITTO_NETTO_MENSILE',
        'ALTRE_ENTRATE_MENSILI',
        '_ENTRATE_LORDE_MENSILI',
        '_ENTRATE_LORDE_ANNUALI',
    ]

    AFFITTO_MENSILE = DATI["INCOME"]["MONTHLY_RENT"]
    TASSO_SFITTO = DATI["INCOME"]["VACANCY_RATE"]
    _TASSO_SFITTO_FMT = "%.2f%%" % (TASSO_SFITTO * 100)
    _AFFITTO_NETTO_MENSILE = arrotonda_alto(AFFITTO_MENSILE * (1 - TASSO_SFITTO))
    _AFFITTO_NETTO_ANNUALE = _AFFITTO_NETTO_MENSILE * 12

    ALTRE_ENTRATE_MENSILI = DATI["INCOME"]["MONTHLY_OTHER_INCOME"]
    _ALTRE_ENTRATE_ANNUALI = ALTRE_ENTRATE_MENSILI * 12

    _ENTRATE_LORDE_MENSILI = _AFFITTO_NETTO_MENSILE + ALTRE_ENTRATE_MENSILI
    _ENTRATE_LORDE_ANNUALI = _ENTRATE_LORDE_MENSILI * 12


class Spese(object):
    """
    SPESE: Costi di gestione (amministrazione, IMU, assicurazione,
    manutenzione, utenze, pubblicità, ecc.)
    """
    __nome = "SPESE"
    __fonte = ['stima pro-forma', 'amministratore condominiale', 'commercialista']
    __ordine_attributi = [
        '_PERCENTUALE_GESTIONE_FMT',
        '_COSTO_GESTIONE_MENSILE',
        '_ALIQUOTA_IMU_FMT',
        '_IMU_MENSILE',
        'ASSICURAZIONE_MENSILE',
        'SPESE_CONDOMINIALI_MENSILI',
        'MANUTENZIONE_MENSILE',
        'UTENZE_MENSILI',
        'PUBBLICITA_MENSILE',
        'GIARDINAGGIO_MENSILE',
        '_SPESE_MENSILI_TOTALI',
        '_SPESE_ANNUALI_TOTALI',
    ]

    PERCENTUALE_GESTIONE = DATI["EXPENSES"]["PROPERTY_MANAGEMENT_FEE_RATE"]
    _PERCENTUALE_GESTIONE_FMT = "%.2f%%" % (PERCENTUALE_GESTIONE * 100)
    _COSTO_GESTIONE_MENSILE = int(math.ceil(PERCENTUALE_GESTIONE * Reddito._AFFITTO_NETTO_MENSILE))
    _COSTO_GESTIONE_ANNUALE = _COSTO_GESTIONE_MENSILE * 12

    ALIQUOTA_IMU = DATI["EXPENSES"]["PROPERTY_TAX_RATE"]
    _ALIQUOTA_IMU_FMT = "%.2f%%" % (ALIQUOTA_IMU * 100)
    _IMU_ANNUALE = arrotonda_alto(ALIQUOTA_IMU * Acquisto.PREZZO_ACQUISTO)
    _IMU_MENSILE = arrotonda_alto(_IMU_ANNUALE / 12)

    ASSICURAZIONE_MENSILE = DATI["EXPENSES"].get("MONTHLY_INSURANCE", 0)
    _ASSICURAZIONE_ANNUALE = ASSICURAZIONE_MENSILE * 12

    SPESE_CONDOMINIALI_MENSILI = DATI["EXPENSES"]["MONTHLY_HOA"]
    _SPESE_CONDOMINIALI_ANNUALI = SPESE_CONDOMINIALI_MENSILI * 12

    MANUTENZIONE_MENSILE = DATI["EXPENSES"]["MONTHLY_MAINTENANCE"]
    _MANUTENZIONE_ANNUALE = MANUTENZIONE_MENSILE * 12

    UTENZE_MENSILI = DATI["EXPENSES"]["MONTHLY_UTILITIES"]
    _UTENZE_ANNUALI = UTENZE_MENSILI * 12

    PUBBLICITA_MENSILE = DATI["EXPENSES"]["MONTHLY_ADVERTISING"]
    _PUBBLICITA_ANNUALE = PUBBLICITA_MENSILE * 12

    GIARDINAGGIO_MENSILE = DATI["EXPENSES"]["MONTHLY_LANDSCAPING"]
    _GIARDINAGGIO_ANNUALE = GIARDINAGGIO_MENSILE * 12

    _SPESE_ANNUALI_TOTALI = (
        _COSTO_GESTIONE_ANNUALE +
        _IMU_ANNUALE +
        _ASSICURAZIONE_ANNUALE +
        _SPESE_CONDOMINIALI_ANNUALI +
        _MANUTENZIONE_ANNUALE +
        _UTENZE_ANNUALI +
        _PUBBLICITA_ANNUALE +
        _GIARDINAGGIO_ANNUALE
    )
    _SPESE_MENSILI_TOTALI = arrotonda_alto(_SPESE_ANNUALI_TOTALI / 12)


class Varie(object):
    """
    VARIE: Tassi di rivalutazione dell'immobile, accrescimento dell'equity,
    o altri parametri non inclusi in altre categorie.
    """
    __nome = "VARIE"
    __fonte = ['assunzione']
    __ordine_attributi = [
        '_TASSO_RIVALUTAZIONE_FMT',
        '_IMPORTO_RIVALUTAZIONE',
        '_ACCRESCIMENTO_EQUITY',
    ]

    TASSO_RIVALUTAZIONE = DATI["MISC"]["PROPERTY_APPRECIATION_RATE"]
    _TASSO_RIVALUTAZIONE_FMT = "%.2f%%" % (TASSO_RIVALUTAZIONE * 100)
    _IMPORTO_RIVALUTAZIONE = arrotonda_alto(TASSO_RIVALUTAZIONE * Acquisto._COSTO_TOTALE)
    _ACCRESCIMENTO_EQUITY = (
        Finanziamento._IMPORTO_MUTUO -
        calcola_debito_residuo_mutuo(
            Finanziamento._IMPORTO_MUTUO,
            Finanziamento.ANNI_MUTUO,
            Finanziamento.TASSO_MUTUO,
            1
        )
    )


class Metriche(object):
    """
    METRICHE: Calcola vari indicatori come prezzo al mq, CAP rate,
    flusso di cassa (cash flow), DSCR, ROI, ecc.
    """
    __nome = "METRICHE"
    __fonte = ['calcolo']
    __ordine_attributi = [
        '_PREZZO_PER_MQ',
        '_COSTO_PER_UNITA',
        '_NOI',
        '_CASH_FLOW',
        '_CASH_FLOW_MENSILE',
        '_DSCR_FMT',
        '_CAP_RATE_FMT',
        '_CASH_ROI_FMT',
        '_TOTAL_ROI_FMT',
    ]

    _PREZZO_PER_MQ = arrotonda_alto(Acquisto._COSTO_TOTALE / Immobile.MQ)
    _COSTO_PER_UNITA = arrotonda_alto(Acquisto._COSTO_TOTALE / Immobile.UNITA)

    # NOI = Entrate Lorde Annue - Spese Annue
    _NOI = Reddito._ENTRATE_LORDE_ANNUALI - Spese._SPESE_ANNUALI_TOTALI

    # CASH_FLOW = NOI - Pagamento annuale mutuo
    _CASH_FLOW = _NOI - Finanziamento._RATA_ANNUALE_MUTUO
    _CASH_FLOW_MENSILE = arrotonda_basso(_CASH_FLOW / 12)

    # DSCR = NOI / Pagamento annuale del mutuo
    _DSCR = _NOI / Finanziamento._RATA_ANNUALE_MUTUO
    _DSCR_FMT = "%.2f%%" % (_DSCR * 100)

    # CAP_RATE = NOI / Costo Totale
    _CAP_RATE = _NOI / Acquisto._COSTO_TOTALE
    _CAP_RATE_FMT = "%.2f%%" % (_CAP_RATE * 100)

    # CASH ROI = (Cash Flow / Esborso Totale Contanti)
    _CASH_ROI = _CASH_FLOW / Finanziamento._ESBORSO_TOTALE_CONTANTI
    _CASH_ROI_FMT = "%.2f%%" % (_CASH_ROI * 100)

    # Conseguenze fiscali non calcolate
    CONSEGUENZE_FISCALI = 0

    # TOTAL ROI = (Cash Flow + Rivalutazione + Equity + Fiscalità) / Esborso Contanti
    _TOTAL_ROI = (_CASH_FLOW + Varie._IMPORTO_RIVALUTAZIONE + Varie._ACCRESCIMENTO_EQUITY + CONSEGUENZE_FISCALI) / Finanziamento._ESBORSO_TOTALE_CONTANTI
    _TOTAL_ROI_FMT = "%.2f%%" % (_TOTAL_ROI * 100)


class Sintesi(object):
    """
    SINTESI: Riepiloga i parametri chiave (rapporto canone/prezzo, NOI, cash flow, CAP rate, ROI, ecc.)
    """
    __nome = "SINTESI"
    __ordine_attributi = [
        'RAPPORTO_AFFITTO_PREZZO',
        'PREZZO_ACQUISTO',
        'COSTO_TOTALE',
        'ESBORSO_TOTALE_CONTANTI',
        'ENTRATE_LORDE_ANNUALI',
        'SPESE_ANNUALI',
        'NOI',
        'RATA_ANNUALE_MUTUO',
        'CASH_FLOW_ANNUALE',
        'CAP_RATE',
        'CASH_ROI',
        'TOTAL_ROI',
    ]

    RAPPORTO_AFFITTO_PREZZO = "%.2f%%" % (Reddito.AFFITTO_MENSILE / Acquisto.PREZZO_ACQUISTO * 100)

    PREZZO_ACQUISTO = Acquisto.PREZZO_ACQUISTO
    COSTO_TOTALE = Acquisto._COSTO_TOTALE
    ESBORSO_TOTALE_CONTANTI = Finanziamento._ESBORSO_TOTALE_CONTANTI

    ENTRATE_LORDE_ANNUALI = '+%s' % Reddito._ENTRATE_LORDE_ANNUALI
    SPESE_ANNUALI = '-%s' % Spese._SPESE_ANNUALI_TOTALI
    NOI = Metriche._NOI
    RATA_ANNUALE_MUTUO = '-%s' % Finanziamento._RATA_ANNUALE_MUTUO
    CASH_FLOW_ANNUALE = Metriche._CASH_FLOW

    CAP_RATE = Metriche._CAP_RATE_FMT
    CASH_ROI = Metriche._CASH_ROI_FMT
    TOTAL_ROI = Metriche._TOTAL_ROI_FMT


def principale():
    flusso = sys.stdout
    if SCRIVI_IN_CARTELLA_OUTPUT:
        nome_file_output = os.path.splitext(os.path.basename(file_dati))[0] + '.txt'
        percorso_output = os.path.join(CARTELLA_OUTPUT, nome_file_output)
        flusso = open(percorso_output, 'w')
        print("Output: %s" % (PREFISSO_OUTPUT + percorso_output))

    mostra(Immobile, stream=flusso)
    mostra(Acquisto, stream=flusso)
    mostra(Reddito, stream=flusso)
    mostra(Spese, stream=flusso)
    mostra(Finanziamento, stream=flusso)
    mostra(Varie, stream=flusso)
    mostra(Metriche, stream=flusso)
    mostra(Sintesi, stream=flusso)

    if SCRIVI_IN_CARTELLA_OUTPUT:
        flusso.close()

    sys.exit(0)


if __name__ == '__main__':
    principale()
