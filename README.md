# daily_capture

A Raspberry Pi camera automation system for capturing daily images and uploading them to an NFS share, with optional Logstash logging.

## Features

- Captures high-resolution images using the Raspberry Pi camera.
- Automatically uploads images to a configured NFS share.
- Systemd service and timer for scheduled (daily) operation.
- Structured logging with optional Logstash/GELF support.
- Easy deployment via Ansible.

## Directory Structure

```
camera-capture/
  main.yaml           # Ansible playbook for setup
  files/
    pipic.py          # Camera capture and upload script
    pipic.service     # systemd service unit
    pipic.timer       # systemd timer unit
```

## Setup

### 1. Requirements

- Raspberry Pi with camera module
- Python 3
- Ansible (for deployment)
- NFS server for image storage

### 2. Installation

1. **Clone this repository** on your Ansible control machine.

2. **Configure your inventory** to include your Raspberry Pi (host group: `pizero`).

3. **Set required variables** (e.g., `nas_ip`, `env`) in your inventory or via `--extra-vars`.

4. **Run the Ansible playbook:**

   ```sh
   ansible-playbook camera-capture/main.yaml -i <your_inventory>
   ```

### 3. What the Playbook Does

- Installs required system and Python packages.
- Mounts the NFS share at /mnt/nas.
- Deploys the camera capture script to /usr/local/bin/pipic.py.
- Installs and enables the systemd service and timer to run the script daily at noon.

### 4. Script Usage
The script can be run manually:
   ```sh
   python3 [pipic.py](http://_vscodecontentref_/4) --nfs --logstash-host <logstash_ip>
   ```

#### Options:
- --nfs : Copy captured image to NFS share.
- --keep : Keep the local image file after upload.
- --logstash-host : Send logs to this Logstash host (GELF UDP).
- --logstash-port : Logstash GELF UDP port (default: 12201).

### 5. Systemd Integration

- The timer (pipic.timer) triggers the service (pipic.service) daily at noon.
- Logs are available via journalctl -u pipic.service.