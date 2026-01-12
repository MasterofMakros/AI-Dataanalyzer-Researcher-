#!/bin/bash
# Bash Test File 1: System Administration
# Expected: Extract functions and commands

# Konfiguration
LOG_DIR="/var/log/myapp"
BACKUP_DIR="/backup"

# Funktion: Backup erstellen
create_backup() {
    local source="\"
    local dest="\/\.tar.gz"
    
    echo "Erstelle Backup von \..."
    tar -czf "\" "\"
    echo "Backup erstellt: \"
}

# Funktion: Logs rotieren
rotate_logs() {
    find "\" -name "*.log" -mtime +7 -exec gzip {} \;
    echo "Logs Ã¤lter als 7 Tage komprimiert"
}

# Hauptprogramm
main() {
    echo "=== System Maintenance ==="
    create_backup "/etc"
    rotate_logs
    echo "Fertig!"
}

main "\$@"
