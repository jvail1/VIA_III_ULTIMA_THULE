# VIA Chapter III — Ultima Thule Routeplanner

Een webapplicatie in één bestand voor het plannen en controleren van routes voor de **VIA Chapter III — Ultima Thule** ultra-afstandswielrennen (Amerongen, Nederland → Volda, Noorwegen, ~4.000km, 24 juli–8 augustus 2026).

Gebouwd op [RideWithGPS](https://ridewithgps.com), [Leaflet.js](https://leafletjs.com), en [OSRM](https://project-osrm.org).

---

## Functies

### 🗺 Live Kaart
- Interactieve Leaflet-kaart met alle 26 waypoints (poorten, veerponten, refuge, start/finish) als gelabelde markeringen
- Knop **🗺 Officiële Kaart** toont de officiële VIA Google My Maps als referentie-overlay
- Kaart splitst in een boven/onder-weergave wanneer een compliancerapport open is

### ⛅ Poortweer
- **3-daagse weersvoorspelling** voor elke poort, automatisch opgehaald wanneer je een poort selecteert
- Toont dagelijkse maximale/minimale temperatuur, windsnelheid en -richting, neerslag en een weersomschrijving
- Aangedreven door [Open-Meteo](https://open-meteo.com) (gratis, geen API-sleutel nodig)
- Schakel de voorspelling per poort in/uit met de knop **⛅ Weer**
- 30 minuten in-memory cache — voorspellingen blijven actueel zonder overbelasting van de API

### 🚴 Mijn Routes — Compliance-inspecteur
- Laadt al je RideWithGPS-routes (gepagineerd, geschikt voor grote bibliotheken)
- Haalt volledige trackgeometrie op via de RWGPS API en voert een compliancecontrole uit tegen:
  - **15 verboden tunnels** (Laerdalstunnelen, Gudvangatunnelen, Innfjordtunnelen, en 12 andere)
  - **6 verboden weggedeelten** (E39 Vassenden–Skei, E6 Sel–Dombås, en andere)
  - **17 verboden veerboten** (Øresondbrug, Hirtshals, Göteborg, Malmö, Oslo, Kiel, en andere)
  - **18 verplichte poortcontroles** (400–500m straal per poort)
  - **30 aanbevolen corridorcontrolepunten** gegroepeerd per etappe met efficiëntienotities
- Compliancerapport toont: aantal overtredingen, gemiste/bezochte poorten, routeringsadviezen, volledig poortoverzicht
- Overtredingen op kaart vastgezet met één klik "Herroute vanaf hier ↗" links naar RideWithGPS
- **GPX-upload als terugvaloptie** — als de API privéroutedata blokkeert, exporteer dan vanuit RWGPS en upload lokaal (er wordt niets verzonden)
- Handmatige route-inspectie op ID als de routelijst niet laadt

### ✚ Aanmaken — Ad-hoc Weggerouteerde Planning
Gebruik het tabblad Aanmaken als **snelle conceptroutetool** — selecteer etappes, kies veerponten, zet spelden, bekijk een voorvertoning op echte wegen en exporteer. Het resultaat is een goed concept dat je kunt verfijnen in RideWithGPS, Komoot, Strava of een ander routeringsprogramma.

- Selecteer een combinatie van de 9 race-etappes en schakel individuele veerponten in/uit
- **Voorvertoning op Wegnetwerk** — routeert elk landsegment via de OSRM openbare fiets-API, met werkelijke fietswegen gekleurd per etappe
- Veerpont-oversteken weergegeven als gestreepte lijnen (OSRM slaat water over)
- Voortgangsoverlay met status per segment tijdens het routeren
- **Direct naar RideWithGPS sturen** — opent meteen in de route-editor voor verdere verfijning
- **GPX downloaden** — importeer in Komoot, Strava, Garmin Connect, Wahoo of elk GPX-compatibel programma
- Waypoints-alleen GPX ook beschikbaar voor het laden van poortmarkeringen in een fietscomputer

### 📌 Spelden — Ad-hoc Waypoints
Zet eigen spelden op de kaart om persoonlijke waypoints toe te voegen — een hotel, een omleidingspunt, een bevoorradingshalte of een alternatief wegkruispunt.

- Tik op **📌 Speld toevoegen** op de kaart om een waypoint te plaatsen
- Geef elke speld een naam — ze verschijnt in het tabblad Spelden met de afstand tot je geladen route
- Vink **«Als routeringswaypoint gebruiken»** aan op een speld in het tabblad Spelden om deze op te nemen in weggerouteerde voorvertoningen en GPX-exports; niet aangevinkte spelden worden opgeslagen maar niet doorgerouteerd
- Spelden worden opgenomen in de volgorde zoals ze in het tabblad Spelden verschijnen — sleep om te herordenen
- Opgeslagen in je browser — spelden blijven bewaard tussen sessies
- Gebruik spelden om omwegen of alternatieven te schetsen voordat je overgaat naar een volledig routeringsprogramma

### ⛺ POI's — Drinkwater, Campings en Toiletten
- Zoom in op de kaart en schakel het POI-menu in
- Waterbronnen, campings en toiletten worden weergegeven en aangepast op basis van zoomniveau
- POI-popups bevatten Google Maps-links voor verdere inspectie

---

## Aan de Slag

Open de app direct in je browser — geen installatie, geen server, geen afhankelijkheden.

---

## Inloggen

Meld je aan met je **RideWithGPS** e-mail en wachtwoord. Inloggegevens worden rechtstreeks naar `ridewithgps.com/users/current.json` gestuurd — deze app ziet of slaat ze nooit op. Alleen het teruggegeven `auth_token` wordt opgeslagen in de `localStorage` van je browser voor de sessie.

---

## Ingevoerde Raceregels

### Verboden tunnels (15)
| Tunnel | Locatie | Alternatief |
|---|---|---|
| Laerdalstunnelen | Bij Borgund | Rv50 Filefjell bergweg |
| Gudvangatunnelen | Bij Flåm | Stalheimskleiva oude weg |
| Innfjordtunnelen | Bij Åndalsnes | Rv63 vanuit het noorden |
| Hellesylt tunnel | Sunnmøre | Alleen richting het zuiden toegestaan |
| Flenjatunnelen | Lærdal corridor | Wegen bovengronds |
| Eiksund tunnel | Volda/Ørsta | Lote–Anda, Festøya, Lauvstad–Volda veerponten |
| Rotsethorntunnelen | Volda | Veerpont-keten |
| Hjartåbergtunnelen | Volda | Veerpont-keten |
| Oppljostunnelen | Strynefjellsveg | Gamle Strynefjellsveg |
| Kvivstunnelen | Gaularfjellet | Oude bergweg |
| Fodnestunnelen | Urnes/Solvorn | Bovengrondse weg via Gaupne |
| Amlatunnelen | Urnes/Solvorn | Bovengrondse wegen |
| Morkaaastunnelen | Volda | Veerpont-keten |
| Selvågtunnelen | Ørsta/Volda | Lote–Anda → Festøya → Lauvstad–Volda |
| Tunnel bij Dovre | Dombås | Rv15 of dalwegen |

### Verboden weggedeelten (6)
- E39 Vassenden–Skei → gebruik Fv13 (Gaularfjellet)
- E39 Sandane gedeelte → gebruik Fv60/Fv615
- E6 Sel–Dombås → gebruik Rv15 via Otta of Rv27
- E39 Ørstavegen (Volda) → aankomst via Lauvstad–Volda veerpont
- E39 Voldavegen gedeelte → aankomst via veerpont-keten
- E39 vanaf Festøya → gebruik Festøya dan Lauvstad–Volda veerpont

### Verboden oversteekpunten (17)
Alle DK→SE oversteekpunten behalve **Helsingør–Helsingborg veerpont** zijn verboden (Øresondbrug, Malmö, Trelleborg, Ystad, Göteborg, Hirtshals). Ook verboden: Rostock–Gedser, Travemünde, Kiel, Oslo, Strömstad–Sandefjord, Bergen snelle boot, en diverse Noorse fjordveerponten.

### Verplichte poorten (16 + start/finish)
S · I · II · III · IV · V · VI · VII · VIII · IX · X · XI · XII · XIII · XIV · XV · XVI · F

---

## Routestructuur

| Etappe | Gedeelte | Afstand |
|---|---|---|
| L1 | Start (Amerongen) → Poort I (Brocken, 1.141m) | ~480km |
| L2 | Brocken → Poort II (Fredriksten) via Denemarken & Zweden | ~620km |
| L3 | Poort II → Poort III (Suleskard, 1.050m) + Refuge | ~380km |
| L4 | Poort IV (Lysebotn) + Lysebotn–Forsand veerpont | ~60km |
| L5 | Poort V (Vøringsfossen) · IX (Borgund) · X (Urnes) · XI (Lom) | ~420km |
| L6 | Poort VI (Sognefjellet, 1.434m) · VII (Gaularfjellet) · VIII (Strynefjellsveg) | ~280km |
| L7 | Poort XIV (Dalsnibba, 1.476m) · XIII (Trollstigen) · XII (Svøufallet) | ~310km |
| L8 | Poort XV (Atlantic Ocean Road) | ~80km |
| L9 | Poort XVI (Vestkapp) → Finish (Volda) via veerpont-keten | ~120km |

---

## Toegestane Veerponten

De volledige lijst van toegestane en verboden veerponten — inclusief Deense eilandoversteken, Elbe-oversteken, Hardangerfjord, Sognefjord en de veerpont-keten naar Volda — is beschikbaar in het **⛴ Veerboten**-paneel op het tabblad Aanmaken. Groene rijen zijn toegestaan; rode rijen zijn verboden.

---

## Belangrijke Data

| Datum | Evenement |
|---|---|
| 23 juli 2026 | Registratie 09:00–17:00, gemeenschappelijke maaltijd 19:00 |
| 24 juli 2026 | Racestart 07:00, De Proloog, Amerongen NL |
| 8 augustus 2026 | Finishviering 20:00, Volda NO |

---

## Technische Notities

### Gebruikte API's
- **RideWithGPS** — authenticatie, routebibliotheek, routeaanmaak (`ridewithgps.com`)
- **OSRM openbare fiets-API** — wegvolgende routering tussen waypoints (`router.project-osrm.org`)
- **CartoDB Voyager tegels** — kaartachtergrond (via Leaflet)

### Routeringslogica
- Landsegmenten: gerouteerd via OSRM fietsprofiel, polylijnen getekend in etappekleuren
- Veerpont-oversteken: gestreepte lijnen (OSRM slaat water over; segmenten vertrekkend vanaf een `ferry`-waypoint zijn altijd gestreept)
- Terugval: als OSRM een landsegment mislukt, wordt een vage gestreepte rechte lijn getekend en meegeteld in de terugvalstatistiek
- RWGPS route-aanmaak: trackpunten worden bemonsterd tot ≤2.000 punten als de voorvertoning dat overschrijdt

### Compliancedetectie
Trackpunten worden elke 3e punt bemonsterd voor prestaties. Detectiestralen zijn 300m voor tunnels, 400–500m voor wegen/veerponten, en 400–500m voor poorten. Corridoradviezen gebruiken grotere stralen (2–20km afhankelijk van het controlepunt).

### Privacy
- Er worden geen gegevens naar een andere server gestuurd dan `ridewithgps.com` en `router.project-osrm.org`
- GPX-upload voor compliancecontrole werkt volledig in de browser
- Alleen het RWGPS `auth_token` wordt opgeslagen (in `localStorage`)

---

## Bestandsstructuur

```
via_chapter3_planner.html   # volledige app — HTML, CSS, JS in één bestand
README.md                   # dit bestand
```

---

## Credits

Race georganiseerd door [VIA](https://via-race.com/). Routedata afkomstig van de officiële race-KML en het compendium (oktober 2025). Routering aangedreven door [OSRM](https://project-osrm.org) en [OpenStreetMap](https://www.openstreetmap.org) bijdragers.
