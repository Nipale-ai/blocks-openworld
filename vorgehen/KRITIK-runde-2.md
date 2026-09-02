# Bildkritik Runde 2 (menschlich gesichtet, 02.09.2026 23:50)

Gesichtet: 08_silhouette, 07_thumbnail, 01_front — jeweils neben `REFERENZ-1.jpg`.

## Behoben, nicht mehr anfassen
- Symmetrie: x -2.05 / +2.05 — der Schiefstand ist weg.
- Masse: 6.02 m hoch, 4.09 m breit. Passt.
- 44 968 Dreiecke — im Zielband.
- Kopf ragt aus der Schulterlinie, Taille ist in der Silhouette sichtbar.
- Beine lang und schlank, Klauenfuesse mit langen Zehen lesen sich hervorragend.
- Orange ist richtig dosiert. Nicht weiter reduzieren.

## Ins Gegenteil gekippt — das sind die zwei Hauptfehler dieser Runde

### 1. Er ist jetzt zu duenn. Die Vorlage ist schlank UND massiv.
Runde 1 war klobig, Runde 2 ist zerbrechlich. Beides falsch. Sieh dir
`REFERENZ-1.jpg` genau an: die Taille ist schmal, aber **alles andere ist dick
gepanzert** — Oberschenkel massig, Waden voluminoes, Schulterpartie breit und
tief, Unterarme kraeftig. Schlank heisst dort **laenglich**, nicht **duenn**.
- Oberschenkel und Waden auf etwa **das 1,4-fache Volumen** bringen.
- Unterarme und Oberarme deutlich staerker panzern.
- Der Brustkorb muss **tiefer** werden (in Z), nicht nur breit.
- Die Laenge und die spitzen Enden bleiben, wie sie sind.

### 2. Die Fluegel sind zu Nadeln geworden.
In der Vorlage sind es **breite, flache Tragflaechen** — massive Platten mit
Flaeche, die man als Flaeche sieht. Bei dir sind es duenne Striche, die wie
Antennen wirken. Sie sind in 07_thumbnail kaum als Fluegel erkennbar.
- Breite (in Y/Z, also die sichtbare Flaeche) auf **40-70 cm** bringen —
  aktuell wirken sie unter 10 cm.
- Laenge 1,6-2,2 m beibehalten, weiter nach aussen-hinten spitz auslaufen lassen.
- Dicke duenn (8-14 cm) lassen: eine Platte, kein Balken.
- Zwei pro Seite ist erlaubt (eine grosse, eine kleinere versetzt darunter) —
  so macht es die Vorlage.

## Ebenfalls offen

### 3. Zu dunkel — das ist fuer ein Thumbnail das K.-o.-Kriterium.
In 01_front verschwindet der halbe Mecha im Hintergrund. Der Grundton wurde
nicht angehoben. Zwei Massnahmen, beide noetig:
- `mech_body` auf **#1a1d22** und `mech_plate` auf **#252a31** setzen, wie
  gefordert. Nicht dunkler.
- Im Renderskript ein **zweites Licht von vorn-seitlich** dazu (Fuellicht,
  ca. 25 % der Hauptlichtstaerke), und den Hintergrund einen Tick heller, damit
  die schwarze Silhouette sich abhebt.

### 4. Die Schulterplatten sind fast verschwunden.
Aktuell sitzen dort kleine Kaesten. Gebraucht wird **je eine grosse Platte pro
Schulter**, die das Gelenk ueberdeckt, seitlich darueber hinausragt und nach
vorn-unten spitz auslaeuft. Sie sind zusammen mit den Fluegeln das, was den
Mecha auf dem Thumbnail ausmacht.

### 5. Der Kopf ist ein Sensorturm, kein Kopf.
Ein weisser Aufsatz mit Antenne. Gebraucht wird ein **waagerechter
Visierschlitz**, der emissiv leuchtet (`mech_eyes`), in einem Helm, der nach
hinten schmaler wird. Der Kopf darf klein bleiben.

### 6. Die weisse Flaeche auf der rechten Brust ist immer noch da.
Sie steht in 01_front deutlich sichtbar rechts der Mitte und wirkt wie ein
Materialfehler — `mech_edge` liegt dort auf einer grossen Flaeche statt als
duenne Kante. Entweder auf `mech_plate` umstellen oder auf eine schmale
Kantenleiste verkleinern.

## Abnahme
07_thumbnail muss ohne Anstrengung lesbar sein: breite Fluegel, grosse
Schulterplatten, massive Beine, schmale Taille — und man muss die Form sehen,
nicht nur ahnen.
