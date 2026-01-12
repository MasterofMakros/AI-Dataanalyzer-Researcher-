# TEMPLATE: Runbook (Operational Guide)

> **Basierend auf Google SRE & AWS Best Practices (2025)**
> **Kopiere dieses Template nach `docs/runbooks/RUNBOOK-XXX-titel.md`**

---

# RUNBOOK-XXX: [Titel der Operation]

<!-- 
ANLEITUNG:
- Ersetze XXX mit der nächsten fortlaufenden Nummer.
- Der Titel sollte klar beschreiben, WAS gemacht wird.
- Beispiel: "RUNBOOK-001: Neustart des n8n Containers"
-->

## Metadaten

| Attribut | Wert |
| :--- | :--- |
| **Erstellt** | YYYY-MM-DD |
| **Letztes Update** | YYYY-MM-DD |
| **Owner** | [Name / Rolle] |
| **Review-Zyklus** | [z.B. "Quartalsmäßig"] |
| **Komplexität** | [Einfach / Mittel / Komplex] |
| **Geschätzte Dauer** | [z.B. "5 Minuten"] |

---

## 🚨 Auslöser (Wann brauche ich das?)

<!-- Beschreibe die Situation(en), die dieses Runbook erfordern -->

- [ ] Der Service [X] reagiert nicht mehr.
- [ ] Alert "[Alert-Name]" wurde ausgelöst.
- [ ] Routinemäßige Wartung (z.B. monatliches Update).
- [ ] [Anderer Auslöser]

---

## ✅ Voraussetzungen

<!-- Was muss vorhanden sein, bevor man beginnt? -->

### Zugänge
- [ ] SSH-Zugang zum Server (via Tailscale)
- [ ] Docker CLI verfügbar (`docker --version`)
- [ ] [Weitere Zugänge]

### Tools
```bash
# Überprüfe, ob alle Tools installiert sind:
docker --version
ssh -V
```

### Wissen
- Grundverständnis von Docker Compose
- Zugriff auf `F:\conductor\docker_stack\`

---

## 📋 Schritt-für-Schritt-Anleitung

<!-- 
WICHTIG:
- Jeder Schritt muss atomar und ausführbar sein.
- Füge erwartete Outputs hinzu.
- Nutze Code-Blöcke für Befehle.
-->

### Schritt 1: [Beschreibung]

```bash
# Befehl eingeben:
[BEFEHL HIER]
```

**Erwarteter Output:**
```
[Beispiel-Output hier]
```

**⚠️ Falls anders:** [Was tun, wenn der Output abweicht?]

---

### Schritt 2: [Beschreibung]

```bash
[BEFEHL HIER]
```

**Erwarteter Output:**
```
[Beispiel-Output hier]
```

---

### Schritt 3: [Beschreibung]

```bash
[BEFEHL HIER]
```

---

## 🔄 Rollback-Prozedur

<!-- Was tun, wenn etwas schiefgeht? -->

### Symptome für Rollback
- [ ] Service startet nicht nach 2 Minuten.
- [ ] Fehlermeldung "[Spezifische Fehlermeldung]" erscheint.
- [ ] [Anderes Symptom]

### Rollback-Schritte

1. **Stoppe die aktuelle Aktion:**
   ```bash
   [STOPP-BEFEHL]
   ```

2. **Stelle den vorherigen Zustand wieder her:**
   ```bash
   [ROLLBACK-BEFEHL]
   ```

3. **Verifiziere Rollback:**
   ```bash
   [VERIFIZIERUNGS-BEFEHL]
   ```

4. **Eskaliere:**
   - Kontaktiere: [Name / Kanal]
   - Erstelle Incident-Ticket: [Link]

---

## ✔️ Verifizierung (Woran erkenne ich Erfolg?)

<!-- Wie weiß ich, dass die Aktion erfolgreich war? -->

### Checkliste

- [ ] Service [X] ist erreichbar unter [URL/Port].
- [ ] Keine Fehler in den Logs (`docker logs [container]`).
- [ ] Dashboard zeigt "Healthy" Status.
- [ ] [Weitere Erfolgskriterien]

### Verifizierungs-Befehle

```bash
# Health-Check:
curl -s http://localhost:[PORT]/health

# Log-Check (letzte 10 Zeilen):
docker logs --tail 10 [CONTAINER_NAME]
```

**Erwarteter Output für Erfolg:**
```
{"status": "healthy"}
```

---

## 📞 Eskalation

<!-- An wen wende ich mich, wenn das Runbook nicht funktioniert? -->

| Stufe | Kontakt | Wann? |
| :--- | :--- | :--- |
| **Level 1** | [Owner dieses Runbooks] | Nach 15 Min ohne Lösung |
| **Level 2** | [Architekt / Senior] | Bei Datenverlust-Risiko |
| **Level 3** | [Externer Support] | Bei Hardware-Ausfall |

---

## 📝 Changelog

<!-- Dokumentiere alle Änderungen an diesem Runbook -->

| Datum | Änderung | Autor |
| :--- | :--- | :--- |
| YYYY-MM-DD | Initiale Version | [Name] |
| YYYY-MM-DD | [Beschreibung der Änderung] | [Name] |

---

## 🔗 Verknüpfte Dokumente

- ADRs: [ADR-XXX](../ADR/ADR-XXX-titel.md)
- Andere Runbooks: [RUNBOOK-XXX](./RUNBOOK-XXX-titel.md)
- Monitoring Dashboard: [Link]
