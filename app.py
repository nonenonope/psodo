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
KALIN_ILK = ['a', 'ı', 'o', 'u']
KALIN_DIGER = ['a', 'ı', 'u']
INCE_ILK = ['e', 'i', 'ö', 'ü']
INCE_DIGER = ['e', 'i', 'ü']
TUM_UNLULER = ['a', 'ı', 'o', 'u', 'e', 'i', 'ö', 'ü']

BAS_UNSUZ = [
    'b', 'c', 'ç', 'd', 'f', 'g', 'h', 'k', 'l',
    'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
IC_UNSUZ = [
    'b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'k', 'l',
    'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
SON_UNSUZ = [
    'ç', 'f', 'ğ', 'h', 'k', 'l', 'm', 'n',
    'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
TUM_UNSUZLER = IC_UNSUZ + ['j']
SERT_UNSUZLER = ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş']
OTUMLU_ENGEL = ['b', 'c', 'd', 'g']

SON_OBEKLER = [
    "lk", "lp", "lt", "lç", "nk", "nt", "nç",
    "rk", "rp", "rt", "rç", "rs", "rş", "st", "şt", "kt", "ft"
]

GERCEK_SOZCUKLER = [
    "masa", "kalem", "defter", "çanta", "kapı", "güneş",
    "deniz", "kitap", "bardak", "yıldız", "orman", "kedi"
]

def unlu_sec(unlu_tipi, ilk_mi):
    if unlu_tipi == "kalin":
        havuz = KALIN_ILK if ilk_mi else KALIN_DIGER
    else:
        havuz = INCE_ILK if ilk_mi else INCE_DIGER
    return random.choice(havuz)

def sonses_sec(son_mi):
    havuz = SON_UNSUZ if son_mi else IC_UNSUZ
    agirlik = [1 if u == 'ğ' else 5 for u in havuz]
    return random.choices(havuz, weights=agirlik)[0]

def onses_sec(ilk_mi, onceki_tip, onceki_son_harf):
    havuz = list(BAS_UNSUZ if ilk_mi else IC_UNSUZ)
    if onceki_tip == "unsuz":
        havuz = [u for u in havuz if u != 'ğ']
        if onceki_son_harf in OTUMLU_ENGEL:
            havuz = [u for u in havuz if u not in SERT_UNSUZLER]
        elif onceki_son_harf in SERT_UNSUZLER:
            havuz = [u for u in havuz if u not in OTUMLU_ENGEL]
    return random.choice(havuz)

def hece_uret(
    unlu_tipi, onceki_tip, onceki_son_harf,
    unsuz_say, ilk_mi, son_mi, ileri=False
):
    unlu = unlu_sec(unlu_tipi, ilk_mi)

    if onceki_tip == "unlu":
        if ileri:
            yapilar = ["CV", "CVC", "CVCC"]
            agirliklar = [50, 38, 12]
        else:
            yapilar = ["CV", "CVC"]
            agirliklar = [55, 45]
    elif unsuz_say >= 2:
        yapilar = ["VC", "V"]
        agirliklar = [70, 30]
    else:
        if ileri:
            yapilar = ["CV", "CVC", "VC", "V", "CVCC", "VCC"]
            agirliklar = [40, 35, 8, 5, 8, 4]
        else:
            yapilar = ["CV", "CVC", "VC", "V"]
            agirliklar = [45, 40, 10, 5]

    yapi = random.choices(yapilar, weights=agirliklar)[0]

    if yapi == "V":
        return unlu
    if yapi == "VC":
        return unlu + sonses_sec(son_mi)
    if yapi == "CV":
        onses = onses_sec(ilk_mi, onceki_tip, onceki_son_harf)
        return onses + unlu
    if yapi == "CVC":
        onses = onses_sec(ilk_mi, onceki_tip, onceki_son_harf)
        return onses + unlu + sonses_sec(son_mi)
    if yapi == "VCC":
        return unlu + random.choice(SON_OBEKLER)
    if yapi == "CVCC":
        onses = onses_sec(ilk_mi, onceki_tip, onceki_son_harf)
        obek = random.choice(SON_OBEKLER)
        return onses + unlu + obek
    return unlu

def kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri=False):
    gercek_alt = min(alt_sinir, ust_sinir)
    gercek_ust = max(alt_sinir, ust_sinir)
    ses_sayisi = random.randint(gercek_alt, gercek_ust)
    unlu_tipi = random.choice(["kalin", "ince"])
    sozcuk = ""
    onceki_tip = ""
    onceki_son_harf = ""
    unsuz_say = 0

    for i in range(ses_sayisi):
        ilk_mi = (i == 0)
        son_mi = (i == ses_sayisi - 1)
        hece = hece_uret(
            unlu_tipi, onceki_tip, onceki_son_harf,
            unsuz_say, ilk_mi, son_mi, ileri
        )
        sozcuk += hece
        onceki_son_harf = sozcuk[-1]

        if onceki_son_harf in TUM_UNLULER:
            onceki_tip = "unlu"
            unsuz_say = 0
        else:
            onceki_tip = "unsuz"
            if len(sozcuk) >= 2 and sozcuk[-2] in TUM_UNSUZLER:
                unsuz_say = 2
            else:
                unsuz_say = 1

    return sozcuk

def morfolojik_ek_getir(sozcuk, ek_tipi):
    unlu_listesi = [h for h in sozcuk if h in TUM_UNLULER]
    son_unlu = unlu_listesi[-1]
    son_harf = sozcuk[-1]
    unsuzle_bitiyor = son_harf in TUM_UNSUZLER
    sertle_bitiyor = son_harf in SERT_UNSUZLER
    kalin_mi = son_unlu in KALIN_ILK

    if ek_tipi == "cogul":
        return sozcuk + ("lar" if kalin_mi else "ler")
    if ek_tipi == "bulunma":
        if sertle_bitiyor:
            ek = "ta" if kalin_mi else "te"
        else:
            ek = "da" if kalin_mi else "de"
        return sozcuk + ek
    if ek_tipi == "belirtme":
        kaynastirma = "" if unsuzle_bitiyor else "y"
        if son_unlu in ['a', 'ı']:
            ek = "ı"
        elif son_unlu in ['e', 'i']:
            ek = "i"
        elif son_unlu in ['o', 'u']:
            ek = "u"
        else:
