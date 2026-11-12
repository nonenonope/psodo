import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

st.set_page_config(page_title="Yalancı Sözcük ve Sözcüksel Seçim Deneyi", layout="wide")

# --- TÜRKÇE KARAKTER YÖNETİMİ ---
def turkce_kucult(metin):
    if not isinstance(metin, str):
        return metin
    return metin.replace("İ", "i").replace("I", "ı").lower()

def turkce_buyut(metin):
    if not isinstance(metin, str):
        return metin
    return metin.replace("i", "İ").replace("ı", "I").upper()

# --- 1. DİLBİLİMSEL KURALLAR VE SES ENVANTERİ ---
KALIN_UNLULER = ["a", "ı", "o", "u"]
INCE_UNLULER = ["e", "i", "ö", "ü"]
UNSUZLER = ["b", "c", "ç", "d", "f", "g", "ğ", "h", "j", "k", "l", "m", "n", "p", "r", "s", "ş", "t", "v", "y", "z"]
SERT_UNSUZLER = ["p", "ç", "t", "k", "f", "h", "s", "ş"]
UNLU_4LU = {"a": "ı", "ı": "ı", "e": "i", "i": "i", "o": "u", "u": "u", "ö": "ü", "ü": "ü"}
GERCEK_SOZCUKLER = ["masa", "kalem", "defter", "çanta", "kapı", "güneş", "deniz", "kitap", "bardak", "yıldız", "orman", "kedi"]

def hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi):
    unlu = random.choice(KALIN_UNLULER if unlu_tipi == "kalin" else INCE_UNLULER)
    if onceki_son_harf_tipi == "unlu":
        secilen_yapi = random.choices(["CV", "CVC"], weights=[55, 45])[0]
    elif ardisik_unsuz_sayisi >= 2:
        secilen_yapi = random.choices(["VC", "V"], weights=[70, 30])[0]
    else:
        secilen_yapi = random.choices(["CV", "CVC", "VC", "V"], weights=[45, 40, 10, 5])[0]

    if secilen_yapi == "V":
        return unlu
    if secilen_yapi == "VC":
        return unlu + random.choice(UNSUZLER)
    if secilen_yapi == "CV":
        return random.choice(UNSUZLER) + unlu
    return random.choice(UNSUZLER) + unlu + random.choice(UNSUZLER)

def kuralli_sozcuk_uret(alt_sinir, ust_sinir):
    ses_sayisi = random.randint(alt_sinir, ust_sinir)
    unlu_tipi = random.choice(["kalin", "ince"])
    sozcuk = ""
    onceki_son_harf_tipi = ""
    ardisik_unsuz_sayisi = 0

    for i in range(ses_sayisi):
        hece = hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi)
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
        sozcuk += hece
        if sozcuk[-1] in (KALIN_UNLULER + INCE_UNLULER):
            onceki_son_harf_tipi = "unlu"
            ardisik_unsuz_sayisi = 0
        else:
            onceki_son_harf_tipi = "unsuz"
            ardisik_unsuz_sayisi = 2 if (len(sozcuk) >= 2 and sozcuk[-2] in UNSUZLER) else 1
    return sozcuk

def morfolojik_ek_getir(sozcuk, ek_tipi):
    son_unlu = [h for h in sozcuk if h in (KALIN_UNLULER + INCE_UNLULER)][-1]
    son_harf = sozcuk[-1]
    unsuzle_bitiyor = son_harf in UNSUZLER
    d_t = "t" if son_harf in SERT_UNSUZLER else "d"
    a_e = "a" if son_unlu in KALIN_UNLULER else "e"
    dar_unlu = UNLU_4LU[son_unlu]

    if ek_tipi == "cogul":
        return f"{sozcuk}l{a_e}r"
    if ek_tipi == "bulunma":
        return f"{sozcuk}{d_t}{a_e}"
    if ek_tipi == "belirtme":
        kaynastirma = "" if unsuzle_bitiyor else "y"
        return f"{sozcuk}{kaynastirma}{dar_unlu}"
    if ek_tipi == "gecmis_zaman":
        return f"{sozcuk}{d_t}{dar_unlu}l{a_e}r"
    if ek_tipi == "genis_zaman":
        return f"{sozcuk}{dar_unlu}r" if unsuzle_bitiyor else f"{sozcuk}r"
    if ek_tipi
