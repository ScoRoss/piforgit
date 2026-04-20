# Vault-System: Fleet Ingest Unit (Pi 5)

This repository contains the software for the Raspberry Pi 5 video ingest units. Each unit captures video from a V4L2-compatible camera and streams it to a central server using the SRT (Secure Reliable Transport) protocol, optimized for stability over cellular (5G/LTE) networks.

## Overview
- **Hardware:** Raspberry Pi 5
- **Encoder:** FFmpeg utilizing libx264
- **Protocol:** SRT (Caller mode) with a 30-second recovery buffer
- **Architecture:** Docker-based containerization for fleet deployment
- **Framerate:** 15 FPS (Optimized for thermal and bandwidth efficiency)

## Prerequisites
The following must be installed and configured on the host Raspberry Pi:
1. **Tailscale:** For secure, private mesh networking.
2. **Docker & Docker Compose:** To manage the containerized ingest service.

## Setup and Deployment

### 1. Clone the Repository
```bash
git clone [https://github.com/ScoRoss/piforgit.git](https://github.com/ScoRoss/piforgit.git)
cd piforgit
