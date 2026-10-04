import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

# --- 1. DİLBİLİMSEL KURALLAR VE SES ENVANTERİ ---
KALIN_UNLULER = ['a', 'ı', 'o', 'u']
INCE_UNLULER = ['e', 'i', 'ö', 'ü']
UNSUZLER = ['b', 'c', 'ç', 'd', 'f', 'g', 'ğ', 'h', 'j', 'k', 'l', 'm', 'n', 'p', 'r', 's', 'ş', 't', 'v', 'y', 'z']
SERT_UNSUZLER = ['p', 'ç', 't', 'k', 'f', 'h', 's', 'ş']
GERCEK_KELIMELER = ["masa", "kalem", "defter", "çanta", "kapı", "güneş", "deniz", "kitap", "bardak", "yıldız", "orman", "kedi"]

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

def kuralli_kelime_uret(min_hece, max_hece):
    hece_sayisi = random.randint(min_hece, max_hece)
    unlu_tipi = random.choice(["kalin", "ince"])
    kelime = ""
    onceki_son_harf_tipi = ""
    ardisik_unsuz_sayisi = 0
    for i in range(hece_sayisi):
        hece = hece_uret(unlu_tipi, onceki_son_harf_tipi, ardisik_unsuz_sayisi)
        if i == 0 and hece.startswith("ğ"):
            hece = hece.replace("ğ", random.choice(["g", "k", "d"]), 1)
        kelime += hece
        if kelime[-1] in (KALIN_UNLULER + INCE_UNLULER):
            onceki_son_harf_tipi = "unlu"
            ardisik_unsuz_sayisi = 0
        else:
            onceki_son_harf_tipi = "unsuz"
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
    if ek_tipi == "cogul": return kelime + ("lar" if son_unlu in KALIN_UNLULER else "ler")
    elif ek_tipi == "bulunma":
        ek = "ta" if sertle_bitiyor and son_unlu in KALIN_UNLULER else "te" if sertle_bitiyor and son_unlu in INCE_UNLULER else "da" if son_unlu in KALIN_UNLULER else "de"
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
    elif ek_tipi == "genis_zaman":
        if unsuzle_bitiyor:
            if son_unlu in ['a', 'ı']: ek = "ır"
            elif son_unlu in ['e', 'i']: ek = "ir"
            elif son_unlu in ['o', 'u']: ek = "ur"
            else: ek = "ür"
        else: ek = "r"
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
        cikis_bellek.seek(0)
        return cikis_bellek
    return ses_bellek

# --- 2. STREAMLIT ARAYÜZÜ (OTURUM YÖNETİMİ) ---
if 'deney_basladi' not in st.session_state: st.session_state.deney_basladi = False
if 'deney_bitti' not in st.session_state: st.session_state.deney_bitti = False
if 'batarya' not in st.session_state: st.session_state.batarya = []
if 'mevcut_soru' not in st.session_state: st.session_state.mevcut_soru = 0
if 'sonuclar' not in st.session_state: st.session_state.sonuclar = []
if 'baslangic_zamani' not in st.session_state: st.session_state.baslangic_zamani = 0
if 'secilen_mod' not in st.session_state: st.session_state.secilen_mod = "Sadece Ses"

st.set_page_config(page_title="Psödo-Sözcük ve LDT Simülatörü", layout="wide")
st.title("🧠 Klinik Psödo-Sözcük ve RT Deney Simülatörü")

sekme1, sekme2 = st.tabs(["⚙️ Jeneratör & Bürünsel Sentez", "⏱️ Klinik Deney (LDT)"])

# --- SEKME 1: JENERATÖR ---
with sekme1:
    st.header("Uyarıcı Bataryası Üret")
    col1, col2 = st.columns(2)
    with col1:
        kelime_sayisi = st.slider("Üretilecek Kelime Sayısı", 5, 50, 10)
        min_hece = st.slider("Minimum Hece Sayısı", 1, 5, 2)
    with col2:
        max_hece = st.slider("Maksimum Hece Sayısı", 1, 5, 3)
        filtre_uygula = st.checkbox("Low-Pass Akustik Filtre Uygula (400Hz)", value=True)

    if st.button("🚀 Uyarıcıları Üret ve Sentezle"):
        with st.spinner("Sentezleniyor..."):
            kelimeler = [kuralli_kelime_uret(min_hece, max_hece) for _ in range(kelime_sayisi)]
            cumleler = [jabberwocky_cumlesi_uret(min_hece, max_hece) for _ in range(3)]
            
            st.subheader("🔊 Bürünsel Sentez (Jabberwocky Cümleleri)")
            for c in cumleler:
                st.write(f"- {c}")
                
            okunacak_metin = ". ".join(cumleler)
            ses_ciktisi = sesi_sentezle(okunacak_metin, filtre_uygula)
            st.audio(ses_ciktisi, format="audio/mp3")
            
            st.subheader("📋 Tekil Uyarıcı Listesi")
            df = pd.DataFrame({"Psödo-Sözcükler": kelimeler})
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Listeyi CSV Olarak İndir", data=csv, file_name="uyarici_bataryasi.csv", mime="text/csv")

