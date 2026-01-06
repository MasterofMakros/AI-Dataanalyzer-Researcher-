#!/bin/bash

# setup_rag_pi.sh
# Deployment script for Conductor Track-003
# Run this on your Raspberry Pi to install the AI Brain Stack

set -e # Exit on error

echo "============================================="
echo "   Conductor: Deploying AI Stack on Pi 5"
echo "============================================="

# 1. Install Docker (Panic if missing)
if ! [ -x "$(command -v docker)" ]; then
  echo "[!] Docker not found. Installing..."
  curl -fsSL https://get.docker.com -o get-docker.sh
  sh get-docker.sh
  sudo usermod -aG docker $USER
  echo "[+] Docker installed. Please re-login!"
  exit 1
fi

echo "[+] Docker is present."

# 2. Check for F: Mount (Simulation)
if [ ! -d "/mnt/f_drive" ]; then
    echo "[!] WARNING: /mnt/f_drive does not exist."
    echo "    Please make sure your USB drive is mounted to /mnt/f_drive"
    echo "    Creating dummy folder for now..."
    sudo mkdir -p /mnt/f_drive
fi

# 3. Start the Stack
echo "[*] Spinning up the Brain Stack..."
docker compose -f docker-compose.yml up -d

# 4. Pull Models (The "Model Portfolio")
echo "[*] Waiting for LLM Engine to wake up..."
sleep 10

echo "[*] Pulling Primary Model: Phi-3 Mini (3.8B)..."
docker exec -it llm-engine ollama pull phi3:mini

echo "[*] Pulling Refactoring Model: Qwen 2.5 Coder (1.5B)..."
docker exec -it llm-engine ollama pull qwen2.5-coder:1.5b

echo "[*] Pulling Embedding Model: Nomic..."
docker exec -it llm-engine ollama pull nomic-embed-text

echo "============================================="
echo "   SUCCESS! Stack is running."
echo "   Interface: http://$(hostname -I | awk '{print $1}'):3001"
echo "============================================="
