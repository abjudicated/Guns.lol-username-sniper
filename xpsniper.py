import requests
import random
import string
import time
import sys
import os
import threading
from colorama import init, Fore, Style
from urllib.parse import urlparse

init(autoreset=True)

def load_proxies():
    """Load proxies from proxies.txt file"""
    proxy_file = os.path.join(os.path.dirname(__file__), 'proxies.txt')
    proxies = []
    
    try:
        with open(proxy_file, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    proxies.append(line)
        
        if not proxies:
            print(f"{Fore.RED}[!] No proxies found in {proxy_file}")
            return None
            
        print(f"{Fore.GREEN}[+] {len(proxies)} proxies loaded")
        return proxies
        
    except FileNotFoundError:
        print(f"{Fore.RED}[!] Proxy file not found: {proxy_file}")
        return None
    except Exception as e:
        print(f"{Fore.RED}[!] Error loading proxies: {e}")
        return None

def get_random_proxy(proxies_list):
    """Return random proxy from list"""
    if not proxies_list:
        return None
    return random.choice(proxies_list)

def format_proxy_for_requests(proxy_string):
    """Format proxy for requests library"""
    try:
        parsed = urlparse(proxy_string)
        if parsed.scheme in ['http', 'https']:
            return {
                'http': proxy_string,
                'https': proxy_string
            }
        elif parsed.scheme in ['socks4', 'socks5']:
            # for socks proxies
            return {
                'http': proxy_string,
                'https': proxy_string
            }
        return None
    except Exception as e:
        print(f"{Fore.YELLOW}[!] Proxy formatting error {proxy_string}: {e}")
        return None

BANNER = f"""
{Fore.MAGENTA}██╗  ██╗██████╗ ███████╗███╗   ██╗██╗██████╗ ███████╗██████╗ 
{Fore.MAGENTA}╚██╗██╔╝██╔══██╗██╔════╝████╗  ██║██║██╔══██╗██╔════╝██╔══██╗
{Fore.MAGENTA} ╚███╔╝ ██████╔╝███████╗██╔██╗ ██║██║██████╔╝█████╗  ██║  ██║
{Fore.MAGENTA} ██╔██╗ ██╔═══╝ ╚════██║██║╚██╗██║██║██╔═══╝ ██╔══╝  ██║  ██║
{Fore.MAGENTA}██╔╝ ██╗██║     ███████║██║ ╚████║██║██║     ███████╗██████╔╝
{Fore.MAGENTA}╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝╚═════╝ 
{Fore.MAGENTA}    > @ykgtteh        > sniper.lol 
{Style.RESET_ALL}
"""

def generate_username(total_length, digits_count, separator=None):
    letters_count = total_length - digits_count
    if separator:
        letters_count -= 1
    if letters_count < 0:
        letters_count = 0
    
    chars = []
    chars.extend(random.choices(string.ascii_lowercase, k=letters_count))
    chars.extend(random.choices(string.digits, k=digits_count))
    
    random.shuffle(chars)
    username = ''.join(chars)
    
    if separator:
        # Choose separator if 'both'
        if separator == 'both':
            actual_sep = random.choice(['.', '_'])
        else:
            actual_sep = separator
        
        # Insert separator at random position (start, middle, or end)
        if len(username) > 0:
            pos = random.randint(0, len(username))
            username = username[:pos] + actual_sep + username[pos:]
        else:
            username = actual_sep
    
    return username

def check_username(username, session, proxies_list):
    url = f"https://guns.lol/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    for attempt in range(2):
        try:
            # Choose random proxy
            proxy_dict = None
            if proxies_list:
                proxy_string = get_random_proxy(proxies_list)
                if proxy_string:
                    proxy_dict = format_proxy_for_requests(proxy_string)
            
            response = session.get(url, headers=headers, proxies=proxy_dict, timeout=3)
            
            if response.status_code == 200:
                if ">Username not found<" in response.text:
                    return username, True
                else:
                    return username, False
            elif response.status_code == 429:
                time.sleep(0.5)  # Shorter pause
                continue
            elif response.status_code in [403, 503]:
                time.sleep(1)  # Shorter pause
                continue
            else:
                # 404 means available
                if response.status_code == 404:
                    return username, True
                return username, False
                
        except requests.exceptions.ConnectTimeout:
            if attempt == 1: 
                print(f"{Fore.YELLOW}[!] Connection timeout for {username}")
            time.sleep(0.05)
            continue
        except requests.exceptions.ConnectionError:
            if attempt == 1:
                print(f"{Fore.YELLOW}[!] Connection error for {username}")
            time.sleep(0.05)
            continue
        except requests.exceptions.RequestException:
            if attempt == 1:
                print(f"{Fore.YELLOW}[!] Request error for {username}")
            time.sleep(0.05)
            continue
        except Exception as e:
            error_msg = str(e).lower()
            
            if attempt == 1: 
                if "proxy" in error_msg or "socks" in error_msg:
                    print(f"{Fore.RED}[!] Proxy error for {username}")
                elif "timeout" in error_msg:
                    print(f"{Fore.YELLOW}[!] Timeout for {username}")
            time.sleep(0.05)
            continue
            
    return username, False # Skip if failed 2 times

def send_to_webhook(webhook_url, username):
    if not webhook_url:
        return
        
    data = {
        "username": "xpsniped",
        "content": f"`{username}` *is **available***"
    }
    try:
        requests.post(webhook_url, json=data, timeout=5)
    except Exception:
        pass

class UsernameGenerator:
    def __init__(self, total_length, digits_count, max_count, separator=None):
        self.total_length = total_length
        self.digits_count = digits_count
        self.max_count = max_count
        self.separator = separator
        self.generated = 0
        self.lock = threading.Lock()
        self.seen = set()
        
    def get_next(self):
        with self.lock:
            if self.generated >= self.max_count:
                return None
            
            # Find unique username
            attempts = 0
            while attempts < 1000:
                uname = generate_username(self.total_length, self.digits_count, self.separator)
                if uname not in self.seen:
                    self.seen.add(uname)
                    self.generated += 1
                    return uname
                attempts += 1
                
            # Stop
            return None

def worker(generator, webhook_url, counter_lock, stats, proxies_list):
    session = requests.Session()
    while True:
        uname = generator.get_next()
        if not uname:
            break
            
        try:
            uname_result, is_valid = check_username(uname, session, proxies_list)
            
            # Send to Discord
            if is_valid:
                threading.Thread(target=send_to_webhook, args=(webhook_url, uname_result), daemon=True).start()
                
            with counter_lock:
                stats['checked'] += 1
                if is_valid:
                    stats['valid'].append(uname_result)
                    print(Fore.GREEN + f"[✓] {uname_result} is available")
                else:
                    print(Fore.RED + f"[-] Taken: {uname_result}")
                    
                if stats['checked'] % 50 == 0:
                    print(Fore.MAGENTA + f"[*] Progress: {stats['checked']}/{stats['total']} | Valid found: {len(stats['valid'])}")
                    if os.name == 'nt':
                        taken = stats['checked'] - len(stats['valid'])
                        os.system(f'title xpsniped ^| Available: {len(stats["valid"])} ^| Taken: {taken}')
        except Exception as e:
            with counter_lock:
                print(Fore.RED + f"[!] Error checking {uname}: {e}")
                
        time.sleep(0.02)  # Very short delay

def main():
    if os.name == 'nt':
        os.system('color 4')
        os.system('title xpsniped')
        os.system('cls')
    else:
        os.system('clear')
        
    print(BANNER)
    
    # LOAD PROXIES
    proxies = load_proxies()
    use_proxies = True
    
    if not proxies:
        print(f"{Fore.MAGENTA}[!] Script will continue without proxies.")
        use_proxies = False
    else:
        print(f"{Fore.YELLOW}[!] Proxies available but disabled by default for speed.")
        print(Fore.MAGENTA + "[?] Use proxies? (y/n, default: n): " + Style.RESET_ALL, end="")
        choice = input().strip().lower()
        if choice == 'y' or choice == 'yes':
            use_proxies = True
            print(f"{Fore.GREEN}[+] Proxies enabled.")
        else:
            use_proxies = False
            print(f"{Fore.YELLOW}[!] Proxies disabled (fast mode).")
    
    print(Fore.MAGENTA + "[?] Enter Webhook URL (leave empty to skip): " + Style.RESET_ALL, end="")
    webhook_url = input().strip()
    
    try:
        print(Fore.MAGENTA + "[?] Total characters in username? (Min 2, Max 32): " + Style.RESET_ALL, end="")
        total_length = int(input())
        if total_length < 2 or total_length > 32:
            print(Fore.RED + "[!] Invalid length. Exiting...")
            sys.exit(1)
            
        print(Fore.MAGENTA + f"[?] How many digits among these {total_length} characters?: " + Style.RESET_ALL, end="")
        digits_count = int(input())
        if digits_count > total_length:
            print(Fore.RED + "[!] You can't have more digits than the total length. Exiting...")
            sys.exit(1)
            
        print(Fore.MAGENTA + "[?] Separator option:")
        print(Fore.MAGENTA + "  1 - None")
        print(Fore.MAGENTA + "  2 - Only dots (.)")
        print(Fore.MAGENTA + "  3 - Only underscores (_)")
        print(Fore.MAGENTA + "  4 - Both dots and underscores randomly")
        print(Fore.MAGENTA + "[?] Choose (1-4): " + Style.RESET_ALL, end="")
        sep_choice = input().strip()
        
        separator = None
        if sep_choice == '2':
            separator = '.'
        elif sep_choice == '3':
            separator = '_'
        elif sep_choice == '4':
            separator = 'both'
        elif sep_choice != '1':
            print(Fore.RED + "[!] Invalid choice. Using none.")
            
        print(Fore.MAGENTA + "[?] How many usernames to generate and check?: " + Style.RESET_ALL, end="")
        count = int(input())
        
    except ValueError:
        print(Fore.RED + "Invalid input. Please enter numbers.")
        return

    print(Fore.MAGENTA + f"\n[*] Starting multi-threaded checks for {count} usernames...\n")
    
    generator = UsernameGenerator(total_length, digits_count, count, separator if separator else None)
    counter_lock = threading.Lock()
    stats = {
        'checked': 0,
        'total': count,
        'valid': []
    }
    
    threads = []
    # 10 threads
    for _ in range(10):
        proxy_list = proxies if use_proxies else None
        t = threading.Thread(target=worker, args=(generator, webhook_url, counter_lock, stats, proxy_list))
        t.daemon = True
        t.start()
        threads.append(t)
        
    for t in threads:
        try:
            # Catch Ctrl+C
            while t.is_alive():
                t.join(0.5)
        except KeyboardInterrupt:
            print(Fore.RED + "\n[!] Interrupted by user. Exiting gracefully...")
            break
                
    print("\n" + "="*50)
    print(Fore.MAGENTA + "🏁 FINISHED!")
    print(Fore.MAGENTA + f"Checked: {stats['checked']}")
    print(Fore.MAGENTA + f"Valid usernames: {len(stats['valid'])}")
    
    if stats['valid']:
        pass # No txt file
    
    input("\nPress any key to exit...")

if __name__ == "__main__":
    main()
