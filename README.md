# WIP: Musikhjälpen Alert: Ett enkelt notissystem för Musikhjälpen bössor
Musikhjälpen Bössa-notiser: Om du någonsin har velat ha ett verktyg som automatiskt skickar notiser när någon donerat till din Musikhjälpen Bössa så har du hittat rätt.

## Hur koden fungerar
I skrivande stund saknas ett öppet API för att lyssna efter uppdateringar av Musikhjälpens bössor så därför är detta en så kallad web scraper.
Med hjälp av open source drivrutiner för Chromeium simulerar koden en att en webbläsare öppnar bössans hemsida.
Sedan inväntas att bössans värde laddas, därefter läses detta HTML-element av och jämförs med angivet startvärde. Har värdet ökat spelas ett notisljud upp och värdet som donerats visas i loggen.
Var 10:e sekund uppdateras sidan och värdet läses av igen.
