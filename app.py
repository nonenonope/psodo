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

def hece_uret(unlu_tipi, onceki_tip, unsuz_say, ilk_mi, son_mi, ileri=False):
    unlu = unlu_sec(unlu_tipi, ilk_mi)
    onses_havuz = BAS_UNSUZ if ilk_mi else IC_UNSUZ

    if onceki_tip == "unlu":
        if ileri:
            yapilar = ["CV", "CVC", "CVCC"]
            w = [50, 38, 12]
        else:
            yapilar = ["CV", "CVC"]
            w = [55, 45]
    elif unsuz_say >= 2:
        yapilar = ["VC", "V"]
        w = [70, 30]
    else:
        if ileri:
            yapilar = ["CV", "CVC", "VC", "V", "CVCC", "VCC"]
            w = [40, 35, 8, 5, 8, 4]
        else:
            yapilar = ["CV", "CVC", "VC", "V"]
            w = [45, 40, 10, 5]

    yapi = random.choices(yapilar, weights=w)[0]

    if yapi == "V":
        return unlu
    if yapi == "VC":
        return unlu + sonses_sec(son_mi)
    if yapi == "CV":
        return random.choice(onses_havuz) + unlu
    if yapi == "CVC":
        return random.choice(onses_havuz) + unlu + sonses_sec(son_mi)
    if yapi == "VCC":
        return unlu + random.choice(SON_OBEKLER)
    if yapi == "CVCC":
        onses = random.choice(onses_havuz)
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
    unsuz_say = 0

    for i in range(ses_sayisi):
        ilk_mi = (i == 0)
        son_mi = (i == ses_sayisi - 1)
        hece = hece_uret(
            unlu_tipi, onceki_tip, unsuz_say, ilk_mi, son_mi, ileri
        )
        sozcuk += hece

        if sozcuk[-1] in TUM_UNLULER:
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
            ek = "ü"
        return sozcuk + kaynastirma + ek
    if ek_tipi == "gecmis_zaman":
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
    if ek_tipi == "genis_zaman":
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
    if ek_tipi == "bildirme":
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

def jabberwocky_tumcesi_uret(alt_sinir, ust_sinir, ileri=False):
    k1 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri)
    k2 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri)
    k3 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri)

    c1 = turkce_buyut(k1[:1]) + turkce_kucult(k1[1:])
    k2_bul = morfolojik_ek_getir(k2, 'bulunma')
    k3_gen = morfolojik_ek_getir(k3, 'genis_zaman')
    k3_bil = morfolojik_ek_getir(k3, 'bildirme')
    k1_cog = morfolojik_ek_getir(c1, 'cogul')
    k2_bel = morfolojik_ek_getir(k2, 'belirtme')
    k3_gec = morfolojik_ek_getir(k3, 'gecmis_zaman')

    cerceveler = [
        f"{c1} çok {k2} bir {k3_bil}.",
        f"{k1_cog} {k2_bul} {k3_gen}.",
        f"{c1} {k2_bel} {k3_gec}."
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
if 'deney_basladi' not in st.session_state:
    st.session_state.deney_basladi = False
if 'deney_bitti' not in st.session_state:
    st.session_state.deney_bitti = False
if 'batarya' not in st.session_state:
    st.session_state.batarya = []
if 'mevcut_soru' not in st.session_state:
    st.session_state.mevcut_soru = 0
if 'sonuclar' not in st.session_state:
    st.session_state.sonuclar = []
if 'baslangic_zamani' not in st.session_state:
    st.session_state.baslangic_zamani = 0
if 'secilen_kanal' not in st.session_state:
    st.session_state.secilen_kanal = "İşitsel"

st.set_page_config(
    page_title="Yalancı Sözcük ve Sözcüksel Seçim Deneyi",
    layout="wide"
)
st.title("🧠 Klinik Dilbilimsel Yalancı Sözcük ve Tepki Süresi Deneyi")

sekme1, sekme2 = st.tabs([
    "⚙️ Bürünsel Uyarlama Üreteci",
    "⏱️ Sözcüksel Seçim Deneyi"
])

# --- SEKME 1: ÜRETEÇ ---
with sekme1:
    st.header("Uyaran Bataryası Üret")
    col1, col2 = st.columns(2)
    with col1:
        sozcuk_sayisi = st.slider("Üretilecek Sözcük Sayısı", 5, 50, 10)
        alt_sinir = st.slider("Alt Sınır (En Az Ses Sayısı)", 1, 5, 2)
    with col2:
        ust_sinir = st.slider("Üst Sınır (En Çok Ses Sayısı)", 1, 5, 3)
        ileri_seslem = st.checkbox(
            "İleri Seslem Örüntülerini Dahil Et (VCC ve CVCC)",
            value=False
        )
        filtre_uygula = st.checkbox(
            "Alçak Geçirgen Akustik Filtre Uygula (400Hz)",
            value=True
        )

    if st.button("🚀 Uyaranları Üret"):
        with st.spinner("Üretiliyor..."):
            sozcukler = [
                kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri_seslem)
                for _ in range(sozcuk_sayisi)
            ]
            tumceler = [
                jabberwocky_tumcesi_uret(alt_sinir, ust_sinir, ileri_seslem)
                for _ in range(3)
            ]

            st.subheader("🔊 Bürünsel Uyarlama (Jabberwocky Tümceleri)")
            for t in tumceler:
                st.write(f"- {t}")

            okunacak_metin = ". ".join(tumceler)
            ses_ciktisi = sesi_sentezle(okunacak_metin, filtre_uygula)
            st.audio(ses_ciktisi, format="audio/mp3")

            st.subheader("📋 Tekil Uyaran Listesi")
            df = pd.DataFrame({"Yalancı Sözcükler": sozcukler})
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Listeyi CSV Olarak İndir",
                data=csv,
                file_name="uyaran_bataryasi.csv",
                mime="text/csv"
            )

