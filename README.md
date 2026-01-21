# Ant Esports GM320 – Linux Experimental Utility

⚠️ **UNDER DEVELOPMENT / EXPERIMENTAL PROJECT** ⚠️

This repository contains an **experimental Linux userspace utility** for the  
**Ant Esports GM320 Optical Gaming Mouse** (Instant Micro A825 chipset).

This project exists for **research and educational purposes only** and is
**NOT an official driver**.

This project does NOT provide any firmware flashing capability.
**Any files related to firmware are strictly for protocol research and observation.**

---

## 🖱️ About the Mouse

- Brand: Ant Esports
- Model: GM320 Optical Gaming Mouse
- Chipset: Instant Micro A825
- Sensor: PixArt PMW3325
- DPI: Up to 12800
- Profiles: Hardware-stored (DPI linked with RGB color)

---

## 🚧 Project Status

❌ **Not fully functional**  
❌ **Does NOT work with all firmware variants**  
❌ **No guarantee of compatibility**

Some GM320 firmware revisions:
- Expose a writable HID configuration interface
- Others operate in **hardware-only mode**
- Some report different USB Product IDs, causing official software rejection

This tool attempts to communicate using **HID Feature Reports**, but many devices
**ignore writes silently**.

---

## ⚠️ WARNING / DISCLAIMER

- This project is **NOT affiliated** with Ant Esports
- No proprietary firmware is included
- No reverse-engineered firmware is distributed
- **Flashing firmware can permanently brick your device**
- Use entirely **at your own risk**

If you do not understand USB HID protocols, **do not attempt firmware flashing**.

---

## ✨ Intended Features

- DPI selection
- Polling rate selection
- RGB mode & color selection
- Linux udev rule generation
- GUI using PySide6

⚠️ Feature availability depends entirely on firmware behavior.

---

## 🧪 Known Limitations

- Cannot change USB VID/PID
- Cannot unlock firmware-locked devices
- Cannot flash firmware safely
- Official Windows software may refuse devices with mismatched PID
- Some GM320 units permanently operate in standalone mode

---

## 📦 Project Structure

- Start.sh # Environment setup & launcher
- Ant_gm320_linux.py # Main GUI application
- protocol_research.py # Firmware-related research (DO NOT USE blindly)
- firm.sh # Experimental flashing script (DANGEROUS)
- LICENSE
- README.md

---

## 🐍 Dependencies

```bash
pip install hidapi PySide6
```
Linux requires access to /dev/hidraw*

## 🔐 udev Rules (Required)

```bash
sudo mv 99-gm320-mouse.rules /etc/udev/rules.d/
sudo udevadm control --reload-rules
sudo udevadm trigger
```
## 📜 Legal Notes

- Ant Esports is a registered trademark of its respective owner
- This software does not include proprietary code
- No firmware binaries are distributed
- Project provided AS IS
  


