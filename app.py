import os
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

# Defining the base URL structure
BASE_URL = "https://hotelki.tv/"

# Clean list containing only the target page names
pages = [
    "hustler-hd.html",
    "private-tv.html",
    "brazzers-tv-europe.html",
    "babes-tv.html",
    "erox.html",
    "eroxxx.html",
    "superone.html",
    "shalun.html",
    "blue-hustler.html",
    "xxl.html",
    "kinoxxx.html",
    "oh-ah-hd.html",
    "dorcel-tv.html",
    "redlight-hd.html",
    "vivid-red.html",
    "penthouse-gold.html",
    "penthouse-reality-tv.html",
    "barely-legal.html",
    "extasy-tv.html",
    "red-lips.html",
    "pinko-tv.html",
    "cineman-exexex.html",
    "cineman-exexex-two.html",
    "xy-plus.html",
    "frenchlover-tv.html",
    "kino-18-international.html",
    "fap-tv-anal.html",
    "fap-tv-bbw.html",
    "fap-tv-compilation.html",
    "fap-tv-lesbian.html",
    "fap-tv-parody.html",
    "fap-tv-teens.html",
    "fap-tv-2.html",
    "fap-tv-3.html",
    "fap-tv-4.html"
]

def format_title(raw_filename):
    """Converts 'hustler-hd.html' to 'Hustler HD'"""
    base_name = os.path.splitext(raw_filename)[0]
    clean_name = base_name.replace("-", " ").title()
    
    replacements = {
        " Hd": " HD",
        " Tv": " TV",
        " Xxl": " XXL",
        " Xy": " XY"
    }
    for search, replace in replacements.items():
        if clean_name.endswith(search) or search + " " in clean_name:
            clean_name = clean_name.replace(search, replace)
            
    return clean_name

def fetch_stream_link(item):
    """Worker function executed by each thread to fetch a single stream link."""
    full_url = f"{BASE_URL}{item}"
    display_name = format_title(item)
    logo_base = os.path.splitext(item)[0] 
    full_logo_url = f"{BASE_URL}images/{logo_base}.png"
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        
        state = {"found_link": None}

        # Custom inline handler to catch the exact full tokenized .m3u8 path
        def check_network(request):
            url = request.url
            if "tvcdnpotok.com" in url and ".m3u8" in url:
                # Regex extracts everything up to '.m3u8' dropping URL arguments
                match = re.search(r'(https://tvcdnpotok\.com/.*?\.m3u8)', url)
                if match:
                    clean_url = match.group(1)
                    
                    # VALIDATION: Check if this is the full token link. 
                    # The short broken link has 4 slashes: https: // tvcdnpotok.com / 46 / index.m3u8
                    # The full working link has 6 slashes: https: // tvcdnpotok.com / TOKEN / 46 / TIMESTAMP / index.m3u8
                    if clean_url.count("/") >= 6:
                        state["found_link"] = clean_url
                        print(f"[FOUND LINK NOW] {display_name} -> {clean_url}")

        page.on("request", check_network)

        try:
            print(f"[START] Processing: {display_name}")
            page.goto(full_url, timeout=20000)
            page.wait_for_timeout(5000)  # Slightly increased to give the stream player time to resolve tokens
            
            if state["found_link"]:
                entry = (
                    f'#EXTINF:-1 tvg-id="" tvg-name="{display_name}" tvg-language="English" '
                    f'tvg-logo="{full_logo_url}" group-title="XXX",{display_name}\n{state["found_link"]}'
                )
                return entry
            else:
                print(f"[FAILED] No complete stream link found for {display_name}")
                return None

        except Exception as e:
            print(f"[ERROR] Timeout or error on page {display_name}: {e}")
            return None
        finally:
            browser.close()

def main():
    playlist_entries = []
    MAX_WORKERS = 5 
    
    print(f"Starting parallel execution with {MAX_WORKERS} workers...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_stream_link, item): item for item in pages}
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                playlist_entries.append(result)

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(playlist_entries))

    print(f"\nFinished! Compiled {len(playlist_entries)} complete links inside playlist.m3u.")

if __name__ == "__main__":
    main()
