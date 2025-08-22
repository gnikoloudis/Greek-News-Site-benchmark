import urllib3
from urllib3.exceptions import ReadTimeoutError
import ast
import networkx as nx
import pandas as pd
import os
import pandas as pd
import re
from selenium import webdriver
from selenium.webdriver.common.by import By
from fake_useragent import UserAgent
import json
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from urllib.parse import urlparse
from bs4 import BeautifulSoup
from selenium.common.exceptions import TimeoutException
from selenium.common.exceptions import WebDriverException


ua = UserAgent()

def get_chrome_options():
    options = webdriver.ChromeOptions()
    options.add_argument("--no-sandbox")
    options.add_argument("--enable-unsafe-swiftshader")
    #options.add_argument("--headless=new")  # Run in headless mode (no GUI)
    options.add_argument('--disable-gpu')  # Disable GPU (recommended for headless)
    options.add_argument('--no-sandbox')  # Bypass OS security model (required for some environments)
    options.add_argument('--disable-dev-shm-usage')  # Overcome limited resource problems
    options.add_argument('--disable-blink-features=AutomationControlled')  # Reduces bot detection
    options.add_argument(f'user-agent={ua.chrome}')  # Set custom User-Agent if needed
    return options

def log_to_file(log_path):
    service = webdriver.ChromeService(log_output=log_path)

    driver = webdriver.Chrome(service=service)

    with open(log_path, 'r') as fp:
        assert "Starting ChromeDriver" in fp.readline()

# see rkengler.com for related blog post
# https://www.rkengler.com/how-to-capture-network-traffic-when-scraping-with-selenium-and-python/

capabilities = DesiredCapabilities.CHROME
# capabilities["loggingPrefs"] = {"performance": "ALL"}  # chromedriver < ~75
capabilities["goog:loggingPrefs"] = {"performance": "ALL"}  # chromedriver 75+


def process_browser_logs_for_network_events(logs):
    """
    Return only logs which have a method that start with "Network.response", "Network.request", or "Network.webSocket"
    since we're interested in the network events specifically.
    """
    for entry in logs:
        log = json.loads(entry["message"])["message"]
        if (
                "Network.response" in log["method"]
                or "Network.request" in log["method"]
                or "Network.webSocket" in log["method"]
        ):
            yield log

def get_track_ids_from_events(log_event):

    scripts = []

    log_entry = json.dumps(log_event)

    loaded_log_entry = json.loads(log_entry)

    # Example: Extract URLs of loaded JS scripts from the network requests audit
    network_audit = loaded_log_entry.get('audits', {}).get('network-requests', {}).get('details', {})
    if 'items' in network_audit:
        for item in network_audit['items']:
            url = item.get('url', '')
            if url.endswith('.js'):
                scripts.append(url)

    # Example pattern search in URLs
    adsense_ids = set()
    ga_ua_ids = set()
    ga_g_ids = set()
    fa_pixel_ids=set()
    gtm_ids=set()

    adsense_pattern = re.compile(r'pub-\d{16}')
    ga_ua_pattern = re.compile(r'UA-\d{4,10}-\d{1,4}')
    ga_g_pattern = re.compile(r'G-[A-Z0-9]{8,15}')
    fa_pixel = re.compile(r"fbq\('init',\s*'(\d{15,16})'\)")
    gtm = re.compile(r'GTM-[A-Z0-9]+')

    
    for script_url in scripts:
        if adsense_pattern.search(script_url):
            adsense_ids.append(script_url)
        if ga_ua_pattern.search(script_url):
            ga_ua_ids.append(script_url)
        if ga_g_pattern.search(script_url):
            ga_g_ids.append(script_url)
        if fa_pixel.search(script_url):
            fa_pixel_ids.append(script_url)
        if gtm.search(script_url):
            gtm_ids.append(script_url)
    
    return {
        'adsense_ids': list(adsense_ids),
        'google_analytics_ua': list(ga_ua_ids),
        'google_analytics_ga4':list(ga_g_ids),
        "facebook_pixel":list(fa_pixel_ids),
        "gtm_ids":list(gtm_ids)
    }

def scrape_tracking_and_referrals(html):
    
    soup = BeautifulSoup(html, 'html.parser')

    # Extract tracking codes using regex patterns
    tracking_codes = {
        'adsense_ids': set(re.findall(r'pub-\d{16}', html)),
        'google_analytics_ua': set(re.findall(r'UA-\d{4,10}-\d{1,4}', html)),
        'google_analytics_ga4': set(re.findall(r'G-[A-Z0-9]{8,15}', html)),
        'facebook_pixel': set(re.findall(r"fbq\('init',\s*'(\d{15,16})'\)", html)),
        'gtm_ids': set(re.findall(r'GTM-[A-Z0-9]+', html)),
    }

    # Get the domain of the current page to filter outbound links
    current_domain = urlparse(url).netloc

    # Extract all outbound referral links
    referral_links = set()
    for link in soup.find_all('a', href=True):
        href = link['href']
        parsed_href = urlparse(href)
        
        # Only consider absolute URLs
        if parsed_href.scheme in ['http', 'https']:
            domain = parsed_href.netloc
            
            # If domain is different, it is a referral link
            if domain and domain != current_domain:
                referral_links.add(href)

    return {
        'tracking_codes': {k: list(v) for k, v in tracking_codes.items()},
        'referral_links': list(referral_links),
    }


social_domains = [
    'instagram.com','facebook.com','linkedin.com','twitter.com',
    'youtube.com','bsky.app',"google.com","tiktok.com",
    "apple.com","spotify.com"'mozilla.org', 'huawei.com', 'significadigital.com','microsoft.com','x.com','wa.me','gov.gr', 'auth.gr','youtu.be', 'flickr.com','goo.gl'
]


