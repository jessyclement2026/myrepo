import os
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
    full_logo_url = f"{BASE_URL}{logo_base}.png"
    
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        
        state = {"found_link": None}

        # Custom inline handler to catch tokenless paths
        def check_network(request):
            url = request.url
            if ".m3u8" in url and "tvcdnpotok.com" in url:
                # FIXED: Added [0] to extract the clean URL string value out of the split array
                clean_path = url.split("?")[0]
                state["found_link"] = clean_path

        page.on("request", check_network)

        try:
            print(f"[START] Processing: {display_name}")
            page.goto(full_url, timeout=20000)
            page.wait_for_timeout(4000)
            
            if state["found_link"]:
                print(f"[SUCCESS] Found clean link for {display_name}")
                entry = (
                    f'#EXTINF:-1 tvg-id="" tvg-name="{display_name}" tvg-language="English" '
                    f'tvg-logo="{full_logo_url}" group-title="XXX",{display_name}\n{state["found_link"]}'
                )
                return entry
            else:
                print(f"[FAILED] No stream link matched for {display_name}")
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

    print(f"\nFinished! Compiled {len(playlist_entries)} clean paths inside playlist.m3u.")

if __name__ == "__main__":
    main()
