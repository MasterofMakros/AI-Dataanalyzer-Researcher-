# Contributing to Conductor

Danke fuer dein Interesse an Conductor! Dieses Dokument erklaert, wie du zum Projekt beitragen kannst.

## Entwicklungsumgebung einrichten

### Voraussetzungen

- Docker Desktop (Windows) oder Docker Engine (Linux)
- Python 3.11+
- Node.js 18+ (fuer Frontend)
- Git

### Setup

```bash
# Repository klonen
git clone https://github.com/MasterofMakros/AI-Dataanalyzer-Researcher-.git
cd AI-Dataanalyzer-Researcher

# Environment konfigurieren
cp .env.example .env

# Backend-Abhaengigkeiten (optional, fuer lokale Entwicklung)
python -m venv venv
source venv/bin/activate  # Linux/Mac
# oder: .\venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Frontend-Abhaengigkeiten
cd mission_control_v2
npm install
cd ..

# Docker Services starten
docker compose up -d
```

## Code Style

### Python

- Verwende [Black](https://github.com/psf/black) fuer Formatierung
- Folge [PEP 8](https://pep8.org/)
- Type Hints sind erwuenscht
- Docstrings fuer oeffentliche Funktionen

```bash
# Formatierung pruefen
black --check .

# Automatisch formatieren
black .
```

### TypeScript/React

- ESLint Konfiguration beachten
- Funktionale Komponenten bevorzugen
- TypeScript strict mode

```bash
cd mission_control_v2
npm run lint
```

### Commits

Wir verwenden [Conventional Commits](https://www.conventionalcommits.org/):

```
feat: Add new feature
fix: Fix bug
docs: Update documentation
chore: Maintenance tasks
refactor: Code refactoring
test: Add tests
```

Beispiele:
- `feat: Add PDF preview in Neural Search`
- `fix: Correct SSE streaming timeout`
- `docs: Update API documentation`

## Pull Requests

1. **Fork** das Repository
2. Erstelle einen **Feature Branch** (`git checkout -b feature/mein-feature`)
3. **Committe** deine Aenderungen
4. **Push** zum Branch (`git push origin feature/mein-feature`)
5. Oeffne einen **Pull Request**

### PR Checkliste

- [ ] Code folgt dem Style Guide
- [ ] Tests hinzugefuegt/aktualisiert
- [ ] Dokumentation aktualisiert
- [ ] CHANGELOG.md aktualisiert (bei Features/Fixes)
- [ ] Keine Secrets im Code

## Issues

### Bug Reports

Nutze das Bug Report Template und gib an:
- Erwartetes Verhalten
- Tatsaechliches Verhalten
- Schritte zur Reproduktion
- System-Informationen (OS, Docker Version, etc.)

### Feature Requests

Nutze das Feature Request Template und beschreibe:
- Das Problem, das geloest werden soll
- Die vorgeschlagene Loesung
- Alternativen, die du betrachtet hast

## Architektur-Entscheidungen

Groessere technische Entscheidungen werden als ADR (Architecture Decision Record) dokumentiert:

1. Erstelle eine neue Datei in `docs/ADR/`
2. Nutze das Template `docs/TEMPLATES/TEMPLATE-ADR.md`
3. Diskutiere im Issue/PR

## Fragen?

- Oeffne ein [GitHub Issue](https://github.com/MasterofMakros/AI-Dataanalyzer-Researcher-/issues)
- Lies die [Dokumentation](docs/)

---

Danke fuer deinen Beitrag!