LOG_DIR = "logs/greek_news_sites"

urls_greek =[
    # TV News Channels
    "ert.gr",
    "alphatv.gr",
    "ant1news.gr",
    "megatv.com",
    "skai.gr",
    "star.gr",
    "mad.tv",
    "onechannel.gr",
    "maktv.gr",
    "tvopen.gr",

    # Major Greek News Websites / Online Newspapers  
    "protothema.gr",
    "newsit.gr",
    "news247.gr",
    "pronews.gr",
    "efsyn.gr",
    "kathimerini.gr",
    "ekathimerini.com",
    "in.gr",
    "gazzetta.gr",
    "iefimerida.gr",
    "newsbomb.gr",
    "enikos.gr",
    "naftemporiki.gr",
    "avgi.gr",
    "parapolitika.gr",
    "inews.gr",
    "cretalive.gr",
    "newpost.gr",
    "newsbomb.gr",
    "newsbeat.gr",
    "flashnews.gr",
    "dnews.gr",
    "lifo.gr",
    "e-thessalia.gr",
    "makedonia.gr",
    "zougla.gr",
    "taxydromos.gr",
    "protagon.gr",
    "hotdoc.gr",
    "katohika.gr",
    "metrosport.gr",
    "athinorama.gr",
    "athensvoice.gr",

    # Newspapers and Weeklies
    "tanea.gr",
    "tovima.gr",
    "ethnos.gr",
    "et.gr",
    "eleftherostypos.gr",
    "protothema.gr",
    "avgi.gr",
    "pentapostagma.gr",
    "makeleio.gr",
    "lamiareport.gr",
    "rizospastis.gr",
    "prin.gr",
    "express.gr",
    "espresso.gr",
    "sport-fm.gr",
    "novasports.gr",
    "neakriti.gr",
    "patris.gr",
    "koutipandoras.gr",
    "dikaiologitika.gr",
    "thetoc.gr",
    "thepressproject.gr",
    "documentonews.gr",
        
    # Regional News Sites
    "achaeanews.gr",
    "trikalavoice.gr",
    "magnesia.news",
    "kriti24.gr",
    "rodosreport.gr",
    "xanthi2.gr",
    "dramanews.gr",
    "eviathema.gr",
    "kefalonianews.gr",

    # Magazines and Journals (online presences)
    "avopolis.gr",
    "lifo.gr",
    "zoornalistas.com",
    "esquire.com.gr",
    "focusgreece.gr",
    "madamefigaro.gr",
    "clickatlife.gr",
    "cosmopoliti.com",
    "oilive.gr",
    "digitallife.gr",
    "zappit.gr",
    "queen.gr",
    "gossip-tv.gr",
    "gynaikamagazine.gr",
    "tlife.gr",
    "bovary.gr",
    "beautetinkyriaki.gr",

    # blogs and independent news sites
    "thepressproject.gr",
    "documentonews.gr", 
    "koutipandoras.gr",
    "zoornalistas.com",
    "protagon.gr",
    "athensvoice.gr",
    "thetoc.gr",
    "news247.gr",
    "newsbeast.gr",
    "newsit.gr",
    "enikos.gr",
    "newsbomb.gr",
    "iefimerida.gr",
    "news.gr",

]

case = "greek_news_sites"
tracker_file = f"{case}.pckl"

if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

options = get_chrome_options()

driver = webdriver.Chrome(options=options)

info_list =[]

for url in urls_greek:

    try:
       
        info = []
        
        log_list=[]

        root_domain =url
        
        filedir = f"{LOG_DIR}/{root_domain}"

        filename = f"{filedir}/{root_domain}_log_entries.log"

        print("Processing:",url)

        if not url.startswith("http"):
            url = "https://"+url

        driver.maximize_window()

        driver.set_page_load_timeout(60)

        driver.get(url)

        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

        driver.save_screenshot(f"{filedir}/{root_domain}_screenshot.png")
        
        html = driver.page_source

        logs = driver.get_log("performance")
        
        events = process_browser_logs_for_network_events(logs)
        
        if not os.path.exists(filedir):
            os.makedirs(filedir)

        for event in events:
        
            event_data = get_track_ids_from_events(event)

            if event_data and any(event_data.values()):
                info.append(event_data)
            
            log_list.append(event)

        df = pd.DataFrame(log_list).to_json(filename)

        df_info = pd.DataFrame(info)

        df_info["root_domain"]  = root_domain

        info_list.append(df_info)
    
    except TimeoutException:
    
        print(f"Timeout loading {url}, skipping...")
    
        continue
    
    except WebDriverException as e:
    
        if 'net::ERR_NAME_NOT_RESOLVED' in str(e):
    
            print(f"DNS resolution failed for {url}, skipping...")
    
            continue
        
        elif 'net::ERR_CONNECTION' in str(e):
    
            print(f"DNS resolution failed for {url}, skipping...")
    
            continue
        elif 'ERR_INTERNET_DISCONNECTED' in str(e):
    
            print(f"Internet disconnected, stopping...")
    
            break

        elif 'ERR_CONNECTION_RESET' in str(e):

            print(f"Connection reset for {url}, skipping...")

            continue

        elif 'SSL' or 'certificate' in str(e):
        
            print(f"SSL error for {url}, skipping...")

            continue

        elif 'timeout' in str(e).lower():
        
            print(f"{url}, timeout...")

            continue

        else:
            raise
    
    except ReadTimeoutError:
        
        print(f"{url}Request timed out. Continuing without stopping the process.")
        
        continue
    

df_info_all = pd.concat(info_list)

driver.quit()
