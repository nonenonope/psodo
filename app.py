import random
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
import io

# --- 1. DİLBİLİMSEL KURALLAR VE SES ENVANTERİ ---
KALIN_UNLULER = ['a', 'ı', 'o', 'u']
INCE_UNLULER = ['e', 'i', 'ö', 'ü']
UNSUZLER = ['b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z']

def hece_uret(unlu_tipi):
    unlu = random.choice(KALIN_UNLULER) if unlu_tipi == "kalin" else random.choice(INCE_UNLULER)
    yapilar = ["CV", "CVC", "VC", "V"]
    # Türkçe hece ağırlıklarına göre olasılık dağılımı
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
    hece_sayisi = random.randint(min_hece, max_hece)
    unlu_tipi = random.choice(["kalin", "ince"])
    
    kelime = ""
    for i in range(hece_sayisi):
        hece = hece_uret(unlu_tipi)
        # Türkçe kuralı: Kelimeler ğ ile başlamaz
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
        kelime += hece
    return kelime

def jabberwocky_cumlesi_uret(min_hece, max_hece):
    k1 = kuralli_kelime_uret(min_hece, max_hece).capitalize()
    k2 = kuralli_kelime_uret(min_hece, max_hece)
    k3 = kuralli_kelime_uret(min_hece, max_hece)
    
    cerceveler = [
        f"{k1} çok {k2} bir {k3}tir.",
        f"{k1}lar {k2}da {k3}iyor.",
        f"{k1} {k2}yi {k3}dılar."
    ]
    return random.choice(cerceveler)

# --- 2. STREAMLIT ARAYÜZÜ ---
st.title("🧠 Türkçe Psödo-Sözcük ve Bürün Simülatörü")
st.write("Fonotaktik kurallara (Büyük Ünlü Uyumu, Hece Yapısı) uygun klinik uyarıcılar üretin.")

# Sol Panel (Ayarlar)
st.sidebar.header("⚙️ Üretim Ayarları")
kelime_sayisi = st.sidebar.slider("Üretilecek Kelime Sayısı", min_value=5, max_value=50, value=10)
min_hece = st.sidebar.slider("Minimum Hece Sayısı", 1, 5, 2)
max_hece = st.sidebar.slider("Maksimum Hece Sayısı", 1, 5, 3)
filtre_uygula = st.sidebar.checkbox("Low-Pass Akustik Filtre Uygula (400Hz)", value=True)

# Ana Buton
if st.button("🚀 Uyarıcıları Üret ve Sentezle"):
    with st.spinner("Kelimeler üretiliyor ve ses sentezleniyor..."):
        
        # Kelime ve Cümle Üretimi
        kelimeler = [kuralli_kelime_uret(min_hece, max_hece) for _ in range(kelime_sayisi)]
        cumleler = [jabberwocky_cumlesi_uret(min_hece, max_hece) for _ in range(3)]
        
        # Cümleleri Ekrana Yazdır
        st.subheader("🔊 Bürünsel Sentez (Jabberwocky Cümleleri)")
        for c in cumleler:
            st.write(f"- {c}")
            
        # Ses Sentezi ve Filtreleme (gTTS + pydub)
        okunacak_metin = ". ".join(cumleler)
        tts = gTTS(text=okunacak_metin, lang='tr')
        
        ses_bellek = io.BytesIO()
        tts.write_to_fp(ses_bellek)
        ses_bellek.seek(0)
        
        audio = AudioSegment.from_file(ses_bellek, format="mp3")
        
        if filtre_uygula:
            audio = audio.low_pass_filter(400)
            
        cikis_bellek = io.BytesIO()
        audio.export(cikis_bellek, format="mp3")
        cikis_bellek.seek(0)
        
        # Ses Oynatıcıyı Göster
        st.audio(cikis_bellek, format="audio/mp3")
        
        # Liste Halinde Kelimeleri Göster
        st.subheader("📋 Tekil Uyarıcı Listesi")
        for i, kelime in enumerate(kelimeler, 1):
            st.write(f"{i}. {kelime}")
