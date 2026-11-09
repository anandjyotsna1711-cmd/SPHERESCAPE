
import requests
import xml.etree.ElementTree as ET
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

url = "https://nasa-irsa-spherex.s3.us-east-1.amazonaws.com/"

session = requests.Session()

retries = Retry(
    total=5,
    backoff_factor=2,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)

session.mount("https://", HTTPAdapter(max_retries=retries))

params = {
    "list-type": "2",
    "prefix": "qr2/spectral_wcs/"
}

namespace = {"s3": "http://s3.amazonaws.com/doc/2006-03-01/"}

print("Searching only the Spectral WCS directory...\n")

while True:
    response = session.get(url, params=params, timeout=(20, 120))
    response.raise_for_status()

    root = ET.fromstring(response.content)

    for item in root.findall("s3:Contents", namespace):
        key = item.find("s3:Key", namespace).text
        size = int(item.find("s3:Size", namespace).text)

        print(f"{key}  |  {size / (1024 * 1024):.2f} MB")

    truncated = root.find("s3:IsTruncated", namespace).text == "true"

    if not truncated:
        break

    token = root.find("s3:NextContinuationToken", namespace).text
    params["continuation-token"] = token

print("\nSearch complete.")
