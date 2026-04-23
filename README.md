# ⚽ Football Analytics Dashboard - Praca Magisterska
## Wersja: v0.4 (Stable - SVG & xG Implementation)

Aplikacja webowa stworzona w ramach pracy magisterskiej, służąca do zaawansowanej analityki danych piłkarskich. Narzędzie łączy w sobie analizę statystyczną, wizualizację zdarzeń meczowych na autorskich grafikach SVG oraz predykcję prawdopodobieństwa goli za pomocą autorskiego modelu Machine Learning.

---

## 🚀 Kluczowe Funkcjonalności (v0.4)

- **Interaktywna Relacja Meczowa:** Chronologiczny podgląd wszystkich zdarzeń z automatycznym czyszczeniem błędów kodowania znaków (fix mojibake).
- **Autorska Wizualizacja SVG:** Wykorzystanie autorskich plików `.svg` do mapowania zdarzeń na murawie oraz precyzyjnego pozycjonowania strzałów w świetle bramki.
- **Model Expected Goals (xG):** Implementacja modelu klasyfikacji binarnej (Random Forest), który w czasie rzeczywistym szacuje jakość oddanego strzału.
- **Match Momentum:** Dynamiczny wykres "ciśnienia" meczowego, pokazujący dominację drużyn w czasie.

---

## 🏗️ Szczegółowa Struktura i Zakładki

### 1. 🏠 Dashboard - Statystyki Ogólne
Główny panel analityczny służący do agregacji i wizualizacji danych na poziomie całych lig, sezonów lub konkretnych drużyn. 

<img width="1866" height="1197" alt="Dashboard View" src="https://github.com/user-attachments/assets/789c2a86-d8c6-48f6-9b04-44f1127a1019" />

**Kluczowe elementy zakładki:**
- **🎛️ Panel Filtrów:** Kaskadowy system wyboru (Liga -> Sezon -> Klub), który dynamicznie aktualizuje wszystkie wykresy poniżej.
- **Rozkład zdarzeń (Wykres Kołowy):** Wizualizuje proporcje poszczególnych typów zdarzeń meczowych (faule, strzały, kartki, rożne) dla wybranego filtru.
- **Kiedy padają bramki? (Histogram):** Analiza rozkładu czasowego strzelanych goli, pogrupowana w czytelne, 10-minutowe okna czasowe (binning).
- **Statystyki dyscyplinarne:** Dodatkowy wykres słupkowy (aktywny po wybraniu konkretnego klubu), analizujący dystrybucję otrzymanych kartek.

---

### 2. ⚽ Analiza Meczów i Event Map
To serce aplikacji, pozwalające na dogłębną, mikroskopijną analizę pojedynczego spotkania. Umożliwia szczegółowy podgląd osi czasu oraz wizualizację każdego strzału.

<img width="1864" height="3053" alt="Match Analysis" src="https://github.com/user-attachments/assets/8eacbbde-f5f4-4bc9-acc4-e220510ee42f" />

**Kluczowe elementy zakładki:**
- **Relacja z meczu (Play-by-play):** Interaktywna, posortowana chronologicznie tabela zawierająca szczegółowe opisy wszystkich akcji (wzbogacona o funkcję dekodowania błędnych znaków tekstowych).
- **Live xG Calculator:** Predykcja w czasie rzeczywistym. Na podstawie wczytanego z pliku `.joblib` modelu Random Forest, algorytm analizuje wektor cech (lokalizacja, typ asysty, część ciała, kontekst) i błyskawicznie zwraca szacowane prawdopodobieństwo zdobycia bramki (Expected Goals).
- **Wizualizacja SVG (Event Map):** Autorski system mapowania strzału na dwa niezależne, niestandardowe wykresy Plotly z tłem SVG:
    - *Lokalizacja na murawie:* Pionowy rzut boiska pokazujący miejsce oddania strzału.
    - *Miejsce strzału:* Czołowy rzut bramki pokazujący punkt, w który poleciała (lub wpadła) piłka.
- **Wskaźnik zagrożenia (Match Momentum):** Wykres słupkowy pokazujący skumulowaną presję (punkty przyznawane za gole, strzały i rzuty rożne) obu drużyn w 5-minutowych interwałach, z wyraźnie zaznaczoną przerwą między połowami.

### 3. 🏃 Analiza Zawodników
Moduł skupiony na indywidualnych osiągnięciach graczy. Pozwala na porównywanie efektywności zawodników oraz analizę ich map strzałów (Shot Maps) w ujęciu całego sezonu.

### 4. 🧠 ML Analysis - Detale Modelu
Sekcja techniczna prezentująca jakość wytrenowanego modelu xG. Zawiera:
- **Feature Importance:** Które parametry (np. lokalizacja, asysta) mają największy wpływ na szacowane xG.
- **Metrics:** Wyniki Brier Score oraz ROC AUC potwierdzające skuteczność predykcyjną modelu.

---

## 🛠️ Stack Techniczny

- **Język:** Python 3.x
- **Frontend:** [Streamlit](https://streamlit.io/) - szybka budowa interfejsów analitycznych.
- **Wizualizacje:** [Plotly](https://plotly.com/python/) & Custom SVG - dynamiczne i skalowalne grafiki.
- **Machine Learning:** [Scikit-learn](https://scikit-learn.org/) - model Random Forest do obliczeń xG.
- **Przetwarzanie danych:** Pandas, Numpy - manipulacja ramkami danych.
- **Wersjonowanie modeli:** Joblib - zapis i odczyt wytrenowanych wag modelu.

---

## ⚙️ Instalacja i Uruchomienie

1. Sklonuj repozytorium:
   ```bash
   git clone [https://github.com/TwojLogin/Praca_mgr_2026.git](https://github.com/TwojLogin/Praca_mgr_2026.git)
   ```
2. Zainstaluj wymagane biblioteki:
   ```bash
   pip install -r requirements.txt
   ```
2. Uruchom aplikację:
   ```bash
   streamlit run app.py
   ```