# --- SEKME 2: KLİNİK DENEY ---
with sekme2:
    st.header("İşitsel ve Görsel Sözcüksel Karar Görevi (LDT)")
    
    if not st.session_state.deney_basladi and not st.session_state.deney_bitti:
        st.write("Lütfen deneyi hangi modalitede (duyusal kanalda) sunmak istediğinizi seçin:")
        
        # Sunum Modu Seçici
        sunum_modu = st.radio("Uyarıcı Sunum Modu:", ["Sadece Ses", "Sadece Yazı", "Ses + Yazı (Birlikte)"])
        
        if st.button("▶️ Deneyi Başlat"):
            st.session_state.secilen_mod = sunum_modu
            gercekler = random.sample(GERCEK_KELIMELER, 5)
            sahteler = [kuralli_kelime_uret(2, 3) for _ in range(5)]
            batarya = [{"kelime": k, "gercek_mi": True} for k in gercekler] + [{"kelime": k, "gercek_mi": False} for k in sahteler]
            random.shuffle(batarya)
            st.session_state.batarya = batarya
            st.session_state.deney_basladi = True
            st.session_state.mevcut_soru = 0
            st.session_state.sonuclar = []
            st.rerun()

    elif st.session_state.deney_basladi and not st.session_state.deney_bitti:
        mevcut_index = st.session_state.mevcut_soru
        aktif_kelime = st.session_state.batarya[mevcut_index]["kelime"]
        st.progress((mevcut_index) / len(st.session_state.batarya))
        st.subheader(f"Soru {mevcut_index + 1} / {len(st.session_state.batarya)}")
        
        # Seçilen moda göre uyarıcıyı ekrana bas
        mod = st.session_state.secilen_mod
        
        if mod in ["Sadece Ses", "Ses + Yazı (Birlikte)"]:
            ses_dosyasi = sesi_sentezle(aktif_kelime, filtre_uygula=False)
            st.audio(ses_dosyasi, format="audio/mp3", autoplay=True)
            
        if mod in ["Sadece Yazı", "Ses + Yazı (Birlikte)"]:
            st.markdown(f"<h1 style='text-align: center; font-size: 60px; margin: 40px 0;'>{aktif_kelime.upper()}</h1>", unsafe_allow_html=True)
            
        if mod == "Sadece Ses":
            st.markdown(f"<h1 style='text-align: center; font-size: 60px; margin: 40px 0;'>🔊</h1>", unsafe_allow_html=True)
        
        if st.session_state.baslangic_zamani == 0:
            st.session_state.baslangic_zamani = time.time()
            
        st.write("---")
        st.write("### Uyarıcı gerçek bir Türkçe kelime mi?")
        col1, col2 = st.columns(2)
        
        def cevabi_kaydet(verilen_cevap):
            rt = (time.time() - st.session_state.baslangic_zamani) * 1000
            dogru_cevap = st.session_state.batarya[mevcut_index]["gercek_mi"]
            isabet = (verilen_cevap == dogru_cevap)
            st.session_state.sonuclar.append({
                "Kelime": st.session_state.batarya[mevcut_index]["kelime"],
                "Tip": "Gerçek" if dogru_cevap else "Psödo",
                "Sunum Modu": st.session_state.secilen_mod, # Modu buraya logluyoruz
                "Cevap": "Gerçek" if verilen_cevap else "Psödo",
                "Doğruluk": isabet,
                "RT (ms)": round(rt, 2)
            })
            st.session_state.baslangic_zamani = 0
            st.session_state.mevcut_soru += 1
            if st.session_state.mevcut_soru >= len(st.session_state.batarya):
                st.session_state.deney_bitti = True
                st.session_state.deney_basladi = False

        with col1:
            if st.button("✅ GERÇEK", use_container_width=True):
                cevabi_kaydet(True)
                st.rerun()
        with col2:
            if st.button("❌ SAHTE", use_container_width=True):
                cevabi_kaydet(False)
                st.rerun()

    elif st.session_state.deney_bitti:
        st.success("🎉 Deney Tamamlandı!")
        df_sonuclar = pd.DataFrame(st.session_state.sonuclar)
        st.dataframe(df_sonuclar, use_container_width=True)
        csv_sonuclar = df_sonuclar.to_csv(index=False).encode('utf-8')
        st.download_button("📥 RT Sonuçlarını CSV İndir", data=csv_sonuclar, file_name="rt_sonuclari.csv", mime="text/csv")
        if st.button("🔄 Sıfırla ve Yeni Deney Yap"):
            st.session_state.deney_bitti = False
            st.session_state.deney_basladi = False
            st.rerun()
