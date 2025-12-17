import streamlit as st
import requests
import re
import pandas as pd
from duckduckgo_search import DDGS
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from fake_useragent import UserAgent
import time
import random

# --- CONFIGURATION ---
STRICT_KEYWORDS = ['girl', 'woman', 'women', 'lady', 'ladies', 'female', 'makeup', 'fashion', 'beauty', 'nurse', 'shopping', 'hijab', 'boutique', 'mom', 'aunt', 'wife']
BLACKLIST_KEYWORDS = ['porn', 'sex', 'xxx', 'adult', 'gambling', 'crypto', 'investment', 'hack', 'boy', 'men', 'male']

# --- SETUP SESSION STATE ---
if 'results' not in st.session_state:
    st.session_state.results = []
if 'scanned_count' not in st.session_state:
    st.session_state.scanned_count = 0

# --- CORE FUNCTIONS ---

def get_random_header():
    ua = UserAgent()
    # Fallback if UA fails (common in cloud envs)
    try:
        agent = ua.random
    except:
        agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        
    return {
        'User-Agent': agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }

def extract_whatsapp_links(html_content):
    """Regex extraction of chat.whatsapp.com links"""
    pattern = r'https:\/\/chat\.whatsapp\.com\/[A-Za-z0-9]{20,25}'
    try:
        return list(set(re.findall(pattern, html_content)))
    except:
        return []

def analyze_page_relevance(html, text, strict_mode=True):
    """
    Smart Intelligent Filter: 
    Returns True if the page content looks like it matches 'Girls/Women' context.
    """
    if not strict_mode:
        return True
    
    content_lower = (text + " " + html).lower()
    
    # Check Blacklist first (High Priority)
    if any(bad in content_lower for bad in BLACKLIST_KEYWORDS):
        return False
        
    # Check Whitelist
    if any(good in content_lower for good in STRICT_KEYWORDS):
        return True
        
    return False

def scrape_url(url, timeout=5):
    """Visits a single URL and extracts WA links if the page is relevant."""
    try:
        # Random delay to be polite and avoid blocking
        time.sleep(random.uniform(0.5, 1.5))
        
        response = requests.get(url, headers=get_random_header(), timeout=timeout)
        if response.status_code != 200:
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        page_text = soup.get_text()
        
        # Intelligent Check
        if analyze_page_relevance(response.text, page_text):
            links = extract_whatsapp_links(response.text)
            return links
    except:
        return []
    return []

# --- STREAMLIT APP UI ---

st.set_page_config(page_title="Scolo 10k Scraper", page_icon="🚀", layout="wide")

st.markdown("""
<style>
    .reportview-container { background: #0e1117; }
    h1 { color: #25D366; }
    .stButton>button { width: 100%; background-color: #25D366; color: white; border: none; font-weight: bold; }
    .stButton>button:hover { background-color: #128C7E; color: white; border: 1px solid white; }
    .metric-card { background-color: #1E1E1E; padding: 15px; border-radius: 10px; border: 1px solid #333; }
</style>
""", unsafe_allow_html=True)

st.title("🚀 Scolo Intelligent Scraper (Cloud Edition)")
st.caption("Auto-filters for 'Girls/Women' content only. Optimized for Streamlit Cloud.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("⚙️ Configuration")
    target_count = st.number_input("Target Links Needed", min_value=10, max_value=2000, value=500)
    
    # Lower concurrency for Cloud Free Tier to prevent crashes
    concurrency = st.slider("Speed (Threads)", 2, 20, 10, help="Higher is faster but may crash on free cloud servers.")
    
    strict_mode = st.checkbox("Strict 'Girls Only' Filter", value=True)
    
    st.markdown("### 🔍 Keywords")
    base_keywords = st.text_area("Search Queries (One per line)", 
                                 "girls whatsapp group links 2024\nladies fashion whatsapp group invite\nwomen shopping group chat\nmakeup tips whatsapp group link\nhijab style whatsapp group\nfemale only whatsapp group link\nmom club whatsapp group", height=200)

    start_btn = st.button("🚀 Start Extraction")

with col2:
    st.subheader("📊 Live Results")
    
    # Metrics
    m1, m2 = st.columns(2)
    metric_found = m1.empty()
    metric_scanned = m2.empty()
    
    # Progress
    status_text = st.empty()
    progress_bar = st.progress(0)
    
    # Table
    df_placeholder = st.empty()

if start_btn:
    st.session_state.results = [] # Reset results
    st.session_state.scanned_count = 0
    all_found_links = set()
    
    search_queries = base_keywords.strip().split('\n')
    status_text.info("🔍 Phase 1: searching the web for group lists...")
    
    # 1. Gather Search Results
    found_pages = []
    try:
        with DDGS() as ddgs:
            for query in search_queries:
                status_text.text(f"Searching: {query}...")
                # Fetching results
                results = list(ddgs.text(query, max_results=50))
                if results:
                    for r in results:
                        found_pages.append(r['href'])
                time.sleep(1) # Pause to avoid rate limits
    except Exception as e:
        st.error(f"Search Engine Error: {e}. Try reducing keyword count.")

    # Remove duplicates
    found_pages = list(set(found_pages))
    total_pages = len(found_pages)
    
    if total_pages == 0:
        st.warning("No sources found. Try different keywords.")
    else:
        status_text.success(f"Found {total_pages} sources. Starting Deep Scan...")
        
        # 2. Deep Scanning
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            future_to_url = {executor.submit(scrape_url, url): url for url in found_pages}
            
            for future in as_completed(future_to_url):
                st.session_state.scanned_count += 1
                url = future_to_url[future]
                
                try:
                    links = future.result()
                    if links:
                        for link in links:
                            if link not in all_found_links:
                                all_found_links.add(link)
                                st.session_state.results.append({"Group Link": link, "Source Page": url})
                except Exception:
                    pass
                
                # Update UI
                count_found = len(all_found_links)
                metric_found.metric("Links Found", count_found)
                metric_scanned.metric("Pages Scanned", f"{st.session_state.scanned_count}/{total_pages}")
                
                progress = min(st.session_state.scanned_count / total_pages, 1.0)
                progress_bar.progress(progress)
                
                # Show partial table (Top 50 to save memory)
                if st.session_state.results:
                    df = pd.DataFrame(st.session_state.results)
                    df_placeholder.dataframe(df.tail(10), use_container_width=True)
                
                if count_found >= target_count:
                    executor.shutdown(wait=False, cancel_futures=True)
                    break

        status_text.success(f"✅ Task Complete! {len(all_found_links)} links extracted.")

# --- Export Section (Outside loop to keep it available) ---
if len(st.session_state.results) > 0:
    st.divider()
    df_final = pd.DataFrame(st.session_state.results)
    
    # CSV Export
    csv = df_final.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Download CSV (for Validator)",
        data=csv,
        file_name='scolo_girls_groups.csv',
        mime='text/csv',
    )
    
    # JSON Export (For your PHP Script)
    json_data = df_final['Group Link'].to_json(orient='records')
    st.download_button(
        label="📥 Download JSON (for Bulk Submit Pro)",
        data=json_data,
        file_name='scolo_links_batch.json',
        mime='application/json'
    )