# --- SEKME 2: KLİNİK DENEY ---
with sekme2:
    st.header("Sözcüksel Seçim Deneyi")

    if not st.session_state.deney_basladi and not st.session_state.deney_bitti:
        st.write(
            "Lütfen deneyi hangi duyusal kanaldan almak istediğinizi seçin:"
        )
        sunum_kanali = st.radio("Uyaran Sunum Kanalı:", ["İşitsel", "Görsel"])

        if st.button("▶️ Deneyi Başlat"):
            st.session_state.secilen_kanal = sunum_kanali
            gercekler = random.sample(GERCEK_SOZCUKLER, 5)
            sahteler = [kuralli_sozcuk_uret(2, 3, False) for _ in range(5)]
            batarya = (
                [{"sozcuk": k, "gercek_mi": True} for k in gercekler]
                + [{"sozcuk": k, "gercek_mi": False} for k in sahteler]
            )
            random.shuffle(batarya)
            st.session_state.batarya = batarya
            st.session_state.deney_basladi = True
            st.session_state.mevcut_soru = 0
            st.session_state.sonuclar = []
            st.rerun()

    elif st.session_state.deney_basladi and not st.session_state.deney_bitti:
        mevcut_index = st.session_state.mevcut_soru
        toplam_soru = len(st.session_state.batarya)
        aktif_sozcuk = st.session_state.batarya[mevcut_index]["sozcuk"]

        st.progress(mevcut_index / toplam_soru)
        st.subheader(f"Soru {mevcut_index + 1} / {toplam_soru}")

        # --- FİKSASYON ARTISI ---
        placeholder = st.empty()
        placeholder.markdown(
            "<h1 style='text-align:center; font-size:80px; margin:40px 0;'>+</h1>",
            unsafe_allow_html=True
        )
        time.sleep(0.5)
        placeholder.empty()

        kanal = st.session_state.secilen_kanal

        if kanal == "İşitsel":
            ses_dosyasi = sesi_sentezle(aktif_sozcuk, filtre_uygula=False)
            st.audio(ses_dosyasi, format="audio/mp3", autoplay=True)
            st.markdown(
                "<h1 style='text-align:center; font-size:60px; margin:40px 0;'>🔊</h1>",
                unsafe_allow_html=True
            )
        elif kanal == "Görsel":
            gosterilecek = turkce_buyut(aktif_sozcuk)
            st.markdown(
                f"<h1 style='text-align:center; font-size:60px; margin:40px 0;'>{gosterilecek}</h1>",
                unsafe_allow_html=True
            )

        if st.session_state.baslangic_zamani == 0:
            st.session_state.baslangic_zamani = time.time()

        st.write("---")
        st.write("### Gelen uyaran gerçek bir Türkçe sözcük mü?")
        col1, col2 = st.columns(2)

        def cevabi_kaydet(verilen_cevap):
            ts = (time.time() - st.session_state.baslangic_zamani) * 1000
            dogru_cevap = st.session_state.batarya[mevcut_index]["gercek_mi"]
            isabet = (verilen_cevap == dogru_cevap)
            st.session_state.sonuclar.append({
                "Sözcük": aktif_sozcuk,
                "Sözcük Türü": "Gerçek" if dogru_cevap else "Yalancı Sözcük",
                "Sunum Kanalı": st.session_state.secilen_kanal,
                "Katılımcı Yanıtı": (
                    "Gerçek" if verilen_cevap else "Yalancı Sözcük"
                ),
                "Doğruluk": isabet,
                "Tepki Süresi (ms)": round(ts, 2)
            })
            st.session_state.baslangic_zamani = 0
            st.session_state.mevcut_soru += 1
            if st.session_state.mevcut_soru >= toplam_soru:
                st.session_state.deney_bitti = True
                st.session_state.deney_basladi = False

        with col1:
            if st.button("✅ GERÇEK SÖZCÜK", use_container_width=True):
                cevabi_kaydet(True)
                st.rerun()
        with col2:
            if st.button("❌ YALANCI SÖZCÜK", use_container_width=True):
                cevabi_kaydet(False)
                st.rerun()

    elif st.session_state.deney_bitti:
        st.success("🎉 Deney Tamamlandı!")
        df_sonuclar = pd.DataFrame(st.session_state.sonuclar)
        st.dataframe(df_sonuclar, use_container_width=True)
        csv_sonuclar = df_sonuclar.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Tepki Süresi Sonuçlarını CSV İndir",
            data=csv_sonuclar,
            file_name="tepki_suresi_sonuclari.csv",
            mime="text/csv"
        )
        if st.button("🔄 Sıfırla ve Yeni Deney Yap"):
            st.session_state.deney_bitti = False
            st.session_state.deney_basladi = False
            st.rerun()
