import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from playwright.sync_api import sync_playwright

BASE_URL = "https://hotelki.tv"

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
    base_name = os.path.splitext(raw_filename)[0]
    clean_name = base_name.replace("-", " ").title()
    replacements = {" Hd": " HD", " Tv": " TV", " Xxl": " XXL", " Xy": " XY"}
    for search, replace in replacements.items():
        if clean_name.endswith(search) or search + " " in clean_name:
            clean_name = clean_name.replace(search, replace)
    return clean_name

def fetch_stream_link(item):
    full_url = f"{BASE_URL}{item}"
    display_name = format_title(item)
    logo_base = os.path.splitext(item)[0] 
    full_logo_url = f"{BASE_URL}images/{logo_base}.png"
    
    with sync_playwright() as p:
        # 1. Inject launch configurations to mask automation footprints
        browser = p.firefox.launch(
            headless=True,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox"
            ]
        )
        
        # 2. Assign high-definition structural geometry to mimic real desktop viewing
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0"
        )
        page = context.new_page()
        state = {"found_link": None}

        def check_network(request):
            url = request.url
            if "tvcdnpotok.com" in url and ".m3u8" in url:
                clean_url = url.split("?")[0]
                if clean_url.count("/") >= 6:
                    state["found_link"] = clean_url
                    print(f"[FOUND LINK NOW] {display_name} -> {clean_url}")

        page.on("request", check_network)

        try:
            print(f"[START] Processing: {display_name}")
            page.goto(full_url, timeout=25000)
            
            # 3. Simulate a physical user interaction directly on the central coordinate
            # to unlock playback engines that block automated media generation
            page.mouse.click(960, 540)
            
            page.wait_for_timeout(7000)  # Wait for player engine updates post-interaction
            
            if state["found_link"]:
                entry = (
                    f'#EXTINF:-1 tvg-id="" tvg-name="{display_name}" tvg-language="English" '
                    f'tvg-logo="{full_logo_url}" group-title="XXX",{display_name}\n'
                    f'#EXTVLCOPT:http-user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:133.0) Gecko/20100101 Firefox/133.0\n'
                    f'{state["found_link"]}'
                )
                return entry
            else:
                print(f"[FAILED] No complete stream link found for {display_name}")
                return None
        except Exception as e:
            print(f"[ERROR] Timeout/Error on page {display_name}: {e}")
            return None
        finally:
            context.close()
            browser.close()

def main():
    playlist_entries = []
    # Reduced threads down to 3 to prevent processing choke inside GitHub cloud allocations
    MAX_WORKERS = 3 
    
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

    print(f"\nFinished! Compiled {len(playlist_entries)} links.")

if __name__ == "__main__":
    main()
