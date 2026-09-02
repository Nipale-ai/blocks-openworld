# Bildkritik Runde 1 (menschlich gesichtet, 02.09.2026 23:35)

Renders angesehen: 01_front, 07_thumbnail, 08_silhouette.

**Was bleibt:** Materialsprache stimmt — schwarzer Klarlack fängt Licht scharf,
Fugenlicht orange ist stark und lesbar, Schulterbreite und Brustkern sitzen.
Nichts davon anfassen.

**Was der Silhouettentest (08) aufdeckt — das ist die Abnahme, und sie ist rot:**

1. **Der Kopf verschwindet in der Schulterlinie.** In der schwarzen Flaeche ist
   kein Kopf erkennbar. Ein Mecha wird am Kopf gelesen. Der Kopf muss als eigene
   Form aus der Schulterlinie herausragen — schmaler als die Schultern, aber
   deutlich abgesetzt, mit einem waagerechten Visierschlitz, der emissiv leuchtet.
2. **Die Oberkante ist zerfranst.** Ein Dutzend kleiner Zacken auf Schultern und
   Ruecken lesen sich als Rauschen, nicht als Design. Weniger, groessere,
   klarer gerichtete Formen: zwei grosse Schulterplatten, die nach hinten-oben
   auslaufen. Kleinteile weg.
3. **Die Arme sind unlesbar.** Links ragt ein Rohr ins Nichts, rechts haengt eine
   flache Platte wie ein abgerissenes Schild. Beide Arme muessen als Arm lesbar
   sein: Oberarm, Ellbogen, Unterarm, in Ruhe leicht angewinkelt am Koerper.
4. **Keine Taille.** Oberkoerper und Huefte verschmelzen zu einem Block. Die
   Taille muss in der Silhouette als Einschnuerung sichtbar sein.

**Bugs (keine Geschmacksfrage):**
5. **Arme asymmetrisch und verdreht.** Report: min x -2.387, max x +2.539 —
   fast 15 cm Schieflage. Ruhepose beider Arme muss spiegelgleich sein.
6. **Weisse Platte auf der rechten Brust** (01_front) wirkt wie ein
   Materialfehler — `mech_edge` auf einer grossen Flaeche statt als duenne Kante.
7. **Masse ueber Vorgabe:** Hoehe 6.27 statt 6.10 m, Breite 4.93 statt 4.20 m.

**Detailarmut:**
8. **29 460 Dreiecke** — die Vorgabe war 40 000 bis 80 000. Zu wenige Dreiecke
   heisst hier zu wenig Fase und zu wenig Plattenversatz. Genau die zwei Merkmale,
   die den Unterschied machen. Steig auf 45 000 bis 65 000, und setz sie in
   Silhouettenkanten: Schulterplatten, Knieklingen, Fussklauen, Kopfvisier.
9. **Merkmal 3 der Spec fehlt vollstaendig: Trapeze statt Quader.** Praktisch
   jede Platte hat noch vier gleich lange Kanten. Verjuenge Platten, lass sie
   spitz auslaufen, schraege die Enden an.

**Positiv und beizubehalten:** Die Fussklauen lesen sich in der Silhouette
bereits als Klauen. Die Beinkontur ist gut. Fugenlicht-Verteilung stimmt.

---

# NACHTRAG — direkter Vergleich mit der Vorlage (02.09.2026 23:36)

Er hat Runde 1 gesehen. Wortlaut: *„schlecht ist es nicht, aber die Vorlage
hatte ein viel sleekeres Design und vor allem so Flügel und Schulterplatten."*

**Das ist die wichtigste Aenderung dieser Runde. Sie geht den Punkten 1-9 vor.**
Runde 1 ist zu klobig und zu kleinteilig. Das Vorbild ist schlank und elegant,
nicht massig.

## A) Sleek — schlank statt klobig

- **Grosse, durchgehende Flaechen statt vieler Kleinteile.** Runde 1 hat auf
  Schultern und Ruecken ein Dutzend kleiner Kaesten. Ersetze sie durch wenige
  grosse, glatte Panzerflaechen mit klarer Kante. Jedes Bauteil, das kleiner
  als 15 cm ist und nicht in der Silhouette liegt, kommt weg.
- **Schlankere Proportionen.** Der Oberkoerper darf nicht als Wuerfel lesen.
  Brust breit oben, deutlich verjuengt zur Taille. Oberarme und Oberschenkel
  schlank und lang, nicht gedrungen.
- **Lange, gerichtete Linien.** Fugen und Kanten laufen ueber mehrere Bauteile
  durch, statt an jedem Teil zu enden. Das ist es, was „sleek" ausmacht.
- Glatt heisst **nicht** rund: die Kanten bleiben scharf gefast. Glatte grosse
  Flaeche, harte Kante.

## B) Fluegel — Pflicht, fehlen komplett

