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
Pierwsza sekcja aplikacji służy do szybkiego przeglądu kondycji ligi i wybranych sezonów. Wyświetla tabele ligowe, rankingi strzelców oraz kluczowe metryki efektywności zespołów.

<img width="1866" height="1197" alt="Dashboard View" src="https://github.com/user-attachments/assets/789c2a86-d8c6-48f6-9b04-44f1127a1019" />

**Narzędzia w tej zakładce:**
- **Selektor Sezonów:** Pozwala na filtrowanie danych historycznych.
- **Tabela Ligowa:** Generowana dynamicznie na podstawie przetworzonych zdarzeń meczowych.
- **KPI Cards:** Najważniejsze statystyki zbiorcze wyświetlane w formie czytelnych kart.

---

### 2. ⚽ Analiza Meczów i Event Map
To serce aplikacji, pozwalające na dogłębną analizę pojedynczego spotkania. Umożliwia wizualizację każdego strzału w dwóch płaszczyznach: pozycji na boisku oraz punktu trafienia w bramkę.

<img width="1864" height="3053" alt="Match Analysis" src="https://github.com/user-attachments/assets/8eacbbde-f5f4-4bc9-acc4-e220510ee42f" />

**Kluczowe moduły:**
- **Event Map (SVG):** Autorski system mapowania współrzędnych strzału na pionowy rzut boiska oraz czołowy rzut bramki.
- **Live xG Calculator:** Dla każdego wybranego strzału model ML oblicza prawdopodobieństwo zdobycia bramki na podstawie:
    - *Lokalizacji:* Dystansu i kąta względem bramki.
    - *Body Part:* Czy strzał oddano nogą, czy głową.
    - *Situation:* Kontekst akcji (np. z gry, rzut wolny, rzut karny).
- **Match Momentum Chart:** Wykres słupkowy pokazujący skumulowane zagrożenie (threat) w 5-minutowych interwałach, ułatwiający identyfikację momentów dominacji.

---

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
