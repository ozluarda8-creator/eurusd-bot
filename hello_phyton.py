import time
import requests
import pandas as pd
import yfinance as yf

# --- TELEGRAM AYARLARI ---
TELEGRAM_TOKEN = "9251631848:AAEPmb-nr0o2k6ZUjxHXilDUVUTe2IPfSIc"
CHAT_ID = "6450908031"


def telegram_bildirimi_gonder(mesaj):
  url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
  payload = {"chat_id": CHAT_ID, "text": mesaj}
  try:
    requests.post(url, json=payload)
  except Exception as e:
    print("Telegram mesajı gönderilemedi:", e)


print("Kesişen IFVG (BPR) Algoritması başlatılıyor...")
bilinen_sinyaller = set()

# Geçmiş verileri ilk başta tarayıp hafızaya atıyoruz ki eski yapılar spam yapmasın
euro = yf.Ticker("EURUSD=X")
df_init = euro.history(period="5d", interval="1h")
for i in range(15, len(df_init)):
  bilinen_sinyaller.add(f"init_bpr_{i}")

telegram_bildirimi_gonder(
    "🤖 Kesişen IFVG / BPR Strateji Botu Devrede! Yeni formasyonlar bekleniyor..."
)
print("Sistem hazır! Likidite, kesişen FVG ve gövde ihlalleri taranıyor...")

while True:
  try:
    euro = yf.Ticker("EURUSD=X")
    df = euro.history(period="5d", interval="1h")

    # Son mumlar üzerinde BPR ve Kesişen IFVG Şartlarını Tarıyoruz
    for i in range(15, len(df) - 2):
      m_prev1 = df.iloc[i - 2]
      m_prev2 = df.iloc[i - 1]
      current_candle = df.iloc[i]

      # Likidite Bölgesi (Son 10 mumun tepe veya dipleri)
      recent_high = df.iloc[i - 10 : i - 2]["High"].max()
      recent_low = df.iloc[i - 10 : i - 2]["Low"].min()

      # 1. AŞAMA: Likidite Alımı ve 1. FVG Tespiti
      # Örneğin Bullish FVG ve dip likiditesi süpürmesi
      if (
          df.iloc[i - 3]["Low"] < recent_low
          and df.iloc[i - 4]["High"] < df.iloc[i - 2]["Low"]
      ):
        # 1. FVG Sınırları (Referans Alanı)
        fvg1_alt = df.iloc[i - 4]["High"]
        fvg1_ust = df.iloc[i - 2]["Low"]

        # 2. AŞAMA: Zıt Yöne Kopuş ve İkinci FVG (Kesişim / Overlap Şartı)
        # Sert dönüşle zıt yönlü FVG oluşumu aranır
        for j in range(i, len(df) - 2):
          k1 = df.iloc[j]
          k3 = df.iloc[j + 2]

          # Zıt FVG (Bearish FVG oluşumu ve kesişim kontrolü)
          if k1["Low"] > k3["High"]:
            fvg2_alt = k3["High"]
            fvg2_ust = k1["Low"]

            # Kesişim (Overlap) Kontrolü: İki FVG fiyat aralığı iç içe geçmeli
            overlap = max(0, min(fvg1_ust, fvg2_ust) - max(fvg1_alt, fvg2_alt))

            if overlap > 0:  # Kesişim varsa BPR (Balanced Price Range) oluşmuştur
              # 3. AŞAMA: Gövde Kapanışı ile İhlal (IFVG Onayı)
              # Sonraki mumların GÖVDESİ 1. FVG'nin dışına çıkıp kapanış yapmalı
              break_candle = df.iloc[j + 3]
              body_top = max(break_candle["Open"], break_candle["Close"])
              body_bottom = min(break_candle["Open"], break_candle["Close"])

              # Gövde tamamen dışarıda kapandı mı? (Sadece iğne olmayacak)
              if body_bottom > fvg1_ust or body_top < fvg1_alt:
                formasyon_id = f"bpr_ifvg_{df.index[j+3]}"

                if formasyon_id not in bilinen_sinyaller:
                  bildiri = (
                      f"🔥 KESİŞEN IFVG (BPR) ONAYLANDI!\n"
                      f"Parite: EURUSD\n"
                      f"Zaman: {df.index[j+3]}\n"
                      f"Durum: Likidite alındı, FVG'ler kesişti ve gövde ihlali gerçekleşti!\n"
                      f"Referans Seviye: {fvg1_alt:.5f} - {fvg1_ust:.5f}"
                  )
                  telegram_bildirimi_gonder(bildiri)
                  bilinen_sinyaller.add(formasyon_id)
                  print(f"Yeni BPR / IFVG yakalandı: {df.index[j+3]}")

    print(
        f"[{time.strftime('%H:%M:%S')}] Tarama tamamlandı. Yeni mumlar"
        " bekleniyor..."
    )

  except Exception as e:
    print("Hata oluştu:", e)

  # Her 1 saatte bir piyasayı yeniden kontrol eder
  time.sleep(3600)