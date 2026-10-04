import random
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
import io

# 1. TÜRKÇE SES ENVANTERİ (Dilbilimsel kurallar için)
KALIN_UNLULER = ['a', 'ı', 'o', 'u']
INCE_UNLULER = ['e', 'i', 'ö', 'ü']
UNSUZLER = ['b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z']

def hece_uret(unlu_tipi):
    """Sadece Türkçede izin verilen hece yapılarını (V, VC, CV, CVC) üretir."""
    # Büyük ünlü uyumu filtresi
    unlu = random.choice(KALIN_UNLULER) if unlu_tipi == "kalin" else random.choice(INCE_UNLULER)
    
    # Türkçe hece yapısı olasılıkları (CV ve CVC en baskındır)
    yapilar = ["CV", "CVC", "VC", "V"]
    secilen_yapi = random.choices(yapilar, weights=[45, 40, 10, 5])[0]
    
    if secilen_yapi == "V":
        return unlu
    elif secilen_yapi == "VC":
        return unlu + random.choice(UNSUZLER)
    elif secilen_yapi == "CV":
        return random.choice(UNSUZLER) + unlu
    elif secilen_yapi == "CVC":
        return random.choice(UNSUZLER) + unlu + random.choice(UNSUZLER)

def kuralli_kelime_uret(min_hece, max_hece):
    """Büyük ünlü uyumuna ve hece sınırlarına uyan psödo-sözcük üretir."""
    hece_sayisi = random.randint(min_hece, max_hece)
    unlu_tipi = random.choice(["kalin", "ince"]) # Kelimenin kök ünlü tipini belirler
    
    kelime = ""
    for i in range(hece_sayisi):
        hece = hece_uret(unlu_tipi)
        
        # Dilbilimsel Kural: Türkçe kelimeler 'ğ' ile başlamaz
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
            
        kelime += hece
        
    return kelime

def jabberwocky_cumlesi_uret():
    """Üretilen kurallı kelimelerle sahte sözdizimsel çerçeveler oluşturur."""
    k1 = kuralli_kelime_uret(2, 3).capitalize()
    k2 = kuralli_kelime_uret(2, 4)
    k3 = kuralli_kelime_uret(2, 3)
    
    # Çerçeve tipleri: Gerçek Türkçe eklerle sahte kökleri birleştirir
    cerceveler = [
        f"{k1} çok {k2} bir {k3}tir.",
        f"{k1}lar {k2}da {k3}iyor.",
        f"{k1} {k2}yi {k3}dılar."
    ]
    return random.choice(cerceveler)

# --- STREAMLIT ARAYÜZÜ ---
st.title("🧠 Türkçe Psödo-Sözcük ve Bürün Simülatörü")
st.write("Fonotaktik kurallara (Büyük Ünlü Uyumu, Hece Yapısı) uygun klinik uyarıcılar üretin.")

# (Geri kalan Streamlit arayüz kodları, slider'lar, pydub ses işlemleri ve st.button kısımları eskisi gibi kalabilir)
