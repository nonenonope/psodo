import streamlit as st
import random
from gtts import gTTS
import os
from pydub import AudioSegment

# --- DİLBİLİMSEL ENVANTER ---
sert_unsuzler = list("çfhkpsşt")
yumusak_unsuzler_bas = list("bcdgjlmnrvyz") 
unsuzler_bas = sert_unsuzler + yumusak_unsuzler_bas
unsuzler_son = list("bcçdfgğhjklmnprsştvyz")
gecerli_cvcc = ['rt', 'rk', 'rs', 'rç', 'rp', 'rş', 'lt', 'lk', 'lp', 'lç', 'nt', 'nk', 'nç', 'mp']

uyum_sozlugu = {
    'a': ['a', 'ı'], 'ı': ['a', 'ı'],
    'e': ['e', 'i'], 'i': ['e', 'i'],
    'o': ['a', 'u'], 'u': ['a', 'u'],
    'ö': ['e', 'ü'], 'ü': ['e', 'ü']
}

def hece_uret(onceki_unlu=None, onceki_coda=None):
    if onceki_unlu is None:
        v = random.choice(list("aeıioöuü"))
    else:
        v = random.choice(uyum_sozlugu[onceki_unlu])
        
    if onceki_coda is not None:
        if onceki_coda in sert_unsuzler:
            gecerli_sertler = [c for c in sert_unsuzler if c != onceki_coda]
            c_bas = random.choice(gecerli_sertler) 
        else:
            gecerli_yumusaklar = [c for c in yumusak_unsuzler_bas if c != onceki_coda]
            c_bas = random.choice(gecerli_yumusaklar) 
    else:
        c_bas = random.choice(unsuzler_bas)
        
    kalip = random.choices(["CV", "CVC", "CVCC"], weights=[45, 45, 10])[0]
    
    if kalip == "CV": return c_bas + v, v, None 
    elif kalip == "CVC":
        c_son = random.choice(unsuzler_son)
        return c_bas + v + c_son, v, c_son 
    elif kalip == "CVCC":
        c_cift = random.choice(gecerli_cvcc)
        return c_bas + v + c_cift, v, c_cift[-1] 

def psodo_sozcuk_uret(hece_sayisi=2):
    sozcuk = ""
    hece, son_unlu, son_coda = hece_uret() 
    sozcuk += hece
    for _ in range(hece_sayisi - 1):
        hece, son_unlu, son_coda = hece_uret(son_unlu, son_coda) 
        sozcuk += hece
    return sozcuk

# --- ARAYÜZ (UI) ---
st.set_page_config(page_title="Türkçe Psödo-Sözcük Simülatörü", page_icon="🧠", layout="wide")

st.title("🧠 Türkçe Psödo-Sözcük ve Bürün Simülatörü")
st.markdown("Bu araç; Büyük/Küçük Ünlü Uyumu, SSP ve Hece Sınırı Kısıtlarını modelleyerek deneyler için **kurala uygun anlamsız uyarıcılar (Jabberwocky)** üretir.")
st.divider()

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ Üretim Ayarları")
    kelime_sayisi = st.slider("Kelime Sayısı", 5, 20, 10)
    hece_min = st.slider("Minimum Hece", 1, 5, 2)
    hece_max = st.slider("Maksimum Hece", 1, 5, 3)
    filtre_uygula = st.checkbox("🎧 Low-Pass Akustik Filtre Uygula (400Hz)", value=True)
    uret_butonu = st.button("🚀 Uyarıcıları Üret ve Sentezle", type="primary")

with col2:
    st.subheader("📝 Üretilen Uyarıcılar")
    
    if uret_butonu:
        with st.spinner('Kelimeler üretiliyor ve ses sentezleniyor...'):
            # Kelimeler
            uretilen_kelimeler = [psodo_sozcuk_uret(random.randint(hece_min, hece_max)) for _ in range(kelime_sayisi)]
            kelime_cikti = "\n".join(f"{i+1}. {kelime}" for i, kelime in enumerate(uretilen_kelimeler))
            
            # Cümleler
            c1_ozne, c1_sifat, c1_isim = psodo_sozcuk_uret(3), psodo_sozcuk_uret(2), psodo_sozcuk_uret(2)
            c2_ozne, c2_yer, c2_fiil = psodo_sozcuk_uret(2), psodo_sozcuk_uret(3), psodo_sozcuk_uret(2)
            c3_zaman, c3_nesne, c3_fiil = psodo_sozcuk_uret(2), psodo_sozcuk_uret(2), psodo_sozcuk_uret(3)

            cumle_1 = f"{c1_ozne.capitalize()} çok {c1_sifat} bir {c1_isim}dir."
            cumle_2 = f"{c2_ozne.capitalize()}lar {c2_yer}da {c2_fiil}iyor."
            cumle_3 = f"{c3_zaman.capitalize()}ken {c3_nesne}yi {c3_fiil}diler."
            
            okunacak_metin = f"{cumle_1} {cumle_2} {cumle_3}"
            
            # Ses İşlemleri
            tts = gTTS(text=okunacak_metin, lang='tr')
            tts.save("ses.mp3")
            
            if filtre_uygula:
                ses = AudioSegment.from_mp3("ses.mp3")
                filtrelenmis = ses.low_pass_filter(400)
                filtrelenmis.export("ses.mp3", format="mp3")
            
            st.success("Üretim Tamamlandı!")
            
            st.markdown("**🔊 Bürünsel Sentez (Jabberwocky Cümleleri):**")
            st.text(f"1) {cumle_1}\n2) {cumle_2}\n3) {cumle_3}")
            st.audio("ses.mp3")
            
            st.markdown("**📋 Tekil Uyarıcı Listesi:**")
            st.text(kelime_cikti)
