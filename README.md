# Crypto Trading Bot

Bot do handlu kryptowalutami na Binance (Spot), działający w izolowanym środowisku Docker.

---

## 1. Wymagania

* [Docker](https://www.docker.com/products/docker-desktop/) zainstalowany na komputerze
* [Git](https://git-scm.com/) (jeśli chcesz pobierać projekt z GitHub)
* Klucz API Binance z uprawnieniami do handlu Spot

---

## 2. Zasada działania bota

Bot działa w oparciu o prostą strategię zarządzania kapitałem i reagowania na zmiany cen:

1. **Obliczanie wielkości pojedynczego zlecenia**  
   - Cały dostępny balans konta (PLN + BTC) dzielony jest przez **50**.  
   - Większy balans → większe zlecenia → większy potencjalny zysk.

2. **Brak aktywnego zlecenia sprzedaży**  
   - Jeśli **nie ma żadnej aktywnej oferty sprzedaży**, bot **kupuje BTC** za wyliczoną kwotę.  
   - Następnie **wystawia zlecenie sprzedaży** o **1% wyższe** niż średnia cena zakupu.

3. **Aktywne zlecenie sprzedaży**  
   - Jeśli istnieje **aktywny SELL**, bot monitoruje rynek.
   - Oblicza próg bezpieczeństwa:
     ```
     próg = (ATH * 1%) + (najniższa cena sprzedaży * 0,5%)
     ```
   - Jeśli **aktualna cena rynkowa spadnie poniżej tego progu**, bot **składa kolejne zlecenie kupna**.

4. **Pętla działania**  
   - Bot działa w pętli, co **5 sekund** aktualizując swoje decyzje i logując wszystkie zdarzenia do pliku `logbtcpln.txt`.

---

## 3. Struktura projektu

```
crypto-bot/
├─ main.py
├─ config.py
├─ .env
├─ requirements.txt
├─ .gitignore
└─ Dockerfile
```

---

## 4. Konfiguracja kluczy API

1. Utwórz plik `.env` w folderze projektu:

```
API_KEY=twój_prawdziwy_klucz
API_SECRET=twój_prawdziwy_secret
```

> **Uwaga:** Nie wgrywaj `.env` na GitHub ani nie udostępniaj publicznie.

2. `config.py` automatycznie pobiera zmienne z `.env`:

```python
from dotenv import load_dotenv
import os

load_dotenv()

API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
```

---

## 5. Budowa i uruchomienie Dockera

Otwórz terminal w folderze projektu i wykonaj:

```bash
# Budowa obrazu Dockera
docker build -t crypto-bot .

# Uruchomienie kontenera z plikiem .env
docker run -it --env-file .env crypto-bot
```

Bot uruchomi się w izolowanym środowisku i zacznie działać.

---

## 6. Uruchamianie projektu z GitHub na nowym komputerze

```bash
git clone https://github.com/MrDead1987/crypto-bot.git
cd crypto-bot
docker build -t crypto-bot .
docker run -it --env-file .env crypto-bot
```

---

## 7. Bezpieczeństwo

* Nigdy nie wrzucaj `.env` na GitHub.
* Zawsze używaj Docker lub virtualenv, aby nie zanieczyścić systemu lokalnego.
* Sprawdzaj uprawnienia API na Binance.

---

## 8. Rozwój i aktualizacje

* Dodawaj zmiany w `main.py` lub innych plikach.
* Używaj Git do wersjonowania:

```bash
git add .
git commit -m "Opis zmian"
git push origin main
```
