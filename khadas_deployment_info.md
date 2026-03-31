
# Khadas Production Deployment Info

## Status: ✅ ONLINE

**Device IP**: `192.168.1.49`

### 🔗 Service Access
| Service | URL | Description |
| :--- | :--- | :--- |
| **Frontend (Local)** | [http://192.168.1.49:3000](http://192.168.1.49:3000) | Local network access |
| **Frontend (Public)** | [https://55aa-2401-4900-1c26-6ff5-4aeb-65bc-a202-67a0.ngrok-free.app](https://55aa-2401-4900-1c26-6ff5-4aeb-65bc-a202-67a0.ngrok-free.app) | Public ngrok tunnel |
| **Backend API** | [http://192.168.1.49:8000/docs](http://192.168.1.49:8000/docs) | Swagger Documentation |
| **Ollama API** | [http://192.168.1.49:11434](http://192.168.1.49:11434) | Local LLM Server |

### 📂 Storage Configuration
The application is configured to use the **External Drive** to preserve internal eMMC longevity.

- **Physical Drive**: `/dev/sda2` → Mounted at `/media/khadas/External1`
- **PDF Storage**: `/media/khadas/External1/PDFs/Arxiv Assistant`
- **Database Storage**: Uses a 10GB loopback image file to ensure compatibility.
  - Image: `/media/khadas/External1/postgres.img`
  - Mount Point: `/home/khadas/arxiv_assistant/postgres_mount`

### 🛠 Management Commands
**Login**: `ssh khadas@192.168.1.49` (Password: `khadas`)

**Restart App**:
```bash
cd ~/arxiv_assistant
docker compose restart
```

**Full Reset (if USB issues recur)**:
```bash
# 1. Stop Docker
sudo systemctl stop docker

# 2. Check Mounts
df -h

# 3. Reboot
sudo reboot
```
