import requests
from pathlib import Path
import os

# Create assets directory if it doesn't exist
ASSETS_DIR = Path("assets/images")
ASSETS_DIR.mkdir(parents=True, exist_ok=True)

# Icon URLs (using high-quality icons from a free icon service)
ICONS = {
    "logo": "https://cdn-icons-png.flaticon.com/512/2097/2097743.png",
    "shopping": "https://cdn-icons-png.flaticon.com/512/3144/3144456.png",
    "cart": "https://cdn-icons-png.flaticon.com/512/3144/3144457.png",
    "tracking": "https://cdn-icons-png.flaticon.com/512/3144/3144458.png",
    "shipping": "https://cdn-icons-png.flaticon.com/512/3144/3144459.png",
    "product": "https://cdn-icons-png.flaticon.com/512/3144/3144460.png",
    "remove": "https://cdn-icons-png.flaticon.com/512/3144/3144461.png"
}

def download_icon(name, url):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            with open(ASSETS_DIR / f"{name}.png", "wb") as f:
                f.write(response.content)
            print(f"Downloaded {name}.png")
        else:
            print(f"Failed to download {name}.png")
    except Exception as e:
        print(f"Error downloading {name}.png: {str(e)}")

# Download all icons
for name, url in ICONS.items():
    download_icon(name, url)

print("All icons downloaded successfully!") 