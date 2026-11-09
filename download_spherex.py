
import os
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor

URL = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/qr2/level2/2026W20_2A/l2b-v25-2026-140/2/level2_2026W20_2A_0191_4D2_spx_l2b-v25-2026-140.fits"

OUTPUT = "data/raw/spherex_observation_may2026.fits"
TEMP = "data/raw/spherex_chunks"

TOTAL_SIZE = 71637120
CHUNKS = 8
WORKERS = 4

os.makedirs(TEMP, exist_ok=True)

def download_chunk(i):
    start = i * (TOTAL_SIZE // CHUNKS)
    end = min((i + 1) * (TOTAL_SIZE // CHUNKS) - 1, TOTAL_SIZE - 1)

    expected = end - start + 1
    path = os.path.join(TEMP, f"chunk_{i}.part")

    if os.path.exists(path) and os.path.getsize(path) == expected:
        print(f"Chunk {i + 1} already complete")
        return

    for attempt in range(5):
        try:
            request = urllib.request.Request(
                URL,
                headers={
                    "Range": f"bytes={start}-{end}",
                    "User-Agent": "Mozilla/5.0"
                }
            )

            with urllib.request.urlopen(request, timeout=90) as response:

                if response.status != 206:
                    raise Exception("Server did not honor range request")

                content_range = response.headers.get("Content-Range", "")

                if not content_range.startswith(f"bytes {start}-{end}/"):
                    raise Exception("Incorrect content range")

                downloaded = 0

                with open(path + ".tmp", "wb") as f:
                    while True:
                        data = response.read(1024 * 1024)
                        if not data:
                            break
                        f.write(data)
                        downloaded += len(data)

                if downloaded != expected:
                    raise Exception("Incomplete chunk")

                os.replace(path + ".tmp", path)

            print(f"Chunk {i + 1}/{CHUNKS} completed")
            return

        except Exception as e:
            if os.path.exists(path + ".tmp"):
                os.remove(path + ".tmp")

            print(f"Chunk {i + 1}, attempt {attempt + 1}: {e}")
            time.sleep(3)

    raise Exception(f"Chunk {i + 1} failed after 5 attempts")


print("Starting parallel SPHEREx download...")

with ThreadPoolExecutor(max_workers=WORKERS) as executor:
    list(executor.map(download_chunk, range(CHUNKS)))

print("\nAll chunks downloaded. Combining...")

temp_output = OUTPUT + ".tmp"

with open(temp_output, "wb") as final_file:
    for i in range(CHUNKS):
        path = os.path.join(TEMP, f"chunk_{i}.part")

        with open(path, "rb") as part:
            while True:
                data = part.read(1024 * 1024)
                if not data:
                    break
                final_file.write(data)

if os.path.getsize(temp_output) != TOTAL_SIZE:
    os.remove(temp_output)
    raise Exception("Final file size verification failed!")

os.replace(temp_output, OUTPUT)

print("\nSUCCESS! SPHEREx FITS file downloaded.")
print("Final size:", os.path.getsize(OUTPUT), "bytes")
