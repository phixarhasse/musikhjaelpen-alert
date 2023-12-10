# Work In Progress: Musikhjälpen Alert: Ett enkelt notissystem för Musikhjälpen bössor

Musikhjälpen Bössa-notiser: Om du någonsin har velat ha ett verktyg som automatiskt skickar notiser när någon donerat till din Musikhjälpen Bössa så har du hittat rätt.
**Disclaimer: Att använda web scrapers är inte tillåtet överallt på internet. Originalförfattaren av koden på denna sidan tar inget ansvar för eventuella påföljder och/eller straffåtgärder som kommer av att köra koden.**

## Hur koden fungerar

I skrivande stund saknas ett öppet API för att lyssna efter uppdateringar av Musikhjälpens bössor så därför är detta en så kallad web scraper.
Koden består av två filer, som körs separat.

### scraper.py

Med hjälp av open source drivrutiner för Chromeium simulerar koden en att en webbläsare öppnar bössans hemsida.
Sedan inväntas att bössans värde laddas, därefter läses detta HTML-element av och jämförs med angivet startvärde. Har värdet ökat spelas skickas en HTTP POST till servern och värdet som donerats visas i loggen.
Var 5:e sekund hämtas sidan och värdet läses av igen.

### gif-server.py

Ansvarar för att spela upp notisen. När en HTTP POST kommer in till endpoint:en `/donation` uppdateras en global variabel som fungerar som triggern för notisen.
När event-processen på endpoint `/event` upptäcker att globala variabeln uppdaterats skickar den gif-datan till de klienter som lyssnar på `http://localhost:5000` samt spelar upp ljudfilen.
Detta är aboslut inte det bästa sättet att göra det på, men som sagt, Work In Progress. Det funkar tills vidare.
**Observera att servern spelar upp ljudet lokalt, alltså på datorn som kör servern.** Ljudet strömmas inte till klienten (än).

## Hur man kör koden

Notera att den medföljande chromedriver-drivrutinen endast har stöd för Windows.
I framtiden kanske någon orkar fixa så koden kan köras på alla operativsystem direkt.

1. Ladda ner denna koden till valfri plats på din dator från [GitHub](https://github.com/phixarhasse/musikhjaelpen-alert)
2. Se till att ha Python installerat, se [python.org](https://www.python.org/) och att Python finns i din PATH-variabel.
3. Öppna PowerSehll, navigera till mappen med koden, alltså `/musikhjaelpen-alert`.
4. Starta ett virtual environment med `python -m venv venv`
5. Aktivera venv genom att köra `.\venv\Script\activate`
6. Installera beroenden med `pip install -r requirements.txt`
7. Skapa en fil dirket i mappen `/musikhjaelpen-alert` med namn `.env`. Innehållet ska se ut som i `.env-example`.
8. Lägg till dina miljövariabler i `.env`, de borde vara självförklarande. Koden kommer med en GIF och en ljudfil att börja med, men lägg gärna till egna och uppdatera `.env` därefter.
9. Starta GIF servern med `python gif-server.py`
10. Öppna en till PowerShell, se till att venv är aktiverat även där och starta scrapern med `python scraper.py`.
11. Nu bör du få notiser om bössan på URL:en du lade in i `.env` får donationer! Gå till [http://localhost:5000/](http://localhost:5000/) för att se GIFen spelas upp.
