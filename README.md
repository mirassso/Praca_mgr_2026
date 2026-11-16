# Przestrzenna analiza danych meczowych w piłce nożnej ⚽📊

Projekt interaktywnego systemu analitycznego wspomagającego proces analizy taktycznej i skautingu w piłce nożnej. Aplikacja transformuje surowe, wielowymiarowe zbiory danych meczowych (event data) w czytelne panele analityczne, wykorzystując przestrzenne wizualizacje, autorskie modele uczenia maszynowego (xG) oraz integrację z generatywną sztuczną inteligencją do tworzenia gotowych raportów.

Projekt zrealizowany w ramach pracy magisterskiej na kierunku Informatyka Stosowana (Politechnika Krakowska).

## 🚀 Główne funkcjonalności systemu

Aplikacja została podzielona na modułowe zakładki analityczne, pozwalające na płynne przechodzenie od oceny makrotaktycznej do analizy pojedynczych zdarzeń:
<img width="886" height="391" alt="image" src="https://github.com/user-attachments/assets/8f2b8d55-cf10-466a-89ee-4f91a2f10277" />

### 1. Dashboard i Nawigacja
Centrum informacyjne pozwalające na filtrowanie rozgrywek i sezonów. Zawiera dynamicznie generowaną tabelę ligową (obliczaną na podstawie iteracji przez wyniki) oraz moduł zaawansowanej analizy wyciągający najlepszych strzelców, kreatorów i najlepiej broniących zawodników.
![Dashboard - Główny widok]
<img width="886" height="211" alt="image" src="https://github.com/user-attachments/assets/e8945648-397f-409c-a423-964eabf4b1c9" />
<img width="886" height="387" alt="image" src="https://github.com/user-attachments/assets/98b46c0c-efb8-42eb-94ec-6634100d730d" />
<img width="886" height="838" alt="image" src="https://github.com/user-attachments/assets/9177e84b-b897-449a-9832-7fff160f8f84" />
<img width="856" height="386" alt="image" src="https://github.com/user-attachments/assets/aef11b99-2a83-466e-a6cc-aa49a4564fbf" />


### 2. Analiza zdarzeń meczowych
Szczegółowa wizualizacja przestrzenna akcji z konkretnego spotkania. Obejmuje mapę strzałów nałożoną na grafikę wektorową boiska (dzięki transformacji liniowej współrzędnych) oraz precyzyjną lokalizację punktu końcowego strzału w świetle bramki.
![Analiza Zdarzeń - Mapa Strzałów]
<img width="705" height="229" alt="image" src="https://github.com/user-attachments/assets/e7dba982-71e2-48a7-8cee-1ab51b81eeef" />
<img width="886" height="473" alt="image" src="https://github.com/user-attachments/assets/30a44d7f-2c9e-4771-855c-e817a9205c37" />
<img width="886" height="300" alt="image" src="https://github.com/user-attachments/assets/b90c8db4-6762-479d-ac35-0a681fc86b8a" />


### 3. Zaawansowana Analiza Zawodników
Narzędzie skautingowe agregujące tysiące zdarzeń. Statystyki zawodników przeliczane są na wskaźnik per 90 minut (p90) i pozycjonowane za pomocą percentyli na interaktywnym wykresie radarowym. Moduł pozwala również na weryfikację przestrzennej dystrybucji podań (w tym podań progresywnych) w wybranych meczach.
![Analiza Zawodnika - Wykres Radarowy]
<img width="853" height="686" alt="image" src="https://github.com/user-attachments/assets/7ceca109-25c5-496a-87dd-d84bd8e1ed76" />
<img width="886" height="700" alt="image" src="https://github.com/user-attachments/assets/9ae41782-c27b-4385-bcaf-c003d8036325" />
<img width="886" height="506" alt="image" src="https://github.com/user-attachments/assets/0c4b927c-dbf1-428c-9aa6-c5911ad06a8b" />


