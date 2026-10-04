import random
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment
import io

# --- 1. DİLBİLİMSEL KURALLAR VE SES ENVANTERİ ---
KALIN_UNLULER = ['a', 'ı', 'o', 'u']
INCE_UNLULER = ['e', 'i', 'ö', 'ü']
UNSUZLER = ['b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z']
SERT_UNSUZLER = ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş'] # Fıstıkçı Şahap

def hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi):
    unlu = random.choice(KALIN_UNLULER) if unlu_tipi == "kalin" else random.choice(INCE_UNLULER)
    
    # Hece başlama kuralları
    if onceki_son_harf_tipi == "unlu":
        # Önceki hece ünlüyle bittiyse, YENİ hece KESİNLİKLE ünsüzle (C) başlamalı
        yapilar = ["CV", "CVC"]
        secilen_yapi = random.choices(yapilar, weights=[55, 45])[0]
    elif ardisik_unsuz_sayisi >= 2:
        # Önceki hecelerde 2 ünsüz yan yana geldiyse, YENİ hece KESİNLİKLE ünlüyle (V) başlamalı (CCC engellemesi)
        yapilar = ["VC", "V"]
        secilen_yapi = random.choices(yapilar, weights=[70, 30])[0]
    else:
        # Serbest durum
        yapilar = ["CV", "CVC", "VC", "V"]
        secilen_yapi = random.choices(yapilar, weights=[45, 40, 10, 5])[0]
        
    if secilen_yapi == "V": return unlu
    elif secilen_yapi == "VC": return unlu + random.choice(UNSUZLER)
    elif secilen_yapi == "CV": return random.choice(UNSUZLER) + unlu
    elif secilen_yapi == "CVC": return random.choice(UNSUZLER) + unlu + random.choice(UNSUZLER)

def kuralli_kelime_uret(min_hece, max_hece):
    hece_sayisi = random.randint(min_hece, max_hece)
    unlu_tipi = random.choice(["kalin", "ince"])
    kelime = ""
    
    onceki_son_harf_tipi = "" # "unlu" veya "unsuz"
    ardisik_unsuz_sayisi = 0
    
    for i in range(hece_sayisi):
        hece = hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi)
        
        # Kelime 'ğ' ile başlayamaz
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
            
        kelime += hece
        
        # Döngü sonunda, mevcut kelimenin son durumunu analiz et
        if kelime[-1] in (KALIN_UNLULER + INCE_UNLULER):
            onceki_son_harf_tipi = "unlu"
            ardisik_unsuz_sayisi = 0
        else:
            onceki_son_harf_tipi = "unsuz"
            # Son 2 harf ünsüz mü diye kontrol et (örn: 'rt')
            if len(kelime) >= 2 and kelime[-1] in UNSUZLER and kelime[-2] in UNSUZLER:
                ardisik_unsuz_sayisi = 2
            else:
                ardisik_unsuz_sayisi = 1
                
    return kelime

def morfolojik_ek_getir(kelime, ek_tipi):
    son_unlu = [harf for harf in kelime if harf in KALIN_UNLULER + INCE_UNLULER][-1]
    son_harf = kelime[-1]
    unsuzle_bitiyor = son_harf in UNSUZLER
    sertle_bitiyor = son_harf in SERT_UNSUZLER
    
    if ek_tipi == "cogul": 
        return kelime + ("lar" if son_unlu in KALIN_UNLULER else "ler")
        
    elif ek_tipi == "bulunma":
        ek = "ta" if sertle_bitiyor and son_unlu in KALIN_UNLULER else \
             "te" if sertle_bitiyor and son_unlu in INCE_UNLULER else \
             "da" if son_unlu in KALIN_UNLULER else "de"
        return kelime + ek
        
    elif ek_tipi == "belirtme":
        kaynastirma = "" if unsuzle_bitiyor else "y"
        if son_unlu in ['a', 'ı']: ek = "ı"
        elif son_unlu in ['e', 'i']: ek = "i"
        elif son_unlu in ['o', 'u']: ek = "u"
        else: ek = "ü"
        return kelime + kaynastirma + ek
        
    elif ek_tipi == "gecmis_zaman":
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']: ek = d_t + "ılar"
        elif son_unlu in ['e', 'i']: ek = d_t + "iler"
        elif son_unlu in ['o', 'u']: ek = d_t + "ular"
        else: ek = d_t + "üler"
        return kelime + ek
        
    elif ek_tipi == "genis_zaman": # Şimdiki zaman (-iyor) yerine, uyumu bozmayan geniş zaman eklendi
        # Basitçe -ar/-er veya -ır/-ir/-ur/-ür kuralı
        if unsuzle_bitiyor:
            if son_unlu in ['a', 'ı']: ek = "ır"
            elif son_unlu in ['e', 'i']: ek = "ir"
            elif son_unlu in ['o', 'u']: ek = "ur"
            else: ek = "ür"
        else:
            ek = "r"
        return kelime + ek
        
    elif ek_tipi == "bildirme":
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']: ek = d_t + "ır"
        elif son_unlu in ['e', 'i']: ek = d_t + "ir"
        elif son_unlu in ['o', 'u']: ek = d_t + "ur"
        else: ek = d_t + "ür"
        return kelime + ek

    return kelime