Am Ruecken bzw. den Schultern sitzen **zwei grosse fluegelartige Platten**, die
nach hinten-oben und aussen ragen. Sie sind das, was die Silhouette unverwechselbar
macht.
- Duenn (8-15 cm), **lang** (1,6-2,4 m), nach aussen spitz zulaufend.
- Leicht nach hinten geneigt, V-foermig gespreizt, spiegelsymmetrisch.
- Innen an der Wurzel dicker, zur Spitze auslaufend — ein Trapez, kein Rechteck.
- Fugenlicht laeuft als **durchgehende Linie** an der Innenkante entlang.
- Sie duerfen die Breitenvorgabe (Radius 2,1 m) nach hinten ueberschreiten, aber
  nicht seitlich: sie ragen nach hinten-oben, nicht zur Seite.
- Haenge sie an `Backpack`, damit sie sich mit dem Oberkoerper drehen.

## C) Schulterplatten — gross, formgebend, nicht kleinteilig

**Zwei grosse Schulterpanzer**, die ueber die Schultergelenke gestuelpt sind und
seitlich sowie nach oben ueber sie hinausragen.
- Je eine **einzige grosse Form** pro Schulter, nicht ein Stapel Kaesten.
- Von oben gesehen leicht nach aussen abfallend; von vorn: obere Kante hoeher
  als das Gelenk, untere Kante deckt den Oberarmansatz.
- Vorderkante spitz nach vorn-unten auslaufend (Trapez).
- Optional eine schmale zweite Platte darueber, versetzt, mit dunkler Fuge —
  das ist der Plattenversatz aus der Spec, in gross.
- Sie sind das Erste, was man auf dem Thumbnail sieht. Bau sie zuerst.

## Abnahme dieser Runde

Die Silhouette (08) muss auf einen Blick zeigen: **Schulterplatten und Fluegel
bestimmen die Form**, darunter ein schlanker Koerper. Wenn die Silhouette wie ein
breiter Kasten mit Beinen aussieht, ist sie nicht fertig.


---

# VERGLEICH: `REFERENZ-1.jpg` (in diesem Ordner) gegen Runde 1

**Sieh dir `REFERENZ-1.jpg` selbst an, bevor du baust.** Das ist die Vorlage des
Auftraggebers. Kein Nachbau — das Bild ist urheberrechtlich geschuetzt
(© NoveltyVariety). Genommen wird die **Formsprache**, nicht das Design.

Der Vergleich zeigt vier Unterschiede, die schwerer wiegen als alles andere:

## 1. Die Fluegel sind das praegende Element — sie fehlen ganz

Die Vorlage traegt **zwei grosse, flache, flügelartige Platten** ueber den
Schultern, die weit nach aussen und leicht nach oben ragen. Sie machen etwa ein
Drittel der Silhouette aus und sind das Erste, was man sieht. Flach wie ein
Tragfluegel, nach aussen spitz auslaufend, an der Oberseite eine schmale
Leuchtlinie. Runde 1 hat davon nichts.

## 2. Das Orange ist bei dir viel zu viel

Die Vorlage ist zu ueber 90 % **dunkles Metall**. Orange kommt nur als **duenne
kurze Linie oder kleine Flaeche** vor — vielleicht ein Dutzend Stellen am ganzen
Koerper, jede klein. Runde 1 hat dutzende dicke Leuchtbalken auf jeder Platte;
das liest sich als Leuchtreklame, nicht als Kampfmaschine. **Reduziere das
Fugenlicht auf ein Drittel** und mach die Linien duenner und kuerzer. Die Wirkung
kommt vom Glanz des Lacks, nicht von der Menge Licht.

## 3. Anthrazit mit Verlauf, nicht flaches Schwarz

Die Vorlage ist **dunkelgrau-anthrazit** und zeigt auf jeder grossen Flaeche
einen weichen Hell-dunkel-Verlauf — deshalb wirkt sie edel. Runde 1 ist fast
reines Schwarz, dadurch verschwindet die Form. Heb `mech_body` auf etwa
**#1a1d22** an und lass `mech_plate` etwas heller (#252a31), damit sich die
Platten voneinander abheben.

## 4. Alles ist laenglich, nichts ist gedrungen

In der Vorlage ist praktisch **jedes** Bauteil deutlich laenger als breit und
laeuft an einem Ende spitz zu — Schulterplatten, Unterarme, Oberschenkel, Waden,
Zehen. Runde 1 besteht aus wuerfelnahen Kaesten. **Streck jedes Bauteil auf
mindestens 1,8:1** und schraege ein Ende an. Das allein bringt den groessten Teil
des „sleek"-Effekts.

## Ausserdem in der Vorlage, in dieser Reihenfolge wichtig

- Beine **lang und schlank**, mit langen durchgehenden Panzerstreifen an der
  Aussenseite. Nicht dicke kurze Bloecke.
- **Fussklauen mit langen, spitzen Zehen**, die weit nach vorn ragen.
- Der Kopf ist klein, sitzt tief — aber ein **waagerechter Visierschlitz** ist
  klar erkennbar.
- Am Ruecken ein **Waffen-/Geraetepaket**, das die Silhouette nach hinten
  ausbeult. Das darf an `Backpack` haengen.
- Weisse Kantenlichter nur an **wenigen** Kanten, sehr duenn.

## Abnahme

Leg deinen neuen `08_silhouette.png` neben die Vorlage. Wenn die Vorlage breite
Fluegel und einen schlanken Koerper zeigt und deine Silhouette einen breiten
Kasten mit Beinen, ist sie nicht fertig.