### 4. Przebieg Spotkania (Match Momentum)
Moduł ilustrujący dynamikę meczu. Zawiera wykres schodkowy skumulowanego wskaźnika Expected Goals (xG) oraz autorski algorytm **Match Momentum** (oparty na 5-okresowej średniej kroczącej), który na bieżąco analizuje inicjatywę i dominację obu drużyn na podstawie akcji konstruktywnych.
![Przebieg Spotkania - Match Momentum]
<img width="886" height="436" alt="image" src="https://github.com/user-attachments/assets/8cfcfddd-5b78-4c4a-b9b1-d4d5eabc12e2" />
<img width="886" height="349" alt="image" src="https://github.com/user-attachments/assets/70a60a8a-d038-4207-b7af-899160753198" />
<img width="886" height="277" alt="image" src="https://github.com/user-attachments/assets/864dd0c1-32d0-49f2-b650-6cbb3663e38e" />
<img width="886" height="390" alt="image" src="https://github.com/user-attachments/assets/34754488-c134-4a46-afcc-54c0200afd3f" />


### 5. Raporty Taktyczne AI (Google Gemini)
Innowacyjny moduł wnioskujący, który syntetyzuje statystyki i percentyle, wysyłając je do dużego modelu językowego (LLM) z rygorystycznym promptem. W odpowiedzi system generuje profesjonalny, tekstowy raport skautingowy oceniający atuty, braki i styl gry (zawodnika lub całej drużyny). Całość można wyeksportować do wygenerowanego programistycznie dokumentu PDF (wraz z przekonwertowanymi na jasny motyw wykresami).
![Raporty AI - Podsumowanie i PDF]
<img width="886" height="378" alt="image" src="https://github.com/user-attachments/assets/18165a0a-adb1-46e2-a6ca-4f3af7c4207e" />
<img width="886" height="269" alt="image" src="https://github.com/user-attachments/assets/15ea3734-cb5a-4106-a309-75d91cd2ac56" />
<img width="886" height="145" alt="image" src="https://github.com/user-attachments/assets/de7ea516-b160-4755-9c05-1d87830488f4" />
<img width="886" height="403" alt="image" src="https://github.com/user-attachments/assets/8751edd0-bace-48d4-90e3-ff0f1716d2c6" />
<img width="886" height="597" alt="image" src="https://github.com/user-attachments/assets/33b16507-f322-4b29-9cb6-04d2ad5b1ffc" />
<img width="886" height="466" alt="image" src="https://github.com/user-attachments/assets/6616c801-a6b6-4c01-a20d-9e8699561dba" />
<img width="886" height="178" alt="image" src="https://github.com/user-attachments/assets/d1187e30-186a-4bfe-820b-3bd7917b67fb" />

<img width="886" height="1002" alt="image" src="https://github.com/user-attachments/assets/3dec7eb5-2cd1-4278-8a86-9a534226b03b" />
<img width="884" height="1327" alt="image" src="https://github.com/user-attachments/assets/eb42eeee-fa22-44de-86b0-5de626a23fca" />

<img width="886" height="227" alt="image" src="https://github.com/user-attachments/assets/75e4969b-6e70-4d9e-9360-c9f9ee83c185" />
<img width="886" height="135" alt="image" src="https://github.com/user-attachments/assets/4461e52f-0600-42c0-9a4f-cbffbc79c1ac" />
<img width="886" height="139" alt="image" src="https://github.com/user-attachments/assets/8029d83e-13ff-499f-aa4d-e08f787e2f64" />
<img width="886" height="316" alt="image" src="https://github.com/user-attachments/assets/316173e6-159f-4aef-b03f-6b7acf6967b3" />
<img width="886" height="158" alt="image" src="https://github.com/user-attachments/assets/d299c902-5404-47af-bb9a-7ecf938cf81c" />

<img width="884" height="431" alt="image" src="https://github.com/user-attachments/assets/2e099244-42f2-4f6d-81ee-4c93e333f0f2" />
<img width="886" height="1075" alt="image" src="https://github.com/user-attachments/assets/616d5a50-42e0-4ae6-abcf-6368457ff595" />
<img width="886" height="158" alt="image" src="https://github.com/user-attachments/assets/2e4bcd09-6465-4ecc-b4a1-7862a3d029fe" />


