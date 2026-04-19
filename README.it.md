# VIA Capitolo III — Pianificatore di percorso Ultima Thule

Un'applicazione web a file singolo per pianificare e verificare la conformità dei percorsi per la gara ciclistica di ultra distanza **VIA Capitolo III — Ultima Thule** (Amerongen, Paesi Bassi → Volda, Norvegia, ~4.000 km, 24 luglio–8 agosto 2026).

Sviluppato con [RideWithGPS](https://ridewithgps.com), [Leaflet.js](https://leafletjs.com) e [OSRM](https://project-osrm.org).

---

## Funzionalità

### 🗺 Mappa live
- Mappa Leaflet interattiva con tutti i 26 waypoint (cancelli, traghetti, rifugio, partenza/arrivo) visualizzati come marcatori etichettati
- Sovrapposizione del **percorso consigliato** in arancione tratteggiato per tutte le 9 tappe, attivabile/disattivabile dalla legenda della mappa
- La mappa si divide in vista superiore/inferiore quando si apre un rapporto di conformità

### 🚴 I miei percorsi — Ispettore di conformità
- Carica tutti i tuoi percorsi RideWithGPS (paginato, gestisce librerie di grandi dimensioni)
- Recupera la geometria completa del tracciato tramite l'API RWGPS ed esegue un controllo di conformità rispetto a:
  - **15 gallerie vietate** (Laerdalstunnelen, Gudvangatunnelen, Innfjordtunnelen e 12 altre)
  - **6 tratti stradali vietati** (E39 Vassenden–Skei, E6 Sel–Dombås e altri)
  - **17 traghetti vietati** (ponte dell'Øresund, Hirtshals, Göteborg, Malmö, Oslo, Kiel e altri)
  - **18 verifiche di prossimità ai cancelli obbligatorie** (raggio 400–500 m per cancello)
  - **30 punti di controllo del corridoio consigliato** raggruppati per tappa con note sull'efficienza
- Il rapporto di conformità mostra: numero di violazioni, cancelli mancati/raggiunti, raccomandazioni di percorso, griglia completa di copertura dei cancelli
- Violazioni segnalate sulla mappa con link «Ricalcola da qui ↗» a RideWithGPS con un solo clic
- **Caricamento GPX come alternativa** — se l'API blocca i dati di percorso privati, esportare da RWGPS e caricare localmente (nessun dato viene inviato da nessuna parte)
- Ispezione manuale del percorso tramite ID se il caricamento dell'elenco percorsi fallisce

### ✚ Crea — Pianificazione su rete stradale
- Seleziona qualsiasi combinazione delle 9 tappe della gara
- **Anteprima sulla rete stradale** — calcola ogni segmento terrestre tramite l'API ciclistica pubblica OSRM, mostrando le strade reali codificate per colore in base alla tappa
- I traversamenti in traghetto sono mostrati come linee tratteggiate (OSRM salta correttamente l'acqua)
- Sovrapposizione di avanzamento con stato per segmento durante il calcolo del percorso
- Invio diretto del percorso completato al tuo account RideWithGPS (fino a 2.000 punti traccia)
- Download come **GPX con percorso stradale** (traccia `<trk>` completa + waypoint `<wpt>`) o GPX con soli waypoint

### ✚ Visualizzazione PDI: acqua potabile, campeggi e servizi igienici
- Ingrandisci la mappa e attiva il menu PDI.
- Fonti d'acqua, campeggi e servizi igienici compariranno e si aggiorneranno in base al livello di zoom. I popup dei PDI includono link a Google Maps per un'ispezione più approfondita.

---

## Per iniziare

Apri l'applicazione direttamente nel browser — nessuna installazione, nessun server, nessuna dipendenza.

---

## Accesso

Accedi con la tua email e password di **RideWithGPS**. Le credenziali vengono inviate direttamente a `ridewithgps.com/users/current.json` — questa app non le vede né le memorizza mai. Solo il `auth_token` restituito viene salvato nel `localStorage` del browser per la sessione.

---

## Regole di gara codificate

### Gallerie vietate (15)
| Galleria | Posizione | Alternativa |
|---|---|---|
| Laerdalstunnelen | Vicino a Borgund | Strada di montagna Rv50 Filefjell |
| Gudvangatunnelen | Vicino a Flåm | Vecchia strada Stalheimskleiva |
| Innfjordtunnelen | Vicino ad Åndalsnes | Rv63 da nord |
| Galleria di Hellesylt | Sunnmøre | Consentita solo in direzione sud |
| Flenjatunnelen | Corridoio di Lærdal | Strade in superficie |
| Galleria di Eiksund | Volda/Ørsta | Traghetti Lote–Anda, Festøya, Lauvstad–Volda |
| Rotsethorntunnelen | Volda | Catena di traghetti |
| Hjartåbergtunnelen | Volda | Catena di traghetti |
| Oppljostunnelen | Strynefjellsveg | Gamle Strynefjellsveg |
| Kvivstunnelen | Gaularfjellet | Vecchia strada di montagna |
| Fodnestunnelen | Urnes/Solvorn | Strada in superficie via Gaupne |
| Amlatunnelen | Urnes/Solvorn | Strade in superficie |
| Morkaaastunnelen | Volda | Catena di traghetti |
| Selvågtunnelen | Ørsta/Volda | Lote–Anda → Festøya → Lauvstad–Volda |
| Galleria vicino a Dovre | Dombås | Rv15 o strade di valle |

### Tratti stradali vietati (6)
- E39 Vassenden–Skei → utilizzare Fv13 (Gaularfjellet)
- Tratto E39 Sandane → utilizzare Fv60/Fv615
- E6 Sel–Dombås → utilizzare Rv15 via Otta o Rv27
- E39 Ørstavegen (Volda) → arrivare tramite traghetto Lauvstad–Volda
- Tratto E39 Voldavegen → arrivare tramite catena di traghetti
- E39 da Festøya → utilizzare Festøya e poi traghetto Lauvstad–Volda

### Attraversamenti vietati (17)
Tutti i valichi DK→SE eccetto il **traghetto Helsingør–Helsingborg** sono vietati (ponte dell'Øresund, Malmö, Trelleborg, Ystad, Göteborg, Hirtshals). Vietati anche: Rostock–Gedser, Travemünde, Kiel, Oslo, Strömstad–Sandefjord, aliscafo di Bergen e diversi traghetti dei fiordi norvegesi.

### Cancelli obbligatori (16 + partenza/arrivo)
S · I · II · III · IV · V · VI · VII · VIII · IX · X · XI · XII · XIII · XIV · XV · XVI · F

---

## Struttura del percorso

| Tappa | Sezione | Distanza |
|---|---|---|
| L1 | Partenza (Amerongen) → Cancello I (Brocken, 1.141 m) | ~480 km |
| L2 | Brocken → Cancello II (Fredriksten) via Danimarca e Svezia | ~620 km |
| L3 | Cancello II → Cancello III (Suleskard, 1.050 m) + Rifugio | ~380 km |
| L4 | Cancello IV (Lysebotn) + traghetto Lysebotn–Forsand | ~60 km |
| L5 | Cancello V (Vøringsfossen) · IX (Borgund) · X (Urnes) · XI (Lom) | ~420 km |
| L6 | Cancello VI (Sognefjellet, 1.434 m) · VII (Gaularfjellet) · VIII (Strynefjellsveg) | ~280 km |
| L7 | Cancello XIV (Dalsnibba, 1.476 m) · XIII (Trollstigen) · XII (Svøufallet) | ~310 km |
| L8 | Cancello XV (Strada dell'Oceano Atlantico) | ~80 km |
| L9 | Cancello XVI (Vestkapp) → Arrivo (Volda) via catena di traghetti | ~120 km |

---

## Traghetti consentiti

L'elenco completo dei traghetti consentiti e vietati — inclusi i collegamenti tra le isole danesi, gli attraversamenti dell'Elba, l'Hardangerfjord, il Sognefjord e la catena di traghetti verso Volda — è disponibile nel pannello **⛴ Traghetti** della scheda Crea. Le righe verdi sono consentite; quelle rosse sono vietate.

---

## Date importanti

| Data | Evento |
|---|---|
| 23 luglio 2026 | Check-in 09:00–17:00, pasto comunitario 19:00 |
| 24 luglio 2026 | Partenza gara 07:00, De Proloog, Amerongen NL |
| 8 agosto 2026 | Festa di arrivo 20:00, Volda NO |

---

## Note tecniche

### API utilizzate
- **RideWithGPS** — autenticazione, libreria percorsi, creazione percorsi (`ridewithgps.com`)
- **API ciclistica pubblica OSRM** — instradamento su strade tra waypoint (`router.project-osrm.org`)
- **Tile CartoDB Voyager** — sfondo mappa (via Leaflet)

### Logica di instradamento
- Segmenti terrestri: instradati tramite profilo ciclista OSRM, polilinee disegnate nei colori della tappa
- Attraversamenti in traghetto: linee tratteggiate (OSRM salta l'acqua; i segmenti che partono da un waypoint di tipo `ferry` sono sempre tratteggiati)
- Fallback: se OSRM fallisce su un segmento terrestre, viene disegnata una linea retta tratteggiata tenue e contabilizzata nel conteggio dei segmenti di riserva
- Creazione percorso RWGPS: i punti traccia vengono campionati a ≤2.000 punti se l'anteprima supera quel limite

### Rilevamento della conformità
I punti traccia vengono campionati ogni 3 punti per le prestazioni. I raggi di rilevamento sono 300 m per le gallerie, 400–500 m per strade/traghetti e 400–500 m per i cancelli. Gli avvisi di corridoio utilizzano raggi più grandi (2–20 km a seconda del punto di controllo).

### Privacy
- Nessun dato viene inviato a server diversi da `ridewithgps.com` e `router.project-osrm.org`
- Il caricamento GPX per la verifica di conformità avviene interamente nel browser
- Solo il `auth_token` RWGPS viene conservato (nel `localStorage`)

---

## Struttura dei file

```
via_chapter3_planner.html   # intera app — HTML, CSS, JS in un unico file
README.md                   # questo file
```

---

## Crediti

Gara organizzata da [VIA](https://via-race.com/). Dati del percorso tratti dal KML ufficiale della gara e dal compendio (ottobre 2025). Instradamento fornito da [OSRM](https://project-osrm.org) e dai contributori di [OpenStreetMap](https://www.openstreetmap.org).
