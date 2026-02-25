"""
Run this once on the host to download Xray binary:
  python download_xray.py
"""
import requests
import zipfile
import os
import stat

XRAY_URL = "https://github.com/XTLS/Xray-core/releases/latest/download/Xray-linux-64.zip"
ZIP_FILE = "xray_tmp.zip"

print(f"Downloading Xray from: {XRAY_URL}")
response = requests.get(XRAY_URL, stream=True, timeout=120)
response.raise_for_status()

with open(ZIP_FILE, "wb") as f:
    for chunk in response.iter_content(chunk_size=8192):
        f.write(chunk)
print("Download complete.")

print("Extracting...")
with zipfile.ZipFile(ZIP_FILE, "r") as z:
    z.extractall(".")
print("Extraction complete.")

os.remove(ZIP_FILE)

xray_path = "./xray"
if os.path.exists(xray_path):
    os.chmod(xray_path, 0o755)
    print(f"✅ xray is ready at: {os.path.abspath(xray_path)}")
    # Verify it runs
    import subprocess
    result = subprocess.run([xray_path, "version"], capture_output=True, text=True, timeout=5)
    print(result.stdout or result.stderr)
else:
    print("❌ xray binary not found after extraction! Check the archive contents.")
