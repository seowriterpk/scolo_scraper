import streamlit as st
import requests
import re
import pandas as pd
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
import time
import random
from urllib.parse import urlparse

# ==========================================
# ⚙️ SYSTEM CONFIGURATION & PROXIES
# ==========================================
st.set_page_config(page_title="Scolo Pro Scraper", page_icon="⚡", layout="wide")

# -- YOUR PROXY CONFIGURATION (Hardcoded as requested) --
PROXY_HOST = "gw.dataimpulse.com"
PROXY_PORT = "823"
PROXY_USER = "866ce82505cfde9cb52e"
PROXY_PASS = "d8c998709832fdc0"

# Construct Proxy String
PROXY_URL = f"http://{PROXY_USER}:{PROXY_PASS}@{PROXY_HOST}:{PROXY_PORT}"
PROXIES = {"http": PROXY_URL, "https": PROXY_URL}




# ==========================================
# 🧠 CORE INTELLIGENCE ENGINE
# ==========================================

def get_proxied_session():
    """Creates a requests session optimized for residential proxies."""
    session = requests.Session()
    session.proxies = PROXIES
    ua = UserAgent()
    try:
        user_agent = ua.random
    except:
        user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    
    session.headers.update({
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Referer': 'https://www.google.com/'
    })
    return session

