import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

# --- SAYFA YAPILANDIRMASI ---
st.set_page_config(page_title="Yalancı Sözcük ve Sözcüksel Seçim Deneyi", layout="wide")

# --- OTURUM DURUMU BAŞLATICI (SESSION STATE) ---
if 'deney_basladi' not in st.session_state: st.session_state.deney_basladi = False
if 'deney_bitti' not in st.session_state: st.session_state.deney_bitti = False
if 'batarya' not in st.session_state: st.session_state.batarya = []
if 'mevcut_soru' not in st.session_state: st.session_state.mevcut_soru = 0
if 'sonuclar' not in st.session_state: st.session_state.sonuclar = []
if 'baslangic_zamani' not in st.session_state: st.session_state.baslangic_zamani = 0
if 'secilen_kanal' not in st.session_state: st.session_state.secilen_kanal = "İşitsel"

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
        if son_unlu in ['a', 'ı']: ek = "ı"
        elif son_unlu in ['e', 'i']: ek = "i"
        elif son_unlu in ['o', 'u']: ek = "u"
        else: ek = "ü"
        return sozcuk + kaynastirma + ek
    elif ek_tipi == "gecmis_zaman":
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']: ek = d_t + "ılar"
        elif son_unlu in ['e', 'i']: ek = d_t + "iler"
        elif son_unlu in ['o', 'u']: ek = d_t + "ular"
        else: ek = d_t + "üler"
        return sozcuk + ek
    elif ek_tipi == "genis_zaman":
        if unsuzle_bitiyor:
            if son_unlu in ['a', 'ı']: ek = "ır"
            elif son_unlu in ['e', 'i']: ek = "ir"
            elif son_unlu in ['o', 'u']: ek = "ur"
            else: ek = "ür"
        else: ek = "r"
        return sozcuk + ek
    elif ek_tipi == "bildirme":
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']: ek = d_t + "ır"
        elif son_unlu in ['e', 'i']: ek = d_t + "ir"
        elif son_unlu in ['o', 'u']: ek = d_t + "ur"
        else: ek = d_t + "ür"
        return sozcuk + ek
    return sozcuk

def jabberwocky_tumcesi_uret(alt_sinir, ust_sinir):
    k1 = kuralli_sozcuk_uret(alt_sinir, ust_sinir)
    k2 = kuralli_sozcuk_uret(alt_sinir, ust_sinir)
    k3 = kuralli_sozcuk_uret(alt_sinir, ust_sinir)
    c1 = turkce_buyut(k1[:1]) + turkce_kucult(k1[1:])
    k2_bulunma = morfolojik_ek_getir(k2, 'bulunma')
    k3_genis = morfolojik_ek_getir(k3, 'genis_zaman')
    k3_bildirme = morfolojik_ek_getir(k3, 'bildirme')
    k1_cogul = morfolojik_ek_getir(c1, 'cogul')
    k2_belirtme = morfolojik_ek_getir(k2, 'belirtme')
    k3_gecmis = morfolojik_ek_getir(k3, 'gecmis_zaman')
    
    cerceveler = [
        f"{c1} çok {k2} bir {k3_bildirme}.",
        f"{k1_cogul} {k2_bulunma} {k3_genis}.",
        f"{c1} {k2_belirtme} {k3_gecmis}."
    ]
    return random.choice(cerceveler)

def sesi_sentezle(metin, filtre_uygula=False):
    tts = gTTS(text=metin, lang='tr')
    ses_bellek = io.BytesIO()
    tts.write_to_fp(ses_bellek)
    ses_bellek.seek(0)
    if filtre_uygula:
        audio = AudioSegment.from_file(ses_bellek, format="mp3")
        audio = audio.low_pass_filter(400)
        cikis_bellek = io.BytesIO()
        audio.export(cikis_bellek, format="mp3")
        cikis
