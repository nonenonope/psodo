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

# --- TURKCE KARAKTER YONETIMI ---
def turkce_kucult(metin):
    if not isinstance(metin, str):
        return metin
    return metin.replace('İ', 'i').replace('I', 'ı').lower()

def turkce_buyut(metin):
    if not isinstance(metin, str):
        return metin
    return metin.replace('i', 'İ').replace('ı', 'I').upper()

# --- 1. DILBILIMSEL KURALLAR VE SES ENVANTERI ---
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
        havuz = KALIN_ILK_UNLULER if ilk_seslem_mi else KALIN_DIGER_UNLULER
    else:
        havuz = INCE_ILK_UNLULER if ilk_ses
