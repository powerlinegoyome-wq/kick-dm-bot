"""
Kick → Telegram DM Botu
Birden fazla yayıncıyı takip eder, yayın başlayınca DM gönderir.
"""

import os
import requests

BOT_TOKEN   = os.environ["TELEGRAM_BOT_TOKEN"]
USER_ID     = os.environ["TELEGRAM_USER_ID"]
GH_TOKEN    = os.environ["GH_TOKEN"]
GH_REPO     = os.environ["GH_REPO"]

YAYINCILAR = [
    "swaggybark",
    "jahrein",
    "erlizzy",
    "caglararts",
    "buraksakinol",
    "burhi",
]

TG_URL  = f"https://api.telegram.org/bot{BOT_TOKEN}"
GH_API  = f"https://api.github.com/repos/{GH_REPO}/actions/variables"
GH_HEADERS = {
    "Authorization": f"Bearer {GH_TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
}
KICK_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json",
}


def gh_var_oku(isim: str, varsayilan: str = "") -> str:
    try:
        r = requests.get(f"{GH_API}/{isim}", headers=GH_HEADERS, timeout=10)
        if r.status_code == 200:
            return r.json().get("value", varsayilan)
    except Exception as e:
        print(f"Variable okuma hatası ({isim}): {e}")
    return varsayilan


def gh_var_yaz(isim: str, deger: str):
    try:
        r = requests.get(f"{GH_API}/{isim}", headers=GH_HEADERS, timeout=10)
        if r.status_code == 200:
            requests.patch(f"{GH_API}/{isim}", headers=GH_HEADERS,
                           json={"value": deger}, timeout=10)
        else:
            requests.post(GH_API, headers=GH_HEADERS,
                          json={"name": isim, "value": deger}, timeout=10)
    except Exception as e:
        print(f"Variable yazma hatası ({isim}): {e}")


def kick_durumu_al(kullanici: str) -> dict | None:
    try:
        r = requests.get(
            f"https://kick.com/api/v2/channels/{kullanici}",
            headers=KICK_HEADERS, timeout=10
        )
        r.raise_for_status()
        veri = r.json()
        ls = veri.get("livestream")
        if ls:
            kategoriler = ls.get("categories", [])
            kategori = kategoriler[0].get("name", "Bilinmiyor") if kategoriler else "Bilinmiyor"
            return {
                "canli": True,
                "baslik": ls.get("session_title", "Başlık yok"),
                "kategori": kategori,
                "izleyici": ls.get("viewer_count", 0),
                "url": f"https://kick.com/{kullanici}",
            }
        return {"canli": False}
    except Exception as e:
        print(f"Kick API hatası ({kullanici}): {e}")
        return None


def telegram_gonder(mesaj: str):
    try:
        r = requests.post(f"{TG_URL}/sendMessage", json={
            "chat_id": USER_ID,
            "text": mesaj,
            "parse_mode": "HTML",
        }, timeout=10)
        r.raise_for_status()
        print(f"✅ DM gönderildi.")
    except Exception as e:
        print(f"❌ Telegram hatası: {e}")


def main():
    for kullanici in YAYINCILAR:
        print(f"🔍 Kontrol: kick.com/{kullanici}")

        durum = kick_durumu_al(kullanici)
        if durum is None:
            continue

        var_ismi = f"DURUM_{kullanici.upper()}"
        simdi_canli  = durum["canli"]
        onceki_canli = gh_var_oku(var_ismi, "false").lower() == "true"

        print(f"  Önceki: {'🔴 Canlı' if onceki_canli else '⚫ Offline'} | "
              f"Şimdi: {'🔴 Canlı' if simdi_canli else '⚫ Offline'}")

        if simdi_canli and not onceki_canli:
            mesaj = (
                f"🔴 <b>{kullanici} YAYINDA!</b>\n\n"
                f"🎮 <b>Kategori:</b> {durum['kategori']}\n"
                f"📺 <b>Başlık:</b> {durum['baslik']}\n"
                f"👥 <b>İzleyici:</b> {durum['izleyici']}\n\n"
                f"👉 <a href=\"{durum['url']}\">Yayına katıl!</a>"
            )
            telegram_gonder(mesaj)

        elif not simdi_canli and onceki_canli:
            telegram_gonder(f"⏹️ <b>{kullanici}</b> yayını kapattı.")

        gh_var_yaz(var_ismi, "true" if simdi_canli else "false")


if __name__ == "__main__":
    main()

