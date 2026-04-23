# ⚽ Football Analytics Dashboard - Praca Magisterska
## Wersja: v0.4 (Stable - SVG & xG Implementation)

Aplikacja webowa stworzona w ramach pracy magisterskiej, służąca do zaawansowanej analityki danych piłkarskich. Narzędzie łączy w sobie analizę statystyczną, wizualizację zdarzeń meczowych na autorskich grafikach SVG oraz predykcję prawdopodobieństwa goli za pomocą autorskiego modelu Machine Learning (Expected Goals - xG).

---

## 📸 Zrzuty Ekranu
*(Wskazówka: Zrób screeny i umieść je w folderze docs/screenshots/, aby stały się widoczne poniżej)*

### 📊 Widok Główny (Dashboard)
![Dashboard Screenshot](docs/screenshots/dashboard.png)

### 🥅 Analiza Meczów i Event Map
![Match Analysis Screenshot](docs/screenshots/matches.png)

### 📈 Model xG w Akcji
![xG Model Screenshot](docs/screenshots/xg_preview.png)

---

## 🚀 Kluczowe Funkcjonalności (v0.4)

- **Interaktywna Relacja Meczowa:** Chronologiczny podgląd wszystkich zdarzeń z automatycznym czyszczeniem błędów kodowania znaków (fix mojibake).
- **Autorska Wizualizacja SVG:** Wykorzystanie własnoręcznie przygotowanych plików `.svg` do mapowania zdarzeń na murawie oraz precyzyjnego pozycjonowania strzałów w świetle bramki.
- **Model Expected Goals (xG):** Implementacja modelu klasyfikacji binarnej (Random Forest), który w czasie rzeczywistym szacuje jakość oddanego strzału na podstawie lokalizacji, części ciała i kontekstu akcji.
- **Match Momentum:** Dynamiczny wykres ciśnienia meczowego, pokazujący dominację drużyn w 5-minutowych interwałach.

---

## 🏗️ Struktura Aplikacji

Aplikacja jest podzielona na dedykowane moduły analityczne:

### 1. 🏠 Dashboard
Ogólne podsumowanie rozgrywek. Statystyki ligowe, tabele i główne wskaźniki efektywności dla wybranego sezonu.

### 2. ⚽ Analiza Meczów
Serce aplikacji. Pozwala na:
- Wybór konkretnego spotkania.
- Przegląd szczegółowej relacji tekstowej.
- **Event Map:** Wybranie dowolnego strzału z listy wyświetla jego dokładną lokalizację na pionowym boisku oraz punkt trafienia w bramkę.
- **Live xG:** Każdy strzał jest oceniany przez model ML pod kątem prawdopodobieństwa zdobycia bramki.

### 3. 🏃 Analiza Zawodników
Szczegółowy wgląd w formę poszczególnych graczy. Statystyki indywidualne, dystrybucja strzałów i kluczowych podań.

### 4. 🧠 ML Analysis
Sekcja poświęcona "bebechom" modelu Machine Learning. Wyjaśnienie wag poszczególnych cech (Features) i metryki skuteczności modelu (Brier Score, ROC AUC).

---

## 🛠️ Stack Techniczny

- **Język:** Python 3.x
- **Frontend:** [Streamlit](https://streamlit.io/)
- **Wizualizacje:** [Plotly](https://plotly.com/python/) & Custom SVG
- **Machine Learning:** [Scikit-learn](https://scikit-learn.org/)
- **Przetwarzanie danych:** Pandas, Numpy
- **Wersjonowanie modeli:** Joblib

---

## ⚙️ Instalacja i Uruchomienie

1. Sklonuj repozytorium:
   ```bash
   git clone [https://github.com/TwojLogin/Praca_mgr_2026.git](https://github.com/TwojLogin/Praca_mgr_2026.git)
   ```bash

   2. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```bash
