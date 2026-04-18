# VIA Chapitre III — Planificateur d'itinéraire Ultima Thule

Application web monopage pour planifier et vérifier la conformité des itinéraires de la course cycliste ultra-distance **VIA Chapitre III — Ultima Thule** (Amerongen, Pays-Bas → Volda, Norvège, ~4 000 km, 24 juillet–8 août 2026).

Développé avec [RideWithGPS](https://ridewithgps.com), [Leaflet.js](https://leafletjs.com) et [OSRM](https://project-osrm.org).

---

## Fonctionnalités

### 🗺 Carte interactive
- Carte Leaflet interactive avec les 26 points de passage (portes, ferries, refuge, départ/arrivée) affichés comme des marqueurs étiquetés
- Superposition de l'**itinéraire recommandé** en orange pointillé pour les 9 étapes, activable/désactivable depuis la légende
- La carte se divise en vue haute/basse lors de l'ouverture d'un rapport de conformité

### 🚴 Mes itinéraires — Inspecteur de conformité
- Charge tous vos itinéraires RideWithGPS (paginé, gère les grandes bibliothèques)
- Récupère la géométrie complète du tracé via l'API RWGPS et effectue un contrôle de conformité contre :
  - **15 tunnels interdits** (Laerdalstunnelen, Gudvangatunnelen, Innfjordtunnelen et 12 autres)
  - **6 sections de route interdites** (E39 Vassenden–Skei, E6 Sel–Dombås et autres)
  - **17 ferries interdits** (pont de l'Øresund, Hirtshals, Göteborg, Malmö, Oslo, Kiel et autres)
  - **18 contrôles de proximité de portes obligatoires** (rayon de 400–500 m par porte)
  - **30 points de contrôle de corridor recommandés** regroupés par étape avec notes d'efficacité
- Le rapport de conformité indique : nombre de violations, portes manquées/atteintes, conseils de routage, grille complète de couverture des portes
- Violations épinglées sur la carte avec liens « Recalculer depuis ici ↗ » vers RideWithGPS en un clic
- **Chargement GPX de secours** — si l'API bloque les données d'itinéraire privées, exportez depuis RWGPS et chargez localement (aucune donnée n'est envoyée nulle part)
- Inspection manuelle d'un itinéraire par identifiant si le chargement de la liste échoue

### ✚ Créer — Planification sur réseau routier
- Sélectionnez toute combinaison des 9 étapes de course
- **Aperçu sur le réseau routier** — trace chaque segment terrestre via l'API cycliste OSRM publique, avec les routes réelles colorées par étape
- Les traversées en ferry s'affichent en pointillés (OSRM ignore correctement l'eau)
- Superposition de progression avec statut par segment lors du calcul
- Envoi direct de l'itinéraire terminé vers votre compte RideWithGPS (jusqu'à 2 000 points de tracé)
- Téléchargement en **GPX routé sur route** (tracé `<trk>` complet + waypoints `<wpt>`) ou en GPX waypoints uniquement

### ✚ Affichage des POI : eau potable, campings et toilettes
- Zoomez sur la carte et activez le menu POI.
- Les sources d'eau, campings et toilettes s'affichent et s'ajustent selon le niveau de zoom. Les fenêtres contextuelles incluent des liens Google Maps pour une inspection approfondie.

---

## Démarrage

Ouvrez l'application directement dans votre navigateur — aucune installation, aucun serveur, aucune dépendance.

---

## Connexion

Connectez-vous avec votre adresse e-mail et mot de passe **RideWithGPS**. Les identifiants sont envoyés directement à `ridewithgps.com/users/current.json` — cette application ne les voit ni ne les stocke jamais. Seul le `auth_token` renvoyé est sauvegardé dans le `localStorage` de votre navigateur pour la session.

La clé API intégrée (`eeee8a09`) est la clé d'application publique VIA pour RideWithGPS.

---

## Règles de course encodées

### Tunnels interdits (15)
| Tunnel | Emplacement | Alternative |
|---|---|---|
| Laerdalstunnelen | Près de Borgund | Route de montagne Rv50 Filefjell |
| Gudvangatunnelen | Près de Flåm | Ancienne route Stalheimskleiva |
| Innfjordtunnelen | Près d'Åndalsnes | Rv63 par le nord |
| Tunnel de Hellesylt | Sunnmøre | Autorisé uniquement en direction sud |
| Flenjatunnelen | Corridor de Lærdal | Routes en surface |
| Tunnel d'Eiksund | Volda/Ørsta | Ferries Lote–Anda, Festøya, Lauvstad–Volda |
| Rotsethorntunnelen | Volda | Chaîne de ferries |
| Hjartåbergtunnelen | Volda | Chaîne de ferries |
| Oppljostunnelen | Strynefjellsveg | Gamle Strynefjellsveg |
| Kvivstunnelen | Gaularfjellet | Ancienne route de montagne |
| Fodnestunnelen | Urnes/Solvorn | Route en surface via Gaupne |
| Amlatunnelen | Urnes/Solvorn | Routes en surface |
| Morkaaastunnelen | Volda | Chaîne de ferries |
| Selvågtunnelen | Ørsta/Volda | Lote–Anda → Festøya → Lauvstad–Volda |
| Tunnel près de Dovre | Dombås | Rv15 ou routes de vallée |

### Sections de route interdites (6)
- E39 Vassenden–Skei → utiliser la Fv13 (Gaularfjellet)
- Section E39 Sandane → utiliser Fv60/Fv615
- E6 Sel–Dombås → utiliser la Rv15 via Otta ou la Rv27
- E39 Ørstavegen (Volda) → arriver via le ferry Lauvstad–Volda
- Section E39 Voldavegen → arriver via la chaîne de ferries
- E39 depuis Festøya → utiliser Festøya puis le ferry Lauvstad–Volda

### Traversées interdites (17)
Toutes les traversées DK→SE sauf le **ferry Helsingør–Helsingborg** sont interdites (pont de l'Øresund, Malmö, Trelleborg, Ystad, Göteborg, Hirtshals). Également interdits : Rostock–Gedser, Travemünde, Kiel, Oslo, Strömstad–Sandefjord, bateau rapide Bergen et plusieurs ferries de fjords norvégiens.

### Portes obligatoires (16 + départ/arrivée)
S · I · II · III · IV · V · VI · VII · VIII · IX · X · XI · XII · XIII · XIV · XV · XVI · F

---

## Structure de l'itinéraire

| Étape | Section | Distance |
|---|---|---|
| L1 | Départ (Amerongen) → Porte I (Brocken, 1 141 m) | ~480 km |
| L2 | Brocken → Porte II (Fredriksten) via Danemark & Suède | ~620 km |
| L3 | Porte II → Porte III (Suleskard, 1 050 m) + Refuge | ~380 km |
| L4 | Porte IV (Lysebotn) + ferry Lysebotn–Forsand | ~60 km |
| L5 | Porte V (Vøringsfossen) · IX (Borgund) · X (Urnes) · XI (Lom) | ~420 km |
| L6 | Porte VI (Sognefjellet, 1 434 m) · VII (Gaularfjellet) · VIII (Strynefjellsveg) | ~280 km |
| L7 | Porte XIV (Dalsnibba, 1 476 m) · XIII (Trollstigen) · XII (Svøufallet) | ~310 km |
| L8 | Porte XV (Route de l'Océan Atlantique) | ~80 km |
| L9 | Porte XVI (Vestkapp) → Arrivée (Volda) via chaîne de ferries | ~120 km |

---

## Ferries autorisés

| Ferry | Notes |
|---|---|
| Puttgarden–Rødby | DE→DK, ~45 min, embarquement piéton |
| Helsingør–Helsingborg | **Seule** traversée DK→SE autorisée, 20 min, toutes les 20 min |
| Lysebotn–Forsand | Réserver à l'avance — complet en juil./août. billetter.kolumbus.no |
| Solvorn–Ornes | Pour l'église en bois debout d'Urnes (Porte X), ~15 min piéton |
| Molde–Vestnes | Traverse le Romsdalsfjord |
| Linge–Eidsdal | Après Trollstigen |
| Lote–Anda | Traverse le Nordfjord, évite tous les tunnels E39 interdits près de Volda |
| Festøya | ~20 min, fréquent |
| Lauvstad–Volda | Dernier ferry jusqu'à l'arrivée |

---

## Dates clés

| Date | Événement |
|---|---|
| 23 juillet 2026 | Enregistrement 09h00–17h00, repas communautaire 19h00 |
| 24 juillet 2026 | Départ de course 07h00, De Proloog, Amerongen NL |
| 8 août 2026 | Célébration de l'arrivée 20h00, Volda NO |

---

## Notes techniques

### APIs utilisées
- **RideWithGPS** — authentification, bibliothèque d'itinéraires, création d'itinéraires (`ridewithgps.com`)
- **API cycliste publique OSRM** — routage suivant les routes entre les points (`router.project-osrm.org`)
- **Tuiles CartoDB Voyager** — fond de carte (via Leaflet)

### Logique de routage
- Segments terrestres : routés via le profil cycliste OSRM, polylignes dessinées en couleurs d'étape
- Traversées en ferry : lignes pointillées (OSRM ignore l'eau ; les segments partant d'un point de type `ferry` sont toujours en pointillés)
- Repli : si OSRM échoue sur un segment terrestre, une ligne droite pointillée pâle est dessinée et comptée dans le bilan des segments de repli
- Création d'itinéraire RWGPS : les points de tracé sont échantillonnés à ≤2 000 points si l'aperçu dépasse cette limite

### Détection de conformité
Les points de tracé sont échantillonnés tous les 3 points pour les performances. Les rayons de détection sont de 300 m pour les tunnels, 400–500 m pour les routes/ferries et 400–500 m pour les portes. Les conseils de corridor utilisent des rayons plus grands (2–20 km selon le point de contrôle).

### Confidentialité
- Aucune donnée n'est envoyée à un serveur autre que `ridewithgps.com` et `router.project-osrm.org`
- La vérification de conformité par chargement GPX s'effectue entièrement dans le navigateur
- Seul le `auth_token` RWGPS est conservé (dans `localStorage`)

---

## Structure des fichiers

```
via_chapter3_planner.html   # application complète — HTML, CSS, JS dans un seul fichier
README.md                   # ce fichier
```

---

## Crédits

Course organisée par [VIA](https://via-race.com/). Données d'itinéraire issues du KML officiel de la course et du compendium (octobre 2025). Routage propulsé par [OSRM](https://project-osrm.org) et les contributeurs [OpenStreetMap](https://www.openstreetmap.org).
