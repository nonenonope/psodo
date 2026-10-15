import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

# --- TÜRKÇE KARAKTER YÖNETİMİ ---
def turkce_kucult(metin):
    if not isinstance(metin, str): return metin
    return metin.replace('İ', 'i').replace('I', 'ı').lower()

def turkce_buyut(metin):
    if not isinstance(metin, str): return metin
    return metin.replace('i', 'İ').replace('ı', 'I').upper()

# --- 1. DİLBİLİMSEL KURALLAR VE SES ENVANTERİ ---
KALIN_UNLULER = ['a', 'ı', 'o', 'u']
INCE_UNLULER = ['e', 'i', 'ö', 'ü']
UNSUZLER = ['b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z']
SERT_UNSUZLER = ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş']
GERCEK_SOZCUKLER = ["masa", "kalem", "defter", "çanta", "kapı", "güneş", "deniz", "kitap", "bardak", "yıldız", "orman", "kedi"]

def hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi):
    unlu = random.choice(KALIN_UNLULER) if unlu_tipi == "kalin" else random.choice(INCE_UNLULER)
    if onceki_son_harf_tipi == "unlu":
        yapilar = ["CV", "CVC"]
        secilen_yapi = random.choices(yapilar, weights=[55, 45])[0]
    elif ardisik_unsuz_sayisi >= 2:
        yapilar = ["VC", "V"]
        secilen_yapi = random.choices(yapilar, weights=[70, 30])[0]
    else:
        yapilar = ["CV", "CVC", "VC", "V"]
        secilen_yapi = random.choices(yapilar, weights=[45, 40, 10, 5])[0]
        
    if secilen_yapi == "V": return unlu
    elif secilen_yapi == "VC": return unlu + random.choice(UNSUZLER)
    elif secilen_yapi == "CV": return random.choice(UNSUZLER) + unlu
    elif secilen_yapi == "CVC": return random.choice(UNSUZLER) + unlu + random.choice(UNSUZLER)

def kuralli_sozcuk_uret(min_hece, max_hece):
    hece_sayisi = random.randint(min_hece, max_hece)
    unlu_tipi = random.choice(["kalin", "ince"])
    sozcuk = ""
    onceki_son_harf_tipi = ""
    ardisik_unsuz_sayisi = 0
    for i in range(hece_sayisi):
        hece = hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi)
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
        sozcuk += hece
        if sozcuk[-1] in (KALIN_UNLULER + INCE_UNLULER):
            onceki_son_harf_tipi = "unlu"
            ardisik_unsuz_sayisi = 0
        else:
            onceki_son_harf_tipi = "unsuz"
            if len(sozcuk) >= 2 and sozcuk[-1] in UNSUZLER and sozcuk[-2] in UNSUZLER:
                ardisik_unsuz_sayisi = 2
            else:
                ardisik_unsuz_sayisi = 1
    return sozcuk

def morfolojik_ek_getir(sozcuk, ek_tipi):
    son_unlu = [harf for harf in sozcuk if harf in KALIN_UNLULER + INCE_UNLULER][-1]
    son_harf = sozcuk[-1]
    unsuzle_bitiyor = son_harf in UNSUZLER
    sertle_bitiyor = son_harf in SERT_UNSUZLER
    if ek_tipi == "cogul": return sozcuk + ("lar" if son_unlu in KALIN_UNLULER else "ler")
    elif ek_tipi == "bulunma":
        ek = "ta" if sertle_bitiyor and son_unlu in KALIN_UNLULER else "te" if sertle_bitiyor and son_unlu in INCE_UNLULER else "da" if son_unlu in KALIN_UNLULER else "de"
        return sozcuk + ek
    elif ek_tipi == "belirtme":
        kaynastirma = "" if unsuzle_bitiyor else "y"
        if son_
