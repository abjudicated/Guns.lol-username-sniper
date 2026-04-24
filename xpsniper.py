import requests
import random
import string
import time
import sys
import os
import threading
from colorama import init, Fore, Style

init(autoreset=True)

BANNER = f"""
{Fore.RED}██╗  ██╗██████╗ ███████╗███╗   ██╗██╗██████╗ ███████╗██████╗ 
{Fore.RED}╚██╗██╔╝██╔══██╗██╔════╝████╗  ██║██║██╔══██╗██╔════╝██╔══██╗
{Fore.RED} ╚███╔╝ ██████╔╝███████╗██╔██╗ ██║██║██████╔╝█████╗  ██║  ██║
{Fore.RED} ██╔██╗ ██╔═══╝ ╚════██║██║╚██╗██║██║██╔═══╝ ██╔══╝  ██║  ██║
{Fore.RED}██╔╝ ██╗██║     ███████║██║ ╚████║██║██║     ███████╗██████╔╝
{Fore.RED}╚═╝  ╚═╝╚═╝     ╚══════╝╚═╝  ╚═══╝╚═╝╚═╝     ╚══════╝╚═════╝ 
{Fore.RED}    >> DEV BY abjudicated <<       >> USERNAME SNIPER <<
{Style.RESET_ALL}
"""

def generate_username(total_length, digits_count):
    letters_count = total_length - digits_count
    if letters_count < 0:
        letters_count = 0
    
    chars = []
    chars.extend(random.choices(string.ascii_lowercase, k=letters_count))
    chars.extend(random.choices(string.digits, k=digits_count))
    
    random.shuffle(chars)
    return ''.join(chars)

def check_username(username, session):
    url = f"https://guns.lol/{username}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }
    
    for _ in range(3): # Max 3 retries
        try:
            response = session.get(url, headers=headers, timeout=5)
            
            if response.status_code == 200:
                if ">Username not found<" in response.text:
                    return username, True
                else:
                    return username, False
            elif response.status_code == 429:
                time.sleep(2)  # Rate limit pause
                continue
            elif response.status_code in [403, 503]:
                # Cloudflare block, wait
                time.sleep(2)
                continue
            else:
                # 404 means available
                if response.status_code == 404:
                    return username, True
                return username, False
                
        except Exception:
            time.sleep(1)
            continue
            
    return username, False # Skip if failed 3 times

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
    def __init__(self, total_length, digits_count, max_count):
        self.total_length = total_length
        self.digits_count = digits_count
        self.max_count = max_count
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
                uname = generate_username(self.total_length, self.digits_count)
                if uname not in self.seen:
                    self.seen.add(uname)
                    self.generated += 1
                    return uname
                attempts += 1
                
            # Stop if stuck
            return None

def worker(generator, webhook_url, counter_lock, stats):
    session = requests.Session()
    while True:
        uname = generator.get_next()
        if not uname:
            break
            
        try:
            uname_result, is_valid = check_username(uname, session)
            
            # Send to Discord in bg
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
                    print(Fore.RED + f"[*] Progress: {stats['checked']}/{stats['total']} | Valid found: {len(stats['valid'])}")
        except Exception as e:
            with counter_lock:
                print(Fore.RED + f"[!] Error checking {uname}: {e}")
                
        time.sleep(0.1)  # Delay to save your internet connection

def main():
    if os.name == 'nt':
        os.system('color 4')
        os.system('cls')
    else:
        os.system('clear')
        
    print(BANNER)
    
    print(Fore.RED + "[?] Enter Webhook URL (leave empty to skip): " + Style.RESET_ALL, end="")
    webhook_url = input().strip()
    
    try:
        print(Fore.RED + "[?] Total characters in username? (Min 2, Max 32): " + Style.RESET_ALL, end="")
        total_length = int(input())
        if total_length < 2 or total_length > 32:
            print(Fore.RED + "[!] Invalid length. Exiting...")
            sys.exit(1)
            
        print(Fore.RED + f"[?] How many digits among these {total_length} characters?: " + Style.RESET_ALL, end="")
        digits_count = int(input())
        if digits_count > total_length:
            print(Fore.RED + "[!] You can't have more digits than the total length. Exiting...")
            sys.exit(1)
            
        print(Fore.RED + "[?] How many usernames to generate and check?: " + Style.RESET_ALL, end="")
        count = int(input())
        
    except ValueError:
        print(Fore.RED + "Invalid input. Please enter numbers.")
        return

    print(Fore.RED + f"\n[*] Starting multi-threaded checks for {count} usernames...\n")
    
    generator = UsernameGenerator(total_length, digits_count, count)
    counter_lock = threading.Lock()
    stats = {
        'checked': 0,
        'total': count,
        'valid': []
    }
    
    threads = []
    # 5 threads to save connection
    for _ in range(5):
        t = threading.Thread(target=worker, args=(generator, webhook_url, counter_lock, stats))
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
    print(Fore.RED + "🏁 FINISHED!")
    print(Fore.RED + f"Checked: {stats['checked']}")
    print(Fore.RED + f"Valid usernames: {len(stats['valid'])}")
    
    if stats['valid']:
        pass # No txt file
    
    input("\nPress any key to exit...")

if __name__ == "__main__":
    main()
