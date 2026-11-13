import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

st.set_page_config(
    page_title="Türkçe Yalancı Sözcükler ve Sözcüksel Karar Görevi ",
    layout="wide"
)

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

def onses_sec(ilk_mi, onceki_tip, onceki_son):
    havuz = list(BAS_UNSUZ if ilk_mi else IC_UNSUZ)
    if onceki_tip == "unsuz":
        havuz = [u for u in havuz if u != 'ğ']
        if onceki_son in OTUMLU_ENGEL:
            havuz = [u for u in havuz if u not in SERT_UNSUZLER]
        elif onceki_son in SERT_UNSUZLER:
            havuz = [u for u in havuz if u not in OTUMLU_ENGEL]
    return random.choice(havuz)

def hece_uret(
    unlu_tipi, onceki_tip, onceki_son,
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
        return onses_sec(ilk_mi, onceki_tip, onceki_son) + unlu
    if yapi == "CVC":
        onses = onses_sec(ilk_mi, onceki_tip, onceki_son)
        return onses + unlu + sonses_sec(son_mi)
    if yapi == "VCC":
        return unlu + random.choice(SON_OBEKLER)
    if yapi == "CVCC":
        onses = onses_sec(ilk_mi, onceki_tip, onceki_son)
        return onses + unlu + random.choice(SON_OBEKLER)
    return unlu

def kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri=False):
    alt = min(alt_sinir, ust_sinir)
    ust = max(alt_sinir, ust_sinir)
    ses_sayisi = random.randint(alt, ust)
    unlu_tipi = random.choice(["kalin", "ince"])
    sozcuk = ""
    onceki_tip = ""
    onceki_son = ""
    unsuz_say = 0

    for i in range(ses_sayisi):
        ilk_mi = (i == 0)
        son_mi = (i == ses_sayisi - 1)
        hece = hece_uret(
            unlu_tipi, onceki_tip, onceki_son,
            unsuz_say, ilk_mi, son_mi, ileri
        )
        sozcuk += hece
        onceki_son = sozcuk[-1]

        if onceki_son in TUM_UNLULER:
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
    son_unlu = [h for h in sozcuk if h in TUM_UNLULER][-1]
    son_harf = sozcuk[-1]
    unsuz_son = son_harf in TUM_UNSUZLER
    sert_son = son_harf in SERT_UNSUZLER
    kalin = son_unlu in KALIN_ILK

    if ek_tipi == "cogul":
        return sozcuk + ("lar" if kalin else "ler")
    if ek_tipi == "bulunma":
        if sert_son:
            return sozcuk + ("ta" if kalin else "te")
        return sozcuk + ("da" if kalin else "de")
    if ek_tipi == "belirtme":
        kaynastirma = "" if unsuz_son else "y"
        ek_map = {'a': 'ı', 'ı': 'ı', 'e': 'i', 'i': 'i', 'o': 'u', 'u': 'u'}
        ek = ek_map.get(son_unlu, 'ü')
        return sozcuk + kaynastirma + ek
    if ek_tipi == "gecmis_zaman":
        d_t = "t" if sert_son else "d"
        ek_map = {
            'a': 'ılar', 'ı': 'ılar', 'e': 'iler', 'i': 'iler',
            'o': 'ular', 'u': 'ular', 'ö': 'üler', 'ü': 'üler'
        }
        return sozcuk + d_t + ek_map[son_unlu]
    if ek_tipi == "genis_zaman":
        if not unsuz_son:
            return sozcuk + "r"
        ek_map = {
            'a': 'ır', 'ı': 'ır', 'e': 'ir', 'i': 'ir',
            'o': 'ur', 'u': 'ur', 'ö': 'ür', 'ü': 'ür'
        }
        return sozcuk + ek_map[son_unlu]
    if ek_tipi == "bildirme":
        d_t = "t" if sert_son else "d"
        ek_map = {
            'a': 'ır', 'ı': 'ır', 'e': 'ir', 'i': 'ir',
            'o': 'ur', 'u': 'ur', 'ö': 'ür', 'ü': 'ür'
        }
        return sozcuk + d_t + ek_map[son_unlu]
    return sozcuk

