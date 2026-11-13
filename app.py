import random
import time
import io
import pandas as pd
import streamlit as st
from gtts import gTTS
from pydub import AudioSegment

st.set_page_config(
    page_title="Türkçe Yalancı Sözcükler ve Sözcüksel Karar Görevi",
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

# Temel referans Türkçe sözlükçe (Komşuluk ve Olasılık hesabı için)
VARSAYILAN_SOZLUKCE = [
    "masa", "kasa", "yasa", "tasa", "paşa", "maşa", "kalem", "kelam",
    "defter", "çanta", "kapı", "yapı", "sapı", "tapı", "güneş", "deniz",
    "beniz", "geniz", "kitap", "hitap", "bardak", "çardak", "yıldız",
    "orman", "harman", "kedi", "yedi", "dedi", "beli", "deli", "veli",
    "seli", "teli", "elma", "alma", "armut", "kiraz", "üzüm", "kavun",
    "karpuz", "ekmek", "yemek", "börek", "çörek", "kürek", "yürek",
    "çiçek", "böcek", "kepek", "köpek", "bebek", "göbek", "elek",
    "melek", "yelek", "felek", "çilek", "dilek", "bilek", "okul",
    "okur", "oyun", "koyun", "boyun", "burun", "fırın", "yarın",
    "karın", "kalın", "yalın", "balık", "salık", "alık", "açık",
    "kaşık", "beşik", "eşik", "ışık", "aşık", "bıçak", "uçak",
    "sıcak", "kucak", "ocak", "bacak", "saçak", "kaçak", "yatak",
    "batak", "çatak", "ortak", "mutfak", "bardak", "yaprak", "toprak",
    "bayrak", "kaynak", "parmak", "ırmak", "tırnak", "durak", "kurak",
    "uzak", "tuzak", "kızak", "kazak", "yüzük", "üzük", "sözlük",
    "gözlük", "kömür", "ömür", "demir", "emir", "hamur", "çamur",
    "yağmur", "maymun", "sabun", "odun", "oyuncak", "salıncak",
    "bilgi", "silgi", "sevgi", "çizgi", "ezgi", "dergi", "vergi",
    "örgü", "sorgu", "kurgu", "duygu", "kaygı", "saygı", "yaygı",
    "yolcu", "kolcu", "solcu", "korucu", "kurucu", "sürücü", "binici",
    "satıcı", "alıcı", "bakıcı", "yakıcı", "yıkıcı", "akıcı", "çekici",
    "kesici", "delici", "geçici", "seçici", "içici", "açıcı", "saçıcı",
    "araba", "akraba", "kasaba", "pencere", "tencere", "testere",
    "kelebek", "örümcek", "karınca", "kaplumbağa", "kurbağa", "balina"
]

GERCEK_SOZCUKLER = [
    "masa", "kalem", "defter", "çanta", "kapı", "güneş",
    "deniz", "kitap", "bardak", "yıldız", "orman", "kedi"
]

# --- 2. PSİKODİLBİLİMSEL DEĞİŞKEN HESAPLAYICILAR ---
def levenshtein_bir_mi(s1, s2):
    uzunluk_farki = abs(len(s1) - len(s2))
    if uzunluk_farki > 1:
        return False
    if s1 == s2:
        return False
    if len(s1) == len(s2):
        fark = sum(1 for a, b in zip(s1, s2) if a != b)
        return fark == 1
    if len(s1) > len(s2):
        s1, s2 = s2, s1
    i, j, fark = 0, 0, 0
    while i < len(s1) and j < len(s2):
        if s1[i] != s2[j]:
            fark += 1
            if fark > 1:
                return False
            j += 1
        else:
            i += 1
            j += 1
    return True

def komsu_analizi(sozcuk, sozlukce):
    komsular = [w for w in sozlukce if levenshtein_bir_mi(sozcuk, w)]
    komsular = sorted(list(set(komsular)))
    return len(komsular), ", ".join(komsular[:5]) if komsular else "-"

def bigram_tablosu_olustur(sozlukce):
    sayac = {}
    toplam = 0
    for w in sozlukce:
        temiz = f"^{turkce_kucult(w)}$"
        for i in range(len(temiz) - 1):
            ikili = temiz[i:i+2]
            sayac[ikili] = sayac.get(ikili, 0) + 1
            toplam += 1
    if toplam == 0:
        return {}
    return {k: v / toplam for k, v in sayac.items()}

def sesdizimsel_olasilik(sozcuk, bigram_olasiliklari):
    temiz = f"^{turkce_kucult(sozcuk)}$"
    if len(temiz) < 2 or not bigram_olasiliklari:
        return 0.0, "Düşük"
    skorlar = []
    for i in range(len(temiz) - 1):
        ikili = temiz[i:i+2]
        skorlar.append(bigram_olasiliklari.get(ikili, 0.0))
    ort = sum(skorlar) / len(skorlar)
    yuzde_skor = round(ort * 100, 3)
    if yuzde_skor >= 1.2:
        duzey = "Yüksek"
    elif yuzde_skor >= 0.5:
        duzey = "Orta"
    else:
        duzey = "Düşük"
    return yuzde_skor, duzey

# --- 3. SESDİZİMSEL ÜRETİM MOTORU ---
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

# --- 4. STREAMLIT ARAYÜZÜ ---
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

# Yan panel: Referans sözlükçe yükleme
with st.sidebar:
    st.header("📚 Referans Sözlükçe")
    st.caption(
        "Komşuluk yoğunluğu (N) ve sesdizimsel olasılık hesabı "
        "için Türkçe sözlükçe listesi kullanılır."
    )
    yuklenen_dosya = st.file_uploader(
        "Özel Sözlükçe Yükle (.txt veya .csv)",
        type=["txt", "csv"]
    )
    aktif_sozlukce = list(VARSAYILAN_SOZLUKCE)
    if yuklenen_dosya is not None:
        icerik = yuklenen_dosya.getvalue().decode("utf-8", errors="ignore")
        ek_sozcukler = [
            turkce_kucult(s.strip().split(",")[0])
            for s in icerik.splitlines()
            if s.strip()
        ]
        aktif_sozlukce = list(set(aktif_sozlukce + ek_sozcukler))
    st.info(f"Aktif Sözlükçe Hacmi: {len(aktif_sozlukce)} sözcük")

bigram_tablosu = bigram_tablosu_olustur(aktif_sozlukce)

sekme1, sekme2 = st.tabs([
    "⚙️ Bürünsel Uyarlama Üreteci",
    "⏱️ Sözcüksel Karar Deneyi"
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
        with st.spinner("Üretiliyor ve psikodilbilimsel değerler hesaplanıyor..."):
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

            st.subheader("📋 Tekil Uyaran Listesi ve Psikodilbilimsel Değişkenler")
            satirlar = []
            for s in sozcukler:
                komsu_say, komsu_ornek = komsu_analizi(s, aktif_sozlukce)
                olasilik_skor, olasilik_duzey = sesdizimsel_olasilik(
                    s, bigram_tablosu
                )
                satirlar.append({
                    "Yalancı Sözcük": s,
                    "Harf Uzunluğu": len(s),
                    "Komşuluk Yoğunluğu (N)": komsu_say,
                    "Komşu Sözcükler": komsu_ornek,
                    "Sesdizimsel Olasılık (%)": olasilik_skor,
                    "Olasılık Düzeyi": olasilik_duzey
                })

            df = pd.DataFrame(satirlar)
            st.dataframe(df, use_container_width=True)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                "📥 Kontrol Değişkenli Listeyi CSV Olarak İndir",
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
            komsu_say, _ = komsu_analizi(aktif, aktif_sozlukce)
            olasilik_skor, _ = sesdizimsel_olasilik(aktif, bigram_tablosu)
            st.session_state.sonuclar.append({
                "Sözcük": aktif,
                "Sözcük Türü": "Gerçek" if dogru else "Yalancı Sözcük",
                "Komşuluk Yoğunluğu (N)": komsu_say,
                "Sesdizimsel Olasılık (%)": olasilik_skor,
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
