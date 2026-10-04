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

def hece_uret(unlu_tipi):
    unlu = random.choice(KALIN_UNLULER) if unlu_tipi == "kalin" else random.choice(INCE_UNLULER)
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
    for i in range(hece_sayisi):
        hece = hece_uret(unlu_tipi)
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
        kelime += hece
    return kelime

def morfolojik_ek_getir(kelime, ek_tipi):
    """Kelimenin son ünlüsüne ve ünsüzüne bakarak dilbilgisi kurallarına (allomorf) uygun eki seçer."""
    # Kelimedeki son ünlüyü bul
    son_unlu = [harf for harf in kelime if harf in KALIN_UNLULER + INCE_UNLULER][-1]
    son_harf = kelime[-1]
    unsuzle_bitiyor = son_harf in UNSUZLER
    sertle_bitiyor = son_harf in SERT_UNSUZLER
    
    if ek_tipi == "cogul": # -lar / -ler (Büyük Ünlü Uyumu)
        return kelime + ("lar" if son_unlu in KALIN_UNLULER else "ler")
        
    elif ek_tipi == "bulunma": # -da / -de / -ta / -te (Ünsüz Sertleşmesi)
        ek = "ta" if sertle_bitiyor and son_unlu in KALIN_UNLULER else \
             "te" if sertle_bitiyor and son_unlu in INCE_UNLULER else \
             "da" if son_unlu in KALIN_UNLULER else "de"
        return kelime + ek
        
    elif ek_tipi == "belirtme": # -ı / -i / -u / -ü (Küçük Ünlü Uyumu ve Kaynaştırma)
        kaynastirma = "" if unsuzle_bitiyor else "y"
        if son_unlu in ['a', 'ı']: ek = "ı"
        elif son_unlu in ['e', 'i']: ek = "i"
        elif son_unlu in ['o', 'u']: ek = "u"
        else: ek = "ü"
        return kelime + kaynastirma + ek
        
    elif ek_tipi == "gecmis_zaman": # -dılar / -diler / -tılar / -tiler
        d_t = "t" if sertle_bitiyor else "d"
        if son_unlu in ['a', 'ı']: ek = d_t + "ılar"
        elif son_unlu in ['e', 'i']: ek = d_t + "iler"
        elif son_unlu in ['o', 'u']: ek = d_t + "ular"
        else: ek = d_t + "üler"
        return kelime + ek
        
    elif ek_tipi == "simdiki_zaman": # -ıyor / -iyor / -uyor / -üyor
        # Ünlü daralmasını basitçe yönetmek için son sesli harfi düşürürüz
        kok = kelime[:-1] if not unsuzle_bitiyor else kelime
        if son_unlu in ['a', 'ı']: ek = "ıyor"
        elif son_unlu in ['e', 'i']: ek = "iyor"
        elif son_unlu in ['o', 'u']: ek = "uyor"
        else: ek = "üyor"
        return kok + ek
        
    elif ek_tipi == "bildirme": # -dır / -dir / -tır / -tir
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
