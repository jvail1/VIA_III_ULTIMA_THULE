# VIA Kapitel III — Ultima Thule Routenplaner

Eine Single-File-Webanwendung zur Routenplanung und Regelkonformitätsprüfung für das Ultra-Radrennen **VIA Kapitel III — Ultima Thule** (Amerongen, Niederlande → Volda, Norwegen, ~4.000 km, 24. Juli–8. August 2026).

Basiert auf [RideWithGPS](https://ridewithgps.com), [Leaflet.js](https://leafletjs.com) und [OSRM](https://project-osrm.org).

---

## Funktionen

### 🗺 Live-Karte
- Interaktive Leaflet-Karte mit allen 26 Wegpunkten (Tore, Fähren, Refuge, Start/Ziel) als beschriftete Marker
- Gestrichelte orangefarbene **empfohlene Routenüberlagerung** für alle 9 Etappen, über die Kartenlegende ein-/ausblendbar
- Karte teilt sich in eine Oben/Unten-Ansicht, wenn ein Konformitätsbericht geöffnet ist

### 🚴 Meine Routen — Konformitätsprüfer
- Lädt alle Ihre RideWithGPS-Routen (paginiert, verarbeitet große Bibliotheken)
- Ruft vollständige Streckengeometrie über die RWGPS-API ab und führt eine Konformitätsprüfung durch gegen:
  - **15 gesperrte Tunnel** (Laerdalstunnelen, Gudvangatunnelen, Innfjordtunnelen und 12 weitere)
  - **6 gesperrte Streckenabschnitte** (E39 Vassenden–Skei, E6 Sel–Dombås und weitere)
  - **17 gesperrte Fähren** (Øresundbrücke, Hirtshals, Göteborg, Malmö, Oslo, Kiel und weitere)
  - **18 Pflicht-Näherungsprüfungen** (400–500 m Radius pro Tor)
  - **30 empfohlene Korridorkontrollpunkte** nach Etappe gruppiert mit Effizienzhinweisen
- Konformitätsbericht zeigt: Anzahl der Verstöße, verpasste/erreichte Tore, Routing-Hinweise, vollständiges Tor-Abdeckungsraster
- Verstöße auf der Karte markiert mit Ein-Klick-Links „Von hier umrouten ↗" zu RideWithGPS
- **GPX-Upload als Fallback** — wenn die API private Routendaten blockiert, exportieren Sie von RWGPS und laden Sie lokal hoch (es werden keine Daten gesendet)
- Manuelle Routenprüfung per ID, falls die Routenliste nicht geladen werden kann

### ✚ Erstellen — Straßenbasierte Routenplanung
- Wählen Sie beliebige Kombinationen der 9 Renn-Etappen
- **Vorschau im Straßennetz** — routet jeden Landabschnitt über die öffentliche OSRM-Fahrrad-API mit echten Straßen farblich nach Etappe kodiert
- Fährüberquerungen als gestrichelte Linien dargestellt (OSRM überspringt Wasser korrekt)
- Fortschrittsanzeige mit Status pro Segment während der Routenberechnung
- Direktes Übertragen der fertigen Route in Ihr RideWithGPS-Konto (bis zu 2.000 Spurpunkte)
- Download als **straßengeroutete GPX-Datei** (vollständiger `<trk>`-Track + `<wpt>`-Wegpunkte) oder als Nur-Wegpunkte-GPX

### ✚ POI: Trinkwasser, Campingplätze und Toiletten anzeigen
- Zoomen Sie auf der Karte heran und aktivieren Sie das POI-Menü.
- Wasserquellen, Campingplätze und Toiletten werden angezeigt und passen sich je nach Zoomstufe an. POI-Popups enthalten Google-Maps-Links zur weiteren Prüfung.

---

## Erste Schritte

Öffnen Sie die App direkt in Ihrem Browser — keine Installation, kein Server, keine Abhängigkeiten erforderlich.

---

## Anmeldung

Melden Sie sich mit Ihrer **RideWithGPS**-E-Mail-Adresse und Ihrem Passwort an. Zugangsdaten werden direkt an `ridewithgps.com/users/current.json` gesendet — diese App sieht oder speichert sie nie. Nur das zurückgegebene `auth_token` wird im `localStorage` Ihres Browsers für die Sitzung gespeichert.

Der eingebettete API-Schlüssel (`eeee8a09`) ist der öffentliche VIA-Anwendungsschlüssel für RideWithGPS.

---

## Kodierte Rennregeln

### Gesperrte Tunnel (15)
| Tunnel | Ort | Alternative |
|---|---|---|
| Laerdalstunnelen | Bei Borgund | Bergstraße Rv50 Filefjell |
| Gudvangatunnelen | Bei Flåm | Alte Straße Stalheimskleiva |
| Innfjordtunnelen | Bei Åndalsnes | Rv63 von Norden |
| Hellesylt-Tunnel | Sunnmøre | Nur in Fahrtrichtung Süd erlaubt |
| Flenjatunnelen | Korridor Lærdal | Oberirdische Straßen |
| Eiksund-Tunnel | Volda/Ørsta | Fähren Lote–Anda, Festøya, Lauvstad–Volda |
| Rotsethorntunnelen | Volda | Fährenkette |
| Hjartåbergtunnelen | Volda | Fährenkette |
| Oppljostunnelen | Strynefjellsveg | Gamle Strynefjellsveg |
| Kvivstunnelen | Gaularfjellet | Alte Bergstraße |
| Fodnestunnelen | Urnes/Solvorn | Oberirdische Straße via Gaupne |
| Amlatunnelen | Urnes/Solvorn | Oberirdische Straßen |
| Morkaaastunnelen | Volda | Fährenkette |
| Selvågtunnelen | Ørsta/Volda | Lote–Anda → Festøya → Lauvstad–Volda |
| Tunnel bei Dovre | Dombås | Rv15 oder Talstraßen |

### Gesperrte Streckenabschnitte (6)
- E39 Vassenden–Skei → Fv13 (Gaularfjellet) nutzen
- E39-Abschnitt Sandane → Fv60/Fv615 nutzen
- E6 Sel–Dombås → Rv15 über Otta oder Rv27 nutzen
- E39 Ørstavegen (Volda) → Ankunft über Fähre Lauvstad–Volda
- E39-Abschnitt Voldavegen → Ankunft über Fährenkette
- E39 ab Festøya → Festøya, dann Fähre Lauvstad–Volda nutzen

### Gesperrte Überquerungen (17)
Alle DK→SE-Überquerungen außer der **Fähre Helsingør–Helsingborg** sind gesperrt (Øresundbrücke, Malmö, Trelleborg, Ystad, Göteborg, Hirtshals). Ebenfalls gesperrt: Rostock–Gedser, Travemünde, Kiel, Oslo, Strömstad–Sandefjord, Bergen Schnellboot und mehrere norwegische Fjordfähren.

### Pflichtore (16 + Start/Ziel)
S · I · II · III · IV · V · VI · VII · VIII · IX · X · XI · XII · XIII · XIV · XV · XVI · F

---

## Streckenstruktur

| Etappe | Abschnitt | Distanz |
|---|---|---|
| L1 | Start (Amerongen) → Tor I (Brocken, 1.141 m) | ~480 km |
| L2 | Brocken → Tor II (Fredriksten) via Dänemark & Schweden | ~620 km |
| L3 | Tor II → Tor III (Suleskard, 1.050 m) + Refuge | ~380 km |
| L4 | Tor IV (Lysebotn) + Fähre Lysebotn–Forsand | ~60 km |
| L5 | Tor V (Vøringsfossen) · IX (Borgund) · X (Urnes) · XI (Lom) | ~420 km |
| L6 | Tor VI (Sognefjellet, 1.434 m) · VII (Gaularfjellet) · VIII (Strynefjellsveg) | ~280 km |
| L7 | Tor XIV (Dalsnibba, 1.476 m) · XIII (Trollstigen) · XII (Svøufallet) | ~310 km |
| L8 | Tor XV (Atlantikstraße) | ~80 km |
| L9 | Tor XVI (Vestkapp) → Ziel (Volda) via Fährenkette | ~120 km |

---

## Erlaubte Fähren

Die vollständige Liste der erlaubten und gesperrten Fähren — einschließlich dänischer Inselüberfahrten, Elbüberquerungen, Hardangerfjord, Sognefjord und der Fährkette nach Volda — ist im **⛴ Fähren**-Panel des Erstellen-Tabs verfügbar. Grüne Zeilen sind erlaubt; rote Zeilen sind gesperrt.

---

## Wichtige Termine

| Datum | Ereignis |
|---|---|
| 23. Juli 2026 | Anmeldung 09:00–17:00 Uhr, Gemeinschaftsessen 19:00 Uhr |
| 24. Juli 2026 | Rennstart 07:00 Uhr, De Proloog, Amerongen NL |
| 8. August 2026 | Zielankunftsfeier 20:00 Uhr, Volda NO |

---

## Technische Hinweise

### Verwendete APIs
- **RideWithGPS** — Authentifizierung, Routenbibliothek, Routenerstellung (`ridewithgps.com`)
- **Öffentliche OSRM-Fahrrad-API** — straßenfolgendes Routing zwischen Wegpunkten (`router.project-osrm.org`)
- **CartoDB Voyager Tiles** — Kartenhintergrund (via Leaflet)

### Routing-Logik
- Landabschnitte: Routing via OSRM-Fahrradprofil, Polylinien in Etappenfarben gezeichnet
- Fährüberquerungen: gestrichelte Linien (OSRM überspringt Wasser; Segmente ab einem Wegpunkt vom Typ `ferry` sind immer gestrichelt)
- Fallback: Schlägt OSRM bei einem Landabschnitt fehl, wird eine schwache gestrichelte Gerade gezeichnet und im Fallback-Segmentzähler erfasst
- RWGPS-Routenerstellung: Spurpunkte werden auf ≤2.000 Punkte reduziert, wenn die Vorschau diesen Grenzwert überschreitet

### Konformitätserkennung
Spurpunkte werden jeden 3. Punkt abgetastet (Performance). Erkennungsradien: 300 m für Tunnel, 400–500 m für Straßen/Fähren und 400–500 m für Tore. Korridorhinweise verwenden größere Radien (2–20 km je nach Kontrollpunkt).

### Datenschutz
- Es werden keine Daten an andere Server als `ridewithgps.com` und `router.project-osrm.org` gesendet
- GPX-Upload zur Konformitätsprüfung läuft vollständig im Browser
- Nur das RWGPS `auth_token` wird gespeichert (im `localStorage`)

---

## Dateistruktur

```
via_chapter3_planner.html   # gesamte App — HTML, CSS, JS in einer Datei
README.md                   # diese Datei
```

---

## Credits

Rennen organisiert von [VIA](https://via-race.com/). Routendaten aus der offiziellen Renn-KML-Datei und dem Kompendium (Oktober 2025). Routing unterstützt durch [OSRM](https://project-osrm.org) und [OpenStreetMap](https://www.openstreetmap.org)-Mitwirkende.