def jabberwocky_cumlesi_uret(min_hece, max_hece):
    k1 = kuralli_kelime_uret(min_hece, max_hece)
    k2 = kuralli_kelime_uret(min_hece, max_hece)
    k3 = kuralli_kelime_uret(min_hece, max_hece)
    
    cerceveler = [
        f"{k1.capitalize()} çok {k2} bir {morfolojik_ek_getir(k3, 'bildirme')}.",
        f"{morfolojik_ek_getir(k1.capitalize(), 'cogul')} {morfolojik_ek_getir(k2, 'bulunma')} {morfolojik_ek_getir(k3, 'genis_zaman')}.",
        f"{k1.capitalize()} {morfolojik_ek_getir(k2, 'belirtme')} {morfolojik_ek_getir(k3, 'gecmis_zaman')}."
    ]
    return random.choice(cerceveler)
    
    # Dinamik morfolojik çerçeveler
    cerceveler = [
        f"{k1.capitalize()} çok {k2} bir {morfolojik_ek_getir(k3, 'bildirme')}.",
        f"{morfolojik_ek_getir(k1.capitalize(), 'cogul')} {morfolojik_ek_getir(k2, 'bulunma')} {morfolojik_ek_getir(k3, 'simdiki_zaman')}.",
        f"{k1.capitalize()} {morfolojik_ek_getir(k2, 'belirtme')} {morfolojik_ek_getir(k3, 'gecmis_zaman')}."
    ]
    return random.choice(cerceveler)

# --- 2. STREAMLIT ARAYÜZÜ ---
st.title("🧠 Türkçe Psödo-Sözcük ve Bürün Simülatörü")
st.write("Fonotaktik kurallara (Büyük Ünlü Uyumu, Hece Yapısı) uygun klinik uyarıcılar üretin.")

st.sidebar.header("⚙️ Üretim Ayarları")
kelime_sayisi = st.sidebar.slider("Üretilecek Kelime Sayısı", min_value=5, max_value=50, value=10)
min_hece = st.sidebar.slider("Minimum Hece Sayısı", 1, 5, 2)
max_hece = st.sidebar.slider("Maksimum Hece Sayısı", 1, 5, 3)
filtre_uygula = st.sidebar.checkbox("Low-Pass Akustik Filtre Uygula (400Hz)", value=True)

if st.button("🚀 Uyarıcıları Üret ve Sentezle"):
    with st.spinner("Kelimeler üretiliyor ve ses sentezleniyor..."):
        
        kelimeler = [kuralli_kelime_uret(min_hece, max_hece) for _ in range(kelime_sayisi)]
        cumleler = [jabberwocky_cumlesi_uret(min_hece, max_hece) for _ in range(3)]
        
        st.subheader("🔊 Bürünsel Sentez (Jabberwocky Cümleleri)")
        for c in cumleler:
            st.write(f"- {c}")
            
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
        
        st.audio(cikis_bellek, format="audio/mp3")
        
        st.subheader("📋 Tekil Uyarıcı Listesi")
        for i, kelime in enumerate(kelimeler, 1):
            st.write(f"{i}. {kelime}")
