# Duplex Merge – fertiges Docker-Image für TrueNAS SCALE

Die App verbindet manuelle Duplex-Scans: `front/` und `back/` als PDFs eingeben, fertig zusammengeführte PDFs an Paperless-ngx `consume/` ausgeben. Originale werden im Archiv behalten. **Ein Dokument zurzeit**.

## Image auf GHCR veröffentlichen (einmalig)

Ein `docker pull` funktioniert erst, wenn ein Image in einer Registry veröffentlicht wurde. Dieses Paket enthält den kompletten Build samt GitHub-Actions-Workflow.

1. Auf GitHub ein neues **öffentliches** Repository namens `duplex-merge` erstellen (ohne README initialisieren).
2. Den **Inhalt dieses ZIP-Archivs** im Repository auf den Branch `main` hochladen. Wichtig: `.github/workflows/publish.yml` muss mit hochgeladen werden (verstecktes Verzeichnis). Alternativ mit Git committen und pushen.
3. In GitHub unter **Actions → Publish Docker image to GHCR** nachsehen; bei Bedarf **Run workflow** starten. In Repository-Einstellungen ggf. Actions-Schreibrechte für Pakete zulassen.
4. Das veröffentlichte Paket unter **Packages** auf **Public** stellen, falls es zunächst privat ist; sonst benötigt TrueNAS Registry-Zugangsdaten.
5. Image-Name: `ghcr.io/DEIN_GITHUB_NUTZERNAME/duplex-merge:latest` (Benutzername kleingeschrieben).

Das Image enthält Python und pypdf. Bei jedem Container-Start werden **keine** Pakete neu heruntergeladen, nur das Image wird beim ersten Start gezogen.

## TrueNAS SCALE

1. Die Ordner `front`, `back`, `archive`, `error` in `/mnt/POOLNAME/Apps/DuplexMerge/` anlegen. Den tatsächlichen Paperless-Consume-Pfad überprüfen. Auf TrueNAS muss die App auf diese Pfade zugreifen können; SMB-Schreibrechte für den Brother auf `front` und `back` vergeben.
2. Apps → Discover → **Install via YAML**; `compose.yaml` einfügen. `GITHUBUSER` (lowercase) und `POOLNAME` durch echte Werte ersetzen, sowie den Consume-Pfad, wenn er anders lautet.
3. Zwei Brother-SMB-Scanprofile erstellen: Front-PDF nach `front/` und Back-PDF nach `back/`. PDF, ADF, 300 dpi.
4. Mit zwei beidseitig bedruckten Blättern testen. Es sollte ein vierseitiges PDF in Paperless erscheinen.

### Optionen

- `REVERSE_BACK=true`: Reihenfolge der rückseitigen Seiten umkehren; je nach Einlegeart `false` nötig.
- `MIN_AGE_SECONDS=15`: Dateien erst nach einer Ruhezeit bearbeiten.
- `POLL_SECONDS=5`: Intervall zur Prüfung.

**Sicherheit & Grenzen:** Nur ein Dokument gleichzeitig; Vorder- und Rückseiten werden zeitlich zugeordnet, nicht durch Job-ID. Die App prüft, dass die PDFs gleich viele Seiten haben. Bei Fehlern bleiben Originale liegen und es wird erneut versucht. Für Dokumente mit ungerader Blattseitenzahl muss ggf. eine leere Rückseite erfasst werden. Keine Netzwerkports. Keine Weboberfläche. Bisher nicht live auf TrueNAS getestet.

## Optional: lokal bauen und pushen

```bash
docker build -t ghcr.io/DEIN_GITHUB_NUTZERNAME/duplex-merge:latest .
docker login ghcr.io
docker push ghcr.io/DEIN_GITHUB_NUTZERNAME/duplex-merge:latest
```

Ein lokal gebautes `.tar`-Archiv wäre **kein** `docker pull`: Es müsste mit `docker load` importiert werden. Für 'nur Image Pull' ist GHCR die passende Variante.
