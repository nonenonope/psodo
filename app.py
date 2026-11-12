import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

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
KALIN_DIGER_UNLULER = ['a', 'ı', 'u']  # /o/ yalnızca ilk seslemde bulunur
INCE_ILK_UNLULER = ['e', 'i', 'ö', 'ü']
INCE_DIGER_UNLULER = ['e', 'i', 'ü']   # /ö/ yalnızca ilk seslemde bulunur
TUM_UNLULER = ['a', 'ı', 'o', 'u', 'e', 'i', 'ö', 'ü']

# Konuma duyarlı ünsüz havuzları (/j/ yabancı kökenli olduğu için hariç)
BASLANGIC_UNSUZLERI = [
    'b', 'c', 'ç', 'd', 'f', 'g', 'h', 'k', 'l',
    'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
IC_UNSUZLER = [
    'b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'k', 'l',
    'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
# Sözcük sonu ünsüz filtresi (/b, c, d, g/ ve /j/ hariç)
SON_UNSUZLER = [
    'ç', 'f', 'ğ', 'h', 'k', 'l', 'm', 'n',
    'p', 'r', 's', 'ş', 't', 'v', 'y', 'z'
]
TUM_UNSUZLER = IC_UNSUZLER + ['j']
SERT_UNSUZLER = ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş']

# Türkçenin seslem sonu (coda) kurallarına uygun ünsüz öbekleri (VCC / CVCC)
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
        havuz = INCE_ILK_UNLULER if ilk_seslem_mi else INCE_DIGER_UNLULER
    return random.choice(havuz)

def sonses_sec(son_seslem_mi):
    havuz = SON_UNSUZLER if son_seslem_mi else IC_UNSUZLER
    # 'ğ' ağırlığını düşük tutarak doğal sıklık sağla
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
    onses_havuzu = BASLANGIC_UNSUZLERI if ilk_seslem_mi else IC_UNSUZLER

    if onceki_son_harf_tipi == "unlu":
        if ileri_seslem:
            yapilar = ["CV", "CVC", "CVCC"]
            secilen_yapi = random.choices(yapilar, weights=[50, 38, 12])[0]
        else:
            yapilar = ["CV", "CVC"]
            secilen_yapi = random.choices(yapilar, weights=[55, 45])[0]
    elif ardisik_unsuz_sayisi >= 2:
        yapilar = ["VC", "V"]
        secilen_yapi = random.choices(yapilar, weights=[70, 30])[0]
    else:
        if ileri_seslem:
            yapilar = ["CV", "CVC", "VC", "V", "CVCC", "VCC"]
            secilen_yapi = random.choices(yapilar, weights=[40, 35, 8, 5, 8, 4])[0]
        else:
            yapilar = ["CV", "CVC", "VC", "V"]
            secilen_yapi = random.choices(yapilar, weights=[45, 40, 10, 5])[0]

    if secilen_yapi == "V":
        return unlu
    elif secilen_yapi == "VC":
        return unlu + sonses_sec(son_seslem_mi)
    elif secilen_yapi == "CV":
        return random.choice(onses_havuzu) + unlu
    elif secilen_yapi == "CVC":
        return random.choice(onses_havuzu) + unlu + sonses_sec(son_seslem_mi)
    elif secilen_yapi == "VCC":
        return unlu + random.choice(TURKCE_SON_UNSUZ_OBEKLERI)
    elif secilen_yapi == "CVCC":
        onses = random.choice(onses_havuzu)
        obek = random.choice(TURKCE_SON_UNSUZ_OBEKLERI)
        return onses + unlu + obek

def kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri_seslem=False):
    ses_sayisi = random.randint(alt_sinir, ust_sinir)
    unlu_tipi = random.choice(["kalin", "ince"])
    sozcuk = ""
    onceki_son_harf_tipi = ""
    ardisik_unsuz_sayisi = 0

    for i in range(ses_sayisi):
        ilk_seslem_mi = (i == 0)
        son_seslem_mi = (i == ses_sayisi - 1)
        hece = hece_uret(
            unlu_tipi,
            onceki_son_harf_tipi,
            ardisik_unsuz_sayisi,
            ilk_seslem_mi,
            son_seslem_mi,
            ileri_seslem
        )
        sozcuk += hece

        if sozcuk[-1] in TUM_UNLULER:
            onceki_son_harf_tipi = "unlu"
            ardisik_unsuz_sayisi = 0
        else:
            onceki_son_harf_tipi = "unsuz"
            if len(sozcuk) >= 2 and sozcuk[-1] in TUM_UNSUZLER and sozcuk[-2] in TUM_UNSUZLER:
                ardisik_unsuz_sayisi = 2
            else:
                ardisik_unsuz_sayisi = 1

    return sozcuk

def morfolojik_ek_getir(sozcuk, ek_tipi):
    son_unlu = [harf for harf in sozcuk if harf in TUM_UNLULER][-1]
    son_harf = sozcuk[-1]
    # 'ğ' sesbilgisel olarak ünsüz gibi davranır ve ünsüz sonlu ek alır
    unsuzle_bitiyor = son_harf in TUM_UNSUZLER
    sertle_bitiyor = son_harf in SERT_UNSUZLER
    kalin_mi = son_unlu in KALIN_ILK_UNLULER

    if ek_tipi == "cogul":
        return sozcuk + ("lar" if kalin_mi else "ler")
    elif ek_tipi == "bulunma":
        if sertle_bitiyor:
            ek = "ta" if kalin_mi else "te"
        else:
            ek = "da" if kalin_mi else "de"
        return sozcuk + ek
    elif ek_tipi == "belirtme":
        kaynastirma = "" if unsuzle_bitiyor else "y"
        if son_unlu in ['a', 'ı']:
            ek = "ı"
        elif son_unlu in ['e', 'i']:
            ek = "i"
        elif son_unlu in ['o', 'u']:
            ek = "u"
        else:
            ek = "ü"
        return sozcuk + kaynastirma + ek
    elif ek_tipi == "gecmis_zaman":
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']:
            ek = d_t + "ılar"
        elif son_unlu in ['e', 'i']:
            ek = d_t + "iler"
        elif son_unlu in ['o', 'u']:
            ek = d_t + "ular"
        else:
            ek = d_t + "üler"
        return sozcuk + ek
    elif ek_tipi == "genis_zaman":
        if unsuzle_bitiyor:
            if son_unlu in ['a', 'ı']:
                ek = "ır"
            elif son_unlu in ['e', 'i']:
                ek = "ir"
            elif son_unlu in ['o', 'u']:
                ek = "ur"
            else:
                ek = "ür"
        else:
            ek = "r"
        return sozcuk + ek
    elif ek_tipi == "bildirme":
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']:
            ek = d_t + "ır"
        elif son_unlu in ['e', 'i']:
            ek = d_t + "ir"
        elif son_unlu in ['o', 'u']:
            ek = d_t + "ur"
        else:
            ek = d_t + "ür"
        return sozcuk + ek
    return sozcuk

def jabberwocky_tumcesi_uret(alt_sinir, ust_sinir, ileri_seslem=False):
    k1 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri_seslem)
    k2 = kuralli_sozcuk_uret
