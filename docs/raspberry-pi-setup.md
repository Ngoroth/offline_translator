# Raspberry Pi Setup Guide

This guide covers setting up a Raspberry Pi 4 for the Offline Translator project.

## Hardware Requirements

| Component | Specification |
|-----------|---------------|
| Raspberry Pi 4 | 2GB+ RAM (4GB recommended) |
| USB Flash Drive | 64GB+ (for OS + models) |
| Power Supply | Official 5V/3A adapter |
| USB Microphone | Any USB mic, 16kHz capable |
| Speakers | 3.5mm jack + USB powered |
| USB Numpad | For PTT (Push-to-Talk) |
| Ethernet cable | Optional, simplifies initial setup |

## Step 1: Flash Raspberry Pi OS

### On Windows:

1. Download and install [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert USB flash drive (64GB+)
3. Launch Imager and configure:
   - **OS:** Raspberry Pi OS Lite (64-bit)
   - **Storage:** Your USB flash drive
   - **Settings (gear icon):**
     - Hostname: `translator`
     - Enable SSH: Yes, public-key authentication only
     - Paste your public key from `~/.ssh/id_ed25519.pub`
     - Configure WiFi (optional, Ethernet recommended for setup)
     - Set locale/timezone
     - Raspberry Pi Connect: **Disable** (not needed)
4. Click **Write** and wait for completion

### Generate SSH Key (if needed):

```powershell
# On Windows PowerShell
ssh-keygen -t ed25519 -C "your-email@example.com"
cat ~/.ssh/id_ed25519.pub
# Copy the output to Raspberry Pi Imager settings
```

## Step 2: First Boot

1. Insert USB flash drive into **blue USB 3.0 port** on Pi
2. Connect Ethernet cable (recommended for initial setup)
3. Connect power supply **last**
4. Wait 60-90 seconds for first boot (filesystem resize occurs)

### LED Status:

| LED | Expected Behavior |
|-----|-------------------|
| Red (PWR) | Solid on |
| Green (ACT) | Blinking during boot |

## Step 3: SSH Connection

From your development machine:

```bash
ssh pi@translator.local
```

If hostname doesn't resolve, find IP in your router and connect directly:
```bash
ssh pi@<IP_ADDRESS>
```

## Step 4: System Update

```bash
sudo apt update && sudo DEBIAN_FRONTEND=noninteractive apt upgrade -y
```

This may take 5-10 minutes on first run.

## Step 5: Install Required Packages

```bash
sudo apt install -y \
    git \
    portaudio19-dev \
    libsndfile1 \
    alsa-utils \
    evtest
```

## Step 6: Install uv (Python Package Manager)

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
source ~/.local/bin/env
```

Verify installation:
```bash
uv --version
```

## Step 7: Configure Swap (Important for 2GB Pi)

Models require significant memory. Configure 4GB swap:

```bash
# Disable existing swap
sudo swapoff -a

# Create 4GB swapfile
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
free -h
```

Expected output should show `Swap: 4.0Gi`.

## Step 8: Audio Configuration

### Connect Hardware:
- USB Microphone: Any USB port
- Speakers: 3.5mm jack for audio, USB for power

### Test Audio Devices:

```bash
# List recording devices
arecord -l

# List playback devices  
aplay -l

# Test recording (speak for 3 seconds)
# Note: Card number may vary - check arecord -l output
arecord -D plughw:3,0 -f S16_LE -r 16000 -d 3 test.wav

# Test playback on 3.5mm jack (card 2)
aplay -D plughw:2,0 test.wav

# Set volume to max if too quiet
amixer -c 2 set PCM 100%
```

### If speakers don't work (3.5mm jack):

```bash
sudo raspi-config
# Navigate: System Options -> Audio -> Force 3.5mm jack
```

## Step 9: Numpad Configuration

```bash
# Find input device
ls /dev/input/

# Test numpad (press keys, see events)
evtest
# Select your numpad from the list
```

## Step 10: Clone Project

```bash
cd ~
git clone <repository-url> offline_translator
cd offline_translator
```

## Step 11: Install Python Dependencies

```bash
uv sync
```

## Step 12: Download Models

```bash
uv run python scripts/download_models.py
```

This downloads ~4-6GB of AI models. Takes 10-30 minutes depending on connection.

## Step 13: Configure Application

Edit `config.yaml` to match your Pi's audio devices:

```bash
nano config.yaml
```

Key settings to verify:
- Audio input device index
- Audio output device  
- Model paths

## Step 14: First Run

```bash
uv run python src/app/main.py
```

## Troubleshooting

### Pi doesn't boot from USB
- Ensure USB is in **blue USB 3.0 port**
- Pi 4 units from 2020+ support USB boot by default
- Older units may need EEPROM update (requires working SD card)

### SSH connection refused
- Wait longer (first boot takes 60-90 seconds)
- Check Ethernet/WiFi connection
- Verify Pi and dev machine are on same network

### Audio not working
- Check `arecord -l` and `aplay -l` for device indices
- Force 3.5mm output via `raspi-config`
- Ensure USB-powered speakers have USB connected

### Out of memory errors
- Verify swap is active: `free -h`
- Consider using smaller models (whisper-tiny instead of whisper-small)
- Close unnecessary processes

### Numpad not detected
- Check `lsusb` for device
- Try different USB port
- Check `/dev/input/` for event devices

## Memory Considerations

| Pi RAM | Recommendation |
|--------|----------------|
| 2GB | Works, uses swap heavily. Use smaller models. |
| 4GB | Recommended. Comfortable for all models. |
| 8GB | Ideal. Room for future expansion. |

## Verified Hardware Configuration

The following hardware was tested and confirmed working:

| Component | Model | USB ID | Device Path |
|-----------|-------|--------|-------------|
| USB Flash Drive | Samsung Flash Drive FIT 64GB | `04e8:6300` | USB 3.0 port (blue) |
| USB Microphone | Texas Instruments PCM2902 | `08bb:2902` | `plughw:3,0` |
| Speakers | 3.5mm jack + USB power | N/A | `plughw:2,0` (card 2) |
| USB Numpad | SiGma Micro TRACER Gamma Ivory | `1c4f:0002` | `/dev/input/event1` |

### Audio Device Mapping

After connecting devices, verify with:

```bash
arecord -l  # Find microphone card number
aplay -l    # Find speaker card number
```

Typical output:
```
Recording: card 3: Device [USB PnP Sound Device]
Playback:  card 2: Headphones [bcm2835 Headphones] (3.5mm jack)
```

### Numpad Device Identification

```bash
cat /proc/bus/input/devices | grep -A 4 -i keyboard
```

Look for `Handlers=... event1` (or similar event number).

Test with:
```bash
evtest /dev/input/event1
# Press numpad keys - should see EV_KEY events like KEY_KP5, KEY_KPENTER, etc.
```

## Quick Reference Commands

```bash
# SSH into Pi
ssh pi@translator.local

# Check memory
free -h

# Check disk space
df -h

# List USB devices
lsusb

# Test audio recording (speak for 3 seconds)
arecord -D plughw:3,0 -f S16_LE -r 16000 -d 3 test.wav

# Test audio playback
aplay -D plughw:2,0 test.wav

# Set speaker volume to max
amixer -c 2 set PCM 100%

# Test numpad
evtest /dev/input/event1

# Run translator
cd ~/offline_translator && uv run python src/app/main.py
```

## Notes from Setup Session

1. **Pi 4 with 2GB RAM** works but relies heavily on swap. 4GB swap is configured.

2. **Raspberry Pi Connect** should be disabled - not needed for offline translator.

3. **SSH with keys** is recommended over password authentication.

4. **Card numbers may vary** depending on USB port order. Always verify with `arecord -l` and `aplay -l`.

5. **SD card does not add RAM** - it's storage only. To get more RAM, need different Pi model (4GB or 8GB).

6. **Swap on USB flash drive** is acceptable. USB 3.0 is faster than SD card (~100MB/s vs ~25MB/s).
