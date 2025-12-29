# 🎹 Conductor Setup Guide (Raspberry Pi 5)

**Role**: Conductor (Control Plane)
**Hardware**: Raspberry Pi 5 (8GB RAM recommended)
**OS**: Raspberry Pi OS (64-bit) / Ubuntu Server

---

## 🚀 1. Transfer Files
Copy the entire `F:\conductor` folder to your Pi.
Recommended target: `~/conductor`

## 🐳 2. Install Docker (One-Time)
Run this on the Pi if you haven't yet:
```bash
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
sudo usermod -aG docker $USER
# LOGOUT and LOGIN again!
```

## ⚡ 3. Start the Brain
Navigate to the folder and launch the stack:
```bash
cd ~/conductor
docker compose -p conductor up -d --build
```

### ✅ Verification
1.  Check Process: `docker ps`
    *   Should show: `conductor-redis`, `conductor-api`, `conductor-traefik`, `conductor-ui`.
2.  Check Logs: `docker logs -f conductor-api`
3.  Check UI: Open `http://<PI-IP>:8080/dashboard` (Traefik) or `http://<PI-IP>:3000` (Mission Control).

---

## 🛑 Maintenance
*   **Stop**: `docker compose down`
*   **Update**: Copy new files -> `docker compose up -d --build`
*   **Logs**: `docker compose logs -f`

---

## 🔒 Security Note (Tailscale)
Since we use Tailscale, ensure the Pi is connected:
`sudo tailscale up`
The `conductor-api` will be available at `http://conductor-api:8000` (via magic DNS) or the Tailscale IP.
