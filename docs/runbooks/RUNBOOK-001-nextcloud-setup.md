# RUNBOOK-001: Nextcloud Setup mit 10TB External Storage

## Metadaten

| Attribut | Wert |
| :--- | :--- |
| **Erstellt** | 2025-12-26 |
| **Letztes Update** | 2025-12-26 |
| **Owner** | System Admin |
| **Review-Zyklus** | Bei Änderungen |
| **Komplexität** | Mittel |
| **Geschätzte Dauer** | 30-45 Minuten |

---

## 🚨 Auslöser (Wann brauche ich das?)

- [ ] Erstmalige Installation von Nextcloud auf dem Ryzen Mini-PC
- [ ] Migration von bestehendem Nextcloud zu neuem Server
- [ ] Nextcloud Container muss neu aufgesetzt werden
- [ ] External Storage (F:/) muss neu verbunden werden

---

## ✅ Voraussetzungen

### Hardware
- [ ] Ryzen AI Mini-PC läuft
- [ ] 10TB+ Laufwerk (F:/) ist gemountet und beschreibbar
- [ ] Netzwerk funktioniert (Tailscale/Cloudflare Tunnel)

### Software
- [ ] Docker Desktop / Docker Engine installiert
- [ ] Docker Compose verfügbar (`docker compose version`)
- [ ] Mindestens 2GB RAM frei für Nextcloud

### Zugänge
- [ ] Admin-Zugang zum Host-System
- [ ] (Optional) Cloudflare Dashboard für Tunnel-Konfiguration

---

## 📋 Schritt-für-Schritt-Anleitung

### Schritt 1: Verzeichnisstruktur erstellen

```powershell
# PowerShell als Administrator
mkdir F:\conductor\docker_stack\nextcloud
cd F:\conductor\docker_stack\nextcloud

# _Inbox Ordner erstellen (Magic Inbox)
mkdir F:\_Inbox
```

**Erwarteter Output:**
```
Verzeichnis: F:\conductor\docker_stack\nextcloud
```

---

### Schritt 2: Docker Compose Datei erstellen

Erstelle `docker-compose.yml`:

```yaml
# F:\conductor\docker_stack\nextcloud\docker-compose.yml

version: '3.8'

services:
  nextcloud:
    image: nextcloud:28-apache
    container_name: nextcloud
    restart: unless-stopped
    ports:
      - "8080:80"
    volumes:
      # Nextcloud interne Daten
      - nextcloud_data:/var/www/html
      # KRITISCH: Das 10TB Laufwerk F: als External Storage
      - F:/:/external/DataPool:rw
    environment:
      - MYSQL_HOST=nextcloud-db
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=${MYSQL_PASSWORD:-NextcloudSecure123!}
      - NEXTCLOUD_ADMIN_USER=admin
      - NEXTCLOUD_ADMIN_PASSWORD=${NEXTCLOUD_ADMIN_PASSWORD:-AdminSecure123!}
      - NEXTCLOUD_TRUSTED_DOMAINS=localhost nextcloud.gigsolutions.info
      - OVERWRITEPROTOCOL=https
    depends_on:
      - nextcloud-db
    networks:
      - nextcloud-net

  nextcloud-db:
    image: mariadb:10.11
    container_name: nextcloud-db
    restart: unless-stopped
    environment:
      - MYSQL_ROOT_PASSWORD=${MYSQL_ROOT_PASSWORD:-RootSecure123!}
      - MYSQL_DATABASE=nextcloud
      - MYSQL_USER=nextcloud
      - MYSQL_PASSWORD=${MYSQL_PASSWORD:-NextcloudSecure123!}
    volumes:
      - nextcloud_db:/var/lib/mysql
    networks:
      - nextcloud-net

volumes:
  nextcloud_data:
  nextcloud_db:

networks:
  nextcloud-net:
    driver: bridge
```

---

### Schritt 3: Container starten

```powershell
cd F:\conductor\docker_stack\nextcloud
docker compose up -d
```

**Erwarteter Output:**
```
[+] Running 3/3
 ✔ Network nextcloud-net       Created
 ✔ Container nextcloud-db      Started
 ✔ Container nextcloud         Started
```

**Warten auf Initialisierung (ca. 1-2 Minuten):**
```powershell
docker logs -f nextcloud
# Warten bis "Apache/2.4.x (Debian) configured" erscheint
# Dann Ctrl+C zum Beenden
```

---

### Schritt 4: External Storage App aktivieren

```powershell
# External Storage Support aktivieren
docker exec -u www-data nextcloud php occ app:enable files_external

# Prüfen ob aktiviert
docker exec -u www-data nextcloud php occ app:list | Select-String "files_external"
```

**Erwarteter Output:**
```
files_external: 1.XX.X
```

---

### Schritt 5: External Storage mounten