### 6. Modele Predykcyjne i Porównanie xG
Silnik wyliczający oczekiwane gole (Expected Goals) oparty na zaawansowanej inżynierii cech. Moduł pozwala na bezpośrednią, wizualną konfrontację autorskich modeli z rynkowym standardem od StatsBomb na wykresie rozrzutu (Scatter Plot).
![Porównanie Modeli xG]
<img width="886" height="391" alt="image" src="https://github.com/user-attachments/assets/d4a256d0-7ad2-4e27-a0a6-2a7de83c8239" />
<img width="886" height="577" alt="image" src="https://github.com/user-attachments/assets/595ef5a0-be54-4308-850b-0d8db3869a2e" />
<img width="886" height="389" alt="image" src="https://github.com/user-attachments/assets/52a831d9-6938-4809-b4f2-5ea28f1c0a45" />

---

## 🧠 Uczenie Maszynowe i Inżynieria Danych

Zamiast polegać wyłącznie na gotowych wyliczeniach, w projekcie stworzono własny system oceny trudności sytuacji strzeleckich na podstawie otwartych danych.
* **Dane wejściowe:** Zdarzenia i tzw. *freeze frames* (zamrożone klatki w momencie strzału) z bazy StatsBomb. Zbiór treningowy to niemal 10 000 idealnie oczyszczonych strzałów z wyłączeniem rzutów karnych.
* **Inżynieria cech:** Wektory zredukowane do kluczowych zmiennych przestrzennych (m.in. geometryczny dystans do bramki, kąt strzału, odległość bramkarza od linii, liczba obrońców w świetle strzału, flaga sytuacji "sam na sam").
* **Wykorzystane modele:** 
  * Regresja Logistyczna
  * Random Forest (Lasy Losowe)
  * XGBoost (Extreme Gradient Boosting) - *Model główny*
* Wszystkie modele osiągnęły doskonałą kalibrację, co potwierdziła ewaluacja metryką **Brier Score** (błąd na poziomie ~0.081).

---

## 🛠️ Stos Technologiczny (Tech Stack)

Aplikacja została zbudowana w języku **Python**, wykorzystując najlepsze rynkowe standardy analityczne:
* **Warstwa prezentacyjna i UI:** `Streamlit`, `Plotly` (interaktywne wykresy i rzuty przestrzenne), `Inkscape` (grafika wektorowa SVG podkładów boisk).
* **Przetwarzanie i Inżynieria Danych:** `pandas`, `NumPy`, `statsbombpy` (obsługa API dostawcy).
* **Machine Learning:** `scikit-learn`, `xgboost`, `joblib` (serializacja modeli).
* **Sztuczna Inteligencja:** `google-generativeai` (integracja z Google Gemini API).
* **Eksport i testy:** `fpdf` (generowanie raportów PDF), `pytest` (automatyczne testy jednostkowe i integracyjne, 71% pokrycia kodu).

---

## 📥 Uruchomienie lokalne

Aby uruchomić aplikację na własnym komputerze, wykonaj poniższe kroki w terminalu:

1. **Sklonuj repozytorium:**
   ```bash
   git clone [https://github.com/mirassso/Praca_mgr_2026.git](https://github.com/mirassso/Praca_mgr_2026.git)
   cd Praca_mgr_2026
   ```

2. **Utwórz i aktywuj środowisko wirtualne:**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # Linux/Mac:
   source venv/bin/activate
   ```

3. **Zainstaluj wymagane biblioteki:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Klucz API Gemini (Wymagane do generowania raportów AI):**
   Utwórz plik `.env` w głównym folderze projektu i dodaj w nim swój klucz Google Gemini API.

5. **Uruchom aplikację:**
   ```bash
   streamlit run app.py
   ```

---
*Autor: Ireneusz Kasprzak*