def google_search_proxied(query, num_results=10):
    """
    Performs a Google Search using Residential Proxies to bypass captchas.
    """
    session = get_proxied_session()
    search_url = "https://www.google.com/search"
    urls = []
    
    # Calculate pages needed (approx 10 results per page)
    pages = (num_results // 10) + 1
    
    for page in range(pages):
        params = {'q': query, 'start': page * 10}
        try:
            # Random delay to mimic human behavior
            time.sleep(random.uniform(1.5, 3.5))
            
            response = session.get(search_url, params=params, timeout=10)
            if response.status_code == 200:
                soup = BeautifulSoup(response.text, 'lxml')
                # Extract clean URLs from Google SERP
                for g in soup.find_all('div', class_='g'):
                    anchors = g.find_all('a')
                    if anchors:
                        link = anchors[0]['href']
                        if link.startswith('http') and 'google.com' not in link:
                            urls.append(link)
            else:
                pass # Fail silently on individual page errors
        except Exception:
            continue
            
    return list(set(urls))[:num_results]

def analyze_content(html, text, strict_mode=True):
    """Smart Filter: Returns True if content matches 'Girls/Women' criteria."""
    if not strict_mode: return True
    
    content_lower = (text + " " + str(html)).lower()
    
    if any(bad in content_lower for bad in BLACKLIST_KEYWORDS): return False
    if any(good in content_lower for good in STRICT_KEYWORDS): return True
    return False

def scrape_target_page(url, strict_mode):
    """Visits a page via Proxy and extracts WA links."""
    session = get_proxied_session()
    try:
        response = session.get(url, timeout=15)
        if response.status_code != 200: return []
        
        soup = BeautifulSoup(response.text, 'lxml')
        text_content = soup.get_text()
        
        if analyze_content(response.text, text_content, strict_mode):
            # Extract Links
            pattern = r'https:\/\/chat\.whatsapp\.com\/[A-Za-z0-9]{20,25}'
            links = list(set(re.findall(pattern, response.text)))
            return links, text_content[:200] # Return links and snippet
            
    except Exception:
        return [], ""
    return [], ""

# ==========================================
# 🖥️ UI LAYOUT & LOGIC
# ==========================================

# -- Sidebar Controls --
with st.sidebar:
    st.header("⚡ Scolo Controller")
    st.success(f"Residential Proxy Active\n{PROXY_HOST}")
    
    st.divider()
    
    scrape_speed = st.slider("🚀 Scraper Threads", 5, 50, 20, help="Higher = Faster, but heavier on proxy bandwidth.")
    strict_mode = st.toggle("🛡️ Strict 'Girls Only' Filter", value=True)
    
    st.divider()
    st.info("💡 **Tip:** Use specific queries like 'Ladies fashion group link' for best results.")

# -- Main Interface --
st.title("Scolo 10k: Production Validator Feed")
st.markdown("### The Fastest, Most Accurate WhatsApp Group Scraper")

# Tabs for Mode Selection
tab_search, tab_direct, tab_data = st.tabs(["🔍 Google Search Scraper", "🔗 Direct URL Scraper", "📂 Data Manager"])

# --- TAB 1: GOOGLE SEARCH ---
with tab_search:
    col_search, col_opts = st.columns([3, 1])
    with col_search:
        search_keywords = st.text_area("Enter Search Keywords (One per line)", 
            "site:facebook.com girls whatsapp group links\nladies fashion whatsapp group invite 2024\nwomen beauty tips group chat\nhijab style whatsapp group\ngirls study group whatsapp", height=150)
    with col_opts:
        results_per_kw = st.number_input("Pages per Keyword", 1, 50, 5)
        st.write("")
        st.write("")
        start_search_btn = st.button("🚀 Start Google Search", type="primary", use_container_width=True)

    if start_search_btn:
        st.session_state.scraped_data = [] # Reset
        
        queries = search_keywords.strip().split('\n')
        status_box = st.status("Initializing Residential Proxies...", expanded=True)
        
        # 1. Google Search Phase
        target_urls = []
        progress_bar = status_box.progress(0)
        
        for i, q in enumerate(queries):
            status_box.write(f"🔎 Googling via Proxy: '{q}'...")
            found = google_search_proxied(q, num_results=results_per_kw * 10)
            target_urls.extend(found)
            progress_bar.progress((i + 1) / len(queries))
        
        target_urls = list(set(target_urls))
        status_box.write(f"✅ Google Phase Done. Found {len(target_urls)} unique websites to scrape.")
        
        # 2. Scraping Phase
        status_box.write("⚡ Starting High-Speed Page Scraping...")
        
        valid_links = []
        processed_count = 0
        
        # UI Elements for live feed
        metric_col1, metric_col2, metric_col3 = st.columns(3)
        live_table = st.empty()
        
        with ThreadPoolExecutor(max_workers=scrape_speed) as executor:
            future_to_url = {executor.submit(scrape_target_page, url, strict_mode): url for url in target_urls}
            
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                processed_count += 1
                try:
                    links, snippet = future.result()
                    if links:
                        for link in links:
                            valid_links.append({
                                "Group Link": link,
                                "Source Website": url,
                                "Found At": time.strftime("%H:%M:%S")
                            })
                except:
                    pass
                
                # Live Updates
                metric_col1.metric("Websites Scanned", f"{processed_count}/{len(target_urls)}")
                metric_col2.metric("Groups Found", len(valid_links))
                metric_col3.metric("Proxy Status", "Active 🟢")
                
                if len(valid_links) > 0 and processed_count % 5 == 0:
                     live_table.dataframe(pd.DataFrame(valid_links).tail(5), use_container_width=True)

        st.session_state.scraped_data = valid_links
        status_box.update(label="✅ Task Complete!", state="complete", expanded=False)
        st.success(f"Extraction Finished! Found {len(valid_links)} groups. Go to 'Data Manager' tab to export.")

# --- TAB 2: DIRECT URL SCRAPING ---
with tab_direct:
    st.markdown("Paste direct URLs of websites (Facebook posts, blog articles, listicles) to scrape immediately.")
    direct_urls_input = st.text_area("Paste Website URLs (One per line)")
    start_direct_btn = st.button("⚡ Scrape Direct URLs", type="primary")
    
    if start_direct_btn:
        urls = direct_urls_input.strip().split('\n')
        st.session_state.scraped_data = []
        
        status_box_d = st.status("Processing Direct Links...", expanded=True)
        valid_links_d = []
        
        with ThreadPoolExecutor(max_workers=scrape_speed) as executor:
            future_to_url = {executor.submit(scrape_target_page, url, strict_mode): url for url in urls}
            for future in as_completed(future_to_url):
                url = future_to_url[future]
                links, snippet = future.result()
                if links:
                    for link in links:
                        valid_links_d.append({"Group Link": link, "Source Website": url, "Found At": time.strftime("%H:%M:%S")})
        
        st.session_state.scraped_data = valid_links_d
        status_box_d.update(label="✅ Direct Scrape Complete", state="complete")
        st.success(f"Found {len(valid_links_d)} links.")

# --- TAB 3: DATA MANAGER & EXPORT ---
with tab_data:
    if 'scraped_data' in st.session_state and st.session_state.scraped_data:
        df = pd.DataFrame(st.session_state.scraped_data)
        
        # Deduplication
        df = df.drop_duplicates(subset=['Group Link'])
        st.subheader(f"📂 Managed Results ({len(df)} Unique Groups)")
        
        # 1. Filter
        filter_text = st.text_input("🔍 Filter by URL text (e.g., type 'chat' or specific code)")
        if filter_text:
            df = df[df['Group Link'].str.contains(filter_text, case=False)]
            
        # 2. Selection
        st.markdown("Select rows to export (or Select All below)")
        # Add a 'Select' column for the data editor
        df.insert(0, "Select", True)
        
        edited_df = st.data_editor(
            df,
            hide_index=True,
            column_config={"Select": st.column_config.CheckboxColumn(required=True)},
            disabled=["Group Link", "Source Website", "Found At"],
            use_container_width=True
        )
        
        # Get selected rows
        selected_rows = edited_df[edited_df.Select]
        
        st.divider()
        col_ex1, col_ex2 = st.columns(2)
        
        # CSV Export
        csv = selected_rows.drop(columns=['Select']).to_csv(index=False).encode('utf-8')
        col_ex1.download_button(
            "📥 Download Selected CSV",
            csv,
            "scolo_groups_pro.csv",
            "text/csv",
            type="primary"
        )
        
        # JSON Export for PHP
        json_data = selected_rows['Group Link'].to_json(orient='records')
        col_ex2.download_button(
            "📥 Download JSON (For PHP Validator)",
            json_data,
            "scolo_groups_pro.json",
            "application/json"
        )
        
    else:
        st.info("No data scraped yet. Use the Search or Direct tabs to begin.")
