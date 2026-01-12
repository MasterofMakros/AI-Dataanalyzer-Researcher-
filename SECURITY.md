# Security Policy

## Unterstuetzte Versionen

| Version | Unterstuetzt |
|---------|--------------|
| main    | ✅           |
| < 1.0   | ❌           |

## Sicherheitsprinzipien

Conductor wurde mit folgenden Sicherheitsprinzipien entwickelt:

1. **100% Lokal** - Keine Daten verlassen dein System
2. **Keine Cloud-Abhaengigkeiten** - Alle KI-Modelle laufen lokal
3. **Secrets in .env** - Niemals hartcodierte Credentials

## Sicherheitsluecke melden

**Bitte melde Sicherheitsluecken NICHT oeffentlich ueber GitHub Issues.**

### Meldeprozess

1. **Email**: Sende Details an security@conductor-project.local (oder oeffne ein privates GitHub Issue)
2. **Verschluesselung**: Nutze PGP wenn verfuegbar
3. **Details**: Beschreibe die Luecke so detailliert wie moeglich:
   - Art der Schwachstelle
   - Betroffene Komponenten
   - Schritte zur Reproduktion
   - Moegliche Auswirkungen

### Was du erwarten kannst

- **Bestaetigung**: Innerhalb von 48 Stunden
- **Erste Einschaetzung**: Innerhalb von 7 Tagen
- **Fix**: Abhaengig von Schweregrad
- **Credit**: Anerkennung im CHANGELOG (auf Wunsch)

## Bekannte Sicherheitsaspekte

### Docker Container

- Container laufen standardmaessig nicht als root
- Netzwerk ist auf lokales Docker-Netzwerk beschraenkt
- Volumes sind auf definierte Pfade begrenzt

### Credentials

- `.env` Datei enthaelt Secrets und ist in `.gitignore`
- `.env.example` enthaelt nur Platzhalter
- Meilisearch/Qdrant API Keys sind standardmaessig gesetzt

### Datenzugriff

- Alle Daten bleiben auf dem Host-System
- Keine externen API-Aufrufe (ausser bei manueller Konfiguration)
- Ollama und andere KI-Modelle laufen komplett lokal

## Best Practices fuer Betreiber

1. **Firewall**: Blockiere externe Zugriffe auf Ports 3100, 6335, 8010, 8040
2. **Updates**: Halte Docker Images aktuell
3. **Backups**: Sichere `ledger.db` und `.env` regelmaessig
4. **Secrets**: Generiere eigene Passwoerter fuer Produktion

```bash
# Neue sichere Passwoerter generieren
openssl rand -hex 32
```

## Abhaengigkeiten

Wir ueberwachen Abhaengigkeiten auf bekannte Schwachstellen:

- Python: `pip-audit`
- Node.js: `npm audit`
- Docker Images: Regelmaessige Updates

---

Danke fuer deinen Beitrag zur Sicherheit von Conductor!
