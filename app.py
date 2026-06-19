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
    # 1. Strip the extension (.html) and grab the string at index 0
    base_name = os.path.splitext(raw_filename)[0]
    
    # 2. Replace hyphens with spaces and capitalize each separate word
    clean_name = base_name.replace("-", " ").title()
    
    # 3. Clean up common acronyms to keep them fully uppercase
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
    
    # 1. Beautiful uppercase text for names
    display_name = format_title(item)
    
    # 2. Clean lowercase string with dashes (e.g., 'hustler-hd')
    logo_base = os.path.splitext(item)[0] 
    
    # 3. Form the absolute URL for the logo pointing to the .png asset
    full_logo_url = f"{BASE_URL}images/{logo_base}.png"
    
    # Each thread needs its own Playwright context manager
    with sync_playwright() as p:
        browser = p.firefox.launch(headless=True)
        page = browser.new_page()
        
        state = {"found_link": None}

        # Inline handler targeting the required m3u8 token structure
        def check_network(request):
            url = request.url
            if ".m3u8" in url and "wmsAuthSign=" in url:
                state["found_link"] = url

        page.on("request", check_network)

        try:
            print(f"[START] Processing: {display_name}")
            page.goto(full_url, timeout=20000)
            page.wait_for_timeout(4000)  # Wait for player to load and request token
            
            if state["found_link"]:
                print(f"[SUCCESS] Found link for {display_name}")
                # Format block using display_name for text labels and full_logo_url for the logo path
                entry = (
                    f'#EXTINF:-1 tvg-id="" tvg-name="{display_name}" tvg-language="English" '
                    f'tvg-logo="{full_logo_url}" group-title="XXX",{display_name}\n{state["found_link"]}'
                )
                return entry
            else:
                print(f"[FAILED] No token link found for {display_name}")
                return None

        except Exception as e:
            print(f"[ERROR] Timeout or error on page {display_name}: {e}")
            return None
        finally:
            browser.close()

def main():
    playlist_entries = []
    
    # Max parallel browser instances running at the same time
    MAX_WORKERS = 5 
    
    print(f"Starting parallel execution with {MAX_WORKERS} workers...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all tasks to the thread pool
        futures = {executor.submit(fetch_stream_link, item): item for item in pages}
        
        # Collect results as they finish
        for future in as_completed(futures):
            result = future.result()
            if result:
                playlist_entries.append(result)

    # Save complete file block context
    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(playlist_entries))

    print(f"\nFinished! Compiled {len(playlist_entries)} links inside playlist.m3u.")

if __name__ == "__main__":
    main()
