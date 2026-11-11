# Duplex Merge – Custom App für TrueNAS SCALE

Eine einfache, eigenständige **TrueNAS Custom App** zum Zusammenführen von zwei einseitigen Scan-Durchgängen eines Brother MFC-J5340DWE. Die fertige PDF-Datei wird in den Consume-Ordner von Paperless-ngx geschrieben.

## Ablauf

1. Vorderseiten eines Dokuments mit dem Brother-SMB-Profil `Duplex Vorderseiten` in `front/` scannen.
2. Stapel umdrehen und die Rückseiten mit `Duplex Rückseiten` in `back/` scannen.
3. Die App wartet mindestens 15 Sekunden nach dem letzten Dateischreibvorgang, prüft die PDF-Seitenzahlen, kehrt bei Bedarf die Reihenfolge der Rückseiten um und erzeugt eine PDF in Paperless `Consume`.
4. Beide Originaldateien werden nach erfolgreicher Prüfung in `archive/` aufbewahrt.

**Wichtig:** Immer nur EIN Dokument gleichzeitig bearbeiten. Unterschiedliche Scan-Jobs lassen sich ohne eine gemeinsame Job-ID nicht zuverlässig automatisch zuordnen. `front/` und `back/` müssen vor Beginn eines neuen Dokumentes leer sein. Paperless kann die fertige Datei recht schnell aus dem Consume-Ordner abholen.

## Installation

1. Bestehende tatsächliche Dataset-Pfade überprüfen; `/mnt/POOLNAME/Apps/Paperless/Consume` ist nur ein Beispiel.
2. Im TrueNAS-Dataset folgende Verzeichnisse anlegen: `Apps/DuplexMerge/{front,back,archive,error}`. Die beiden SMB-Ziele sollen in `front` und `back` schreiben dürfen. App muss in allen Verzeichnissen lesen/schreiben dürfen.
3. `app.py` nach `/mnt/POOLNAME/Apps/DuplexMerge/app.py` kopieren. Am besten aus der TrueNAS-Shell oder per SMB in einen zugänglichen Admin-Ordner und dann verschieben.
4. `compose.yaml` öffnen und alle `POOLNAME`-Platzhalter ersetzen. Besonders wichtig: Paperless Consume **tatsächlich** verwendeten Host-Pfad kontrollieren. Die Consume-Freigabe darf nicht nochmals als Eingabequelle dienen.
5. TrueNAS: **Apps → Discover → ⋮ → Install via YAML**. App-Name `duplex-merge`, YAML einfügen, speichern.
6. Am Brother zwei SMB-Profile erstellen, die in die beiden Ordner schreiben. Einseitiger ADF-Scan, PDF, 300 dpi.
7. Probe: zwei beidseitig bedruckte Blätter jeweils einseitig scannen. Das Ergebnis sollte genau vier Seiten mit richtiger Reihenfolge enthalten.

## Einstellungen

- `REVERSE_BACK=true`: Rückseitenfolge umkehren. Das hängt davon ab, wie der Stapel beim zweiten Durchlauf eingelegt wird. Falls das Test-PDF die falsche Reihenfolge hat, `false` probieren.
- `MIN_AGE_SECONDS=15`: Verzögerung, damit noch laufende SMB-Dateiübertragungen nicht sofort verarbeitet werden. Bei großen Dokumenten erhöhen.
- `POLL_SECONDS=5`: Prüfrhythmus.
- In `compose.yaml` wird `pypdf` beim Containerstart geladen; dafür braucht die App beim Start Internet. Später kann man ein eigenes versioniertes Docker-Image (z. B. über Forgejo CI) bauen, das das Paket bereits enthält.

## Fehler und Grenzen

- Bei ungleichen Seitenzahlen/kaputten PDFs: Logmeldung, Originale bleiben in `front/` und `back/`, bis der Fehler behoben wird. Nach einem Fehlschlag erfolgt ein neuer Versuch etwa jede Minute.
- Standardannahme: gerade Anzahl der Originalseiten; bei einseitiger letzter Seite eine leere Rückseite mitscannen oder nachbearbeiten.
- Die Zuordnung geschieht in der Reihenfolge des Dateieingangs. Daher keine parallelen Dokumente scannen.
- Die App hat bewusst keine Weboberfläche und keine offenen Netzwerkports.
- `error/` ist für eine mögliche spätere Quarantänefunktion reserviert; die erste Version verschiebt fehlerhafte Eingaben nicht automatisch.
- Dateisystemberechtigungen und SMB-ACLs müssen auf deinem TrueNAS passend konfiguriert sein. Prüfe Logs bei `Permission denied`.
- Stand: vorbereitetes Paket; **noch nicht auf deinem TrueNAS installiert oder getestet**.
