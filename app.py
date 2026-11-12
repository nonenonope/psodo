import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

st.set_page_config(
    page_title="Yalancı Sözcük ve Sözcüksel Seçim Deneyi",
    layout="wide"
)

# --- TÜRKÇE KARAKTER YÖNETİMİ ---
def turkce_kucult(metin):
    if not isinstance(metin, str):
        return metin
    return metin.replace('İ', 'i').replace('I', 'ı').lower()

def turkce_buyut(metin):
    if not isinstance(metin, str):
        return metin
    return metin.replace('i', 'İ').replace('ı', 'I').upper()

# --- 1. DİLBİLİMSEL KURALLAR VE SES ENVANTERİ ---
KALIN_ILK_UNLULER = ['a', 'ı', 'o', 'u']
KALIN_DIGER_UNLULER = ['a', 'ı', 'u']
INCE_ILK_UNLULER = ['e', 'i', 'ö', 'ü']
INCE_DIGER_UNLULER = ['e', 'i', 'ü']
TUM_UNLULER = ['a', 'ı', 'o', 'u', 'e', 'i', 'ö', 'ü']

BASLANGIC_UNSUZLERI = [
    'b', 'c', 'ç', 'd', 'f', 'g', 'h', 'k', 'l',
    'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
IC_UNSUZLER = [
    'b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'k', 'l',
    'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
SON_UNSUZLER = [
    'ç', 'f', 'ğ', 'h', 'k', 'l', 'm', 'n',
    'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
TUM_UNSUZLER = IC_UNSUZLER + ['j']
SERT_UNSUZLER = ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş']

TURKCE_SON_UNSUZ_OBEKLERI = [
    "lk", "lp", "lt", "lç", "nk", "nt", "nç",
    "rk", "rp", "rt", "rç", "rs", "rş", "st", "şt", "kt", "ft"
]

GERCEK_SOZCUKLER = [
    "masa", "kalem", "defter", "çanta", "kapı", "güneş",
    "deniz", "kitap", "bardak", "yıldız", "orman", "kedi"
]

def unlu_sec(unlu_tipi, ilk_seslem_mi):
    if unlu_tipi == "kalin":
        if ilk_seslem_mi:
            havuz = KALIN_ILK_UNLULER
        else:
            havuz = KALIN_DIGER_UNLULER
    else:
        if ilk_seslem_mi:
            havuz = INCE_ILK_UNLULER
        else:
            havuz = INCE_DIGER_UNLULER
    return random.choice(havuz)

def sonses_sec(son_seslem_mi):
    if son_seslem_mi:
        havuz = SON_UNSUZLER
    else:
        havuz = IC_UNSUZLER
    agirliklar = [1 if u == 'ğ' else 5 for u in havuz]
    return random.choices(havuz, weights=agirliklar)[0]

def hece_uret(
    unlu_tipi,
    onceki_son_harf_tipi,
    ardisik_unsuz_sayisi,
    ilk_seslem_mi,
    son_seslem_mi,
    ileri_seslem=False
):
    unlu = unlu_sec(unlu_tipi, ilk_seslem_mi)
    if ilk_seslem_mi:
        onses_havuzu = BASLANGIC_UNSUZLERI
    else:
        onses_havuzu = IC_UNSUZLER

    if onceki_son_harf_tipi == "unlu":
        if ileri_seslem:
            yapilar = ["CV", "CVC", "CVCC"]
            secilen_yapi = random.choices(yapilar, weights=[50, 38, 12])[0]
        else:
            yapilar = ["CV", "CVC"]
            secilen_yapi = random.choices(yapilar, weights=[55, 45])[0]
    elif ardisik_unsuz_sayisi >= 2:
        yapilar = ["VC", "V"]
        secilen_yapi = random.choices(yapilar, weights=[70, 30