def jabberwocky_tumcesi_uret(alt_sinir, ust_sinir, ileri=False):
    k1 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri)
    k2 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri)
    k3 = kuralli_sozcuk_uret(alt_sinir, ust_sinir, ileri)

    c1 = turkce_buyut(k1[:1]) + turkce_kucult(k1[1:])
    cerceveler = [
        f"{c1} çok {k2} bir {morfolojik_ek_getir(k3, 'bildirme')}.",
        f"{morfolojik_ek_getir(c1, 'cogul')} "
        f"{morfolojik_ek_getir(k2, 'bulunma')} "
        f"{morfolojik_ek_getir(k3, 'genis_zaman')}.",
        f"{c1} {morfolojik_ek_getir(k2, 'belirtme')} "
        f"{morfolojik_ek_getir(k3, 'gecmis_zaman')}."
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

# --- 2. STREAMLIT ARAYÜZÜ ---
for anahtar, varsayilan in [
    ('deney_basladi', False),
    ('deney_bitti', False),
    ('batarya', []),
    ('mevcut_soru', 0),
    ('sonuclar', []),
    ('baslangic_zamani', 0),
    ('secilen_kanal', "İşitsel")
]:
    if anahtar not in st.session_state:
        st.session_state[anahtar] = varsayilan

st.title("🧠 Klinik Dilbilimsel Yalancı Sözcük ve Tepki Süresi Deneyi")

sekme1, sekme2 = st.tabs([
    "⚙️ Bürünsel Uyarlama Üreteci",
    "⏱️ Sözcüksel Karar Görevi"
])

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

            ses_ciktisi = sesi_sentezle(". ".join(tumceler), filtre_uygula)
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

with sekme2:
    st.header("Sözcüksel Seçim Deneyi")

    if not st.session_state.deney_basladi and not st.session_state.deney_bitti:
        st.write("Lütfen deneyi hangi duyusal kanaldan almak istediğinizi seçin:")
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
        idx = st.session_state.mevcut_soru
        toplam = len(st.session_state.batarya)
        aktif = st.session_state.batarya[idx]["sozcuk"]

        st.progress(idx / toplam)
        st.subheader(f"Soru {idx + 1} / {toplam}")

        placeholder = st.empty()
        placeholder.markdown(
            "<h1 style='text-align:center; font-size:80px; margin:40px 0;'>+</h1>",
            unsafe_allow_html=True
        )
        time.sleep(0.5)
        placeholder.empty()

        kanal = st.session_state.secilen_kanal
        if kanal == "İşitsel":
            ses_dosyasi = sesi_sentezle(aktif, filtre_uygula=False)
            st.audio(ses_dosyasi, format="audio/mp3", autoplay=True)
            st.markdown(
                "<h1 style='text-align:center; font-size:60px; margin:40px 0;'>🔊</h1>",
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                f"<h1 style='text-align:center; font-size:60px; margin:40px 0;'>"
                f"{turkce_buyut(aktif)}</h1>",
                unsafe_allow_html=True
            )

        if st.session_state.baslangic_zamani == 0:
            st.session_state.baslangic_zamani = time.time()

        st.write("---")
        st.write("### Gelen uyaran gerçek bir Türkçe sözcük mü?")
        col1, col2 = st.columns(2)

        def cevabi_kaydet(verilen_cevap):
            ts = (time.time() - st.session_state.baslangic_zamani) * 1000
            dogru = st.session_state.batarya[idx]["gercek_mi"]
            st.session_state.sonuclar.append({
                "Sözcük": aktif,
                "Sözcük Türü": "Gerçek" if dogru else "Yalancı Sözcük",
                "Sunum Kanalı": st.session_state.secilen_kanal,
                "Katılımcı Yanıtı": (
                    "Gerçek" if verilen_cevap else "Yalancı Sözcük"
                ),
                "Doğruluk": (verilen_cevap == dogru),
                "Tepki Süresi (ms)": round(ts, 2)
            })
            st.session_state.baslangic_zamani = 0
            st.session_state.mevcut_soru += 1
            if st.session_state.mevcut_soru >= toplam:
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
        csv_sonuc = df_sonuclar.to_csv(index=False).encode('utf-8')
        st.download_button(
            "📥 Tepki Süresi Sonuçlarını CSV İndir",
            data=csv_sonuc,
            file_name="tepki_suresi_sonuclari.csv",
            mime="text/csv"
        )
        if st.button("🔄 Sıfırla ve Yeni Deney Yap"):
            st.session_state.deney_bitti = False
            st.session_state.deney_basladi = False
            st.rerun()