```powershell
# DataPool (F:/) als External Storage hinzufügen
docker exec -u www-data nextcloud php occ files_external:create `
    "DataPool" `
    local `
    null::null `
    -c datadir=/external/DataPool

# Für alle User verfügbar machen
docker exec -u www-data nextcloud php occ files_external:applicable --add-user=admin 1

# Storage-Liste anzeigen
docker exec -u www-data nextcloud php occ files_external:list
```

**Erwarteter Output:**
```
+----------+-----------+----------+--------------------+--------------+
| Mount ID | Mount Point | Storage | Configuration     | Options      |
+----------+-----------+----------+--------------------+--------------+
| 1        | /DataPool | Local    | datadir: /external | Admin: admin |
+----------+-----------+----------+--------------------+--------------+
```

---

### Schritt 6: Ersten Scan ausführen

```powershell
# Initiales Scannen aller Dateien (DAUERT LANGE bei 10TB!)
# Für den ersten Test nur _Inbox scannen:
docker exec -u www-data nextcloud php occ files:scan --path="admin/files/DataPool/_Inbox"

# SPÄTER: Vollständiger Scan (über Nacht laufen lassen)
# docker exec -u www-data nextcloud php occ files:scan --all
```

**Erwarteter Output:**
```
Starting scan for user 1 out of 1 (admin)
+---------+-------+--------+-------------+
| Folders | Files | Errors | Elapsed time|
+---------+-------+--------+-------------+
| 5       | 23    | 0      | 00:00:02    |
+---------+-------+--------+-------------+
```

---

### Schritt 7: Web-Zugang testen

1. Öffne Browser: `http://localhost:8080`
2. Login mit:
   - User: `admin`
   - Passwort: `AdminSecure123!` (oder dein gesetztes Passwort)
3. Navigiere zu "Files" → "DataPool"
4. Prüfe ob `_Inbox` Ordner sichtbar ist

---

### Schritt 8: Cron-Job für regelmäßigen Scan einrichten

```powershell
# Cron im Container aktivieren (statt AJAX)
docker exec -u www-data nextcloud php occ background:cron

# Windows Task Scheduler: Alle 15 Minuten Scan
# Erstelle: F:\conductor\scripts\nextcloud-cron.ps1
```

**Inhalt von `nextcloud-cron.ps1`:**
```powershell
# F:\conductor\scripts\nextcloud-cron.ps1
docker exec -u www-data nextcloud php occ files:scan --path="admin/files/DataPool/_Inbox" --shallow
docker exec -u www-data nextcloud php cron.php
```

---

## 🔄 Rollback-Prozedur

### Symptome für Rollback
- [ ] Nextcloud startet nicht (Container crasht)
- [ ] External Storage zeigt Fehler
- [ ] Dateien sind nicht sichtbar

### Rollback-Schritte

1. **Container stoppen:**
   ```powershell
   docker compose down
   ```

2. **Volumes löschen (VORSICHT: Löscht Nextcloud-Daten!):**
   ```powershell
   docker volume rm nextcloud_nextcloud_data nextcloud_nextcloud_db
   ```

3. **Neu starten:**
   ```powershell
   docker compose up -d
   ```

4. **Falls F:/ nicht mounted:**
   - Prüfe ob F:/ existiert: `Get-Volume`
   - Prüfe Docker Desktop Sharing Settings

---

## ✔️ Verifizierung (Woran erkenne ich Erfolg?)

### Checkliste

- [ ] `http://localhost:8080` zeigt Nextcloud Login
- [ ] Nach Login: "DataPool" Ordner ist sichtbar
- [ ] `_Inbox` Ordner ist in DataPool sichtbar
- [ ] Eine Testdatei in `F:\_Inbox\` legen → erscheint nach Scan in Nextcloud
- [ ] Container-Logs zeigen keine Errors: `docker logs nextcloud | Select-String "error"`

### Quick Health-Check

```powershell
# Container Status
docker ps | Select-String "nextcloud"

# Nextcloud Status
docker exec -u www-data nextcloud php occ status
```

**Erwarteter Output:**
```
  - installed: true
  - version: 28.x.x.x
  - versionstring: 28.x.x
  - edition:
  - maintenance: false
```

---

## 📞 Eskalation

| Stufe | Kontakt | Wann? |
| :--- | :--- | :--- |
| **Level 1** | Dieses Runbook erneut durchgehen | Zuerst |
| **Level 2** | Nextcloud Community Forum | Bei spezifischen Fehlern |
| **Level 3** | Docker Desktop Logs prüfen | Bei Container-Problemen |

---

## 📝 Changelog

| Datum | Änderung | Autor |
| :--- | :--- | :--- |
| 2025-12-26 | Initiale Version | Expertenteam |

---

## 🔗 Verknüpfte Dokumente

- [ADR-006: Nextcloud Integration](../ADR/ADR-006-nextcloud-integration.md)
- [Project Overview 2025](../project/overview_2025.md)
- [GLOSSARY.md](../GLOSSARY.md)
