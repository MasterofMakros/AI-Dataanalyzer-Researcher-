# Conductor Deployment Script v3
# Usage: .\deploy_to_pi.ps1

param(
    [string]$Hostname = "DockerServices",
    [string]$Username = "docker"
)

Write-Host "🎹 Conductor Deployment to $Hostname" -ForegroundColor Cyan

# 1. Resolve IP
try {
    $ip = [System.Net.Dns]::GetHostAddresses($Hostname)[0].IPAddressToString
    Write-Host "   Target IP: $ip" -ForegroundColor Gray
}
catch {
    Write-Warning "Could not resolve hostname '$Hostname'. Trying '$Hostname.local'..."
    try {
        $Hostname = "$Hostname.local"
        $ip = [System.Net.Dns]::GetHostAddresses($Hostname)[0].IPAddressToString
        Write-Host "   Target IP: $ip" -ForegroundColor Gray
    }
    catch {
        Write-Error "Could not find Pi on the network. Check if it's turned on and connected."
        exit
    }
}

# 3. Credentials
$pass = Read-Host -Prompt "Enter Password for $Username@$Hostname (Hidden)" -AsSecureString

Write-Host "`n🚀 Step 1: Checking Docker..." -ForegroundColor Yellow
# Check if docker exists, if not install it
# We need to send the password for sudo. This is tricky. 
# We'll try to run a check first.
ssh $Username@$Hostname "which docker >/dev/null || (echo 'Docker missing. Installing...' && curl -fsSL https://get.docker.com -o get-docker.sh && sudo sh get-docker.sh && sudo usermod -aG docker $Username)"

Write-Host "`n🚀 Step 2: Preparing Folders..." -ForegroundColor Yellow
ssh $Username@$Hostname "mkdir -p ~/conductor"

Write-Host "`n🚀 Step 3: Transferring Stack..." -ForegroundColor Yellow
# FIX: docker-compose.yml is inside docker_stack folder usually, checking structure...
# Based on previous ls, we move contents.
$dest = "$($Username)@$($Hostname):~/conductor/"

# Copy folders
scp -r backend_api mission_control docker_stack requirements.txt README_PI.md $dest

# Copy docker-compose.yml (Handling path issue)
if (Test-Path "docker_stack\docker-compose.yml") {
    scp docker_stack\docker-compose.yml $dest
}
elseif (Test-Path "docker-compose.yml") {
    scp docker-compose.yml $dest
}
else {
    Write-Warning "docker-compose.yml not found in root or docker_stack!"
}

Write-Host "`n🚀 Step 4: Launching Docker..." -ForegroundColor Yellow
# Note: We added user to docker group, but it requires re-login. 
# We use 'newgrp docker' to activate it in the current session script
ssh $Username@$Hostname "cd ~/conductor && sudo docker compose up -d --build"

Write-Host "`n✅ Deployment Complete!" -ForegroundColor Green
Write-Host "   Dashboard: http://$Hostname:3000"
Write-Host "   API:       http://$Hostname:8000"
