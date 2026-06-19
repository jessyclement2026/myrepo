import os
import re
import urllib.parse
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

BASE_URL = "https://hotelki.tv/"

# Do NOT include a trailing slash (/) at the end
CLOUDFLARE_WORKER_URL = "https://iptv.jessyclement2026.workers.dev"

pages = [
    "hustler-hd.html", "private-tv.html", "brazzers-tv-europe.html", "babes-tv.html",
    "erox.html", "eroxxx.html", "superone.html", "shalun.html", "blue-hustler.html",
    "xxl.html", "kinoxxx.html", "oh-ah-hd.html", "dorcel-tv.html", "redlight-hd.html",
    "vivid-red.html", "penthouse-gold.html", "penthouse-reality-tv.html",
    "barely-legal.html", "extasy-tv.html", "red-lips.html", "pinko-tv.html",
    "cineman-exexex.html", "cineman-exexex-two.html", "xy-plus.html",
    "frenchlover-tv.html", "kino-18-international.html", "fap-tv-anal.html",
    "fap-tv-bbw.html", "fap-tv-compilation.html", "fap-tv-lesbian.html",
    "fap-tv-parody.html", "fap-tv-teens.html", "fap-tv-2.html", "fap-tv-3.html", "fap-tv-4.html"
]

def format_title(raw_filename):
    """Converts 'hustler-hd.html' to 'Hustler HD'"""
    # FIXED: Added [0] index accessor to capture the pure text base name string from the tuple array
    base_name = os.path.splitext(raw_filename)[0]
    clean_name = base_name.replace("-", " ").title()
    replacements = {" Hd": " HD", " Tv": " TV", " Xxl": " XXL", " Xy": " XY"}
    for search, replace in replacements.items():
        if clean_name.endswith(search) or search + " " in clean_name:
            clean_name = clean_name.replace(search, replace)
    return clean_name

def fetch_stream_link(item):
    """Worker function executed by each thread to fetch a single stream link."""
    full_url = f"{BASE_URL}{item}"
    display_name = format_title(item)
    # FIXED: Added [0] index accessor to prevent tuple errors inside the logo path construction
    logo_base = os.path.splitext(item)[0] 
    full_logo_url = f"{BASE_URL}images/{logo_base}.png"
    
    MAX_ATTEMPTS = 3
    
    for attempt in range(1, MAX_ATTEMPTS + 1):
        with sync_playwright() as p:
            # Mask automation footprints on browser initialization level
            browser = p.firefox.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled", "--no-sandbox"]
            )
            context = browser.new_context(
                viewport={"width": 1920, "height": 1080},
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
            )
            page = context.new_page()
            state = {"found_link": None}

            # ROUTING TUNNEL: Catches internal script player calls and forces them through Cloudflare
            def handle_route(route):
                request_url = route.request.url
                if "tvcdnpotok.com" in request_url:
                    # Encodes the original stream URL and ships it to our Worker endpoint
                    encoded_url = urllib.parse.quote(request_url, safe='')
                    proxied_url = f"{CLOUDFLARE_WORKER_URL}/fetch-tunnel?url={encoded_url}"
                    route.continue_(url=proxied_url)
                else:
                    route.continue_()

            page.route("**/*", handle_route)

            def check_network(request):
                url = request.url
                if "tvcdnpotok.com" in url and ".m3u8" in url:
                    clean_url = url.split("?")[0]
                    if clean_url.count("/") >= 6:
                        state["found_link"] = clean_url
                        print(f"[FOUND CLOUD LINK] {display_name} -> {clean_url}")

            page.on("request", check_network)

            try:
                print(f"[START] Processing: {display_name} (Attempt {attempt}/{MAX_ATTEMPTS})")
                page.goto(f"{full_url}?t={int(time.time())}", timeout=20000)
                
                # Simulate page click interaction layer to trigger player media script handshakes
                page.mouse.click(960, 540)
                page.wait_for_timeout(6000) 
                
                if state["found_link"]:
                    entry = (
                        f'#EXTINF:-1 tvg-id="" tvg-name="{display_name}" tvg-language="English" '
                        f'tvg-logo="{full_logo_url}" group-title="XXX",{display_name}\n'
                        f'{state["found_link"]}'
                    )
                    return entry
                else:
                    print(f"[FAILED] Attempt {attempt} failed for {display_name}")
            except Exception as e:
                print(f"[ERROR] Attempt {attempt} threw an exception on {display_name}: {e}")
            finally:
                context.close()
                browser.close()
                
    return None

def main():
    playlist_entries = []
    # Keeps max workers stable to prevent virtual allocation drops
    MAX_WORKERS = 5 
    print(f"Starting execution with {MAX_WORKERS} workers tunneling via Cloudflare...")
    
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(fetch_stream_link, item): item for item in pages}
        for future in as_completed(futures):
            result = future.result()
            if result:
                playlist_entries.append(result)

    with open("playlist.m3u", "w", encoding="utf-8") as f:
        f.write("#EXTM3U\n")
        f.write("\n".join(playlist_entries))
        
    print(f"\nFinished! Compiled {len(playlist_entries)} Cloudflare-bound links inside playlist.m3u.")

if __name__ == "__main__":
    main()
