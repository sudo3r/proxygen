import asyncio
import aiohttp
import argparse
import sys
import re
import time

total_proxies = 0
checked_proxies = 0
working_proxies = 0
last_update_time = 0

def print_progress():
    global checked_proxies, total_proxies, working_proxies, last_update_time
    current_time = time.time()
    if current_time - last_update_time < 1 and checked_proxies < total_proxies:
        return
    
    last_update_time = current_time
    remaining = total_proxies - checked_proxies
    progress = (checked_proxies / total_proxies) * 100 if total_proxies > 0 else 0
    print(f"\r[*] Progress: {checked_proxies}/{total_proxies} ({progress:.1f}%) | Working: {working_proxies} | Remaining: {remaining}", end="", flush=True)

async def fetch_proxies_from_url(session, url, timeout):
    try:
        async with session.get(url, timeout=timeout) as response:
            if response.status != 200:
                print(f"[-] Failed to fetch {url}: Status {response.status}")
                return []
            content = await response.text()
            proxy_pattern = r'(?:(http|socks4|socks5):\/\/)?(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}:\d{1,5})'
            proxies = []
            for proto, ip_port in re.findall(proxy_pattern, content):
                if proto:
                    proxies.append(f"{proto}://{ip_port}")
                else:
                    proxies.extend([f"{scheme}://{ip_port}" for scheme in ["http", "socks4", "socks5"]])
            print(f"[+] Added {len(proxies)} proxies from {url}")
            return proxies
    except Exception as e:
        print(f"[-] Error fetching {url}: {str(e)}")
        return []

async def check_proxy(session, proxy, timeout):
    global checked_proxies, working_proxies
    try:
        async with session.get("https://httpbin.org/ip", proxy=proxy, timeout=timeout) as response:
            if response.status == 200:
                working_proxies += 1
                return True
            return False
    except Exception:
        return False
    finally:
        checked_proxies += 1
        print_progress()

async def collect_proxies(sources, timeout, concurrency):
    async with aiohttp.ClientSession() as session:
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_fetch(url):
            async with semaphore:
                return await fetch_proxies_from_url(session, url, timeout)
        
        for source in sources:
            tasks.append(bounded_fetch(source))
        
        proxy_lists = await asyncio.gather(*tasks, return_exceptions=True)
        proxies = set()
        for proxy_list in proxy_lists:
            if isinstance(proxy_list, list):
                proxies.update(proxy_list)
        
        print(f"[+] Collected {len(proxies)} unique proxies")
        return list(proxies)

async def check_proxies(proxies, timeout, concurrency, output_file):
    global total_proxies, checked_proxies, working_proxies
    total_proxies = len(proxies)
    checked_proxies = 0
    working_proxies = 0
    
    async with aiohttp.ClientSession() as session:
        tasks = []
        semaphore = asyncio.Semaphore(concurrency)
        
        async def bounded_check(proxy):
            async with semaphore:
                is_working = await check_proxy(session, proxy, timeout)
                if is_working and output_file:
                    with open(output_file, 'a') as f:
                        f.write(f"{proxy}\n")
                return is_working
        
        for proxy in proxies:
            tasks.append(bounded_check(proxy))
        
        await asyncio.gather(*tasks, return_exceptions=True)
        print(f"\n[+] Found {working_proxies} working proxies", flush=True)

async def main():
    parser = argparse.ArgumentParser(description="Proxy List Generator")
    parser.add_argument('-o', '--output', required=True, help="Output file for working proxies")
    parser.add_argument('-c', '--concurrency', type=int, default=30, help="Number of concurrent requests")
    parser.add_argument('-t', '--timeout', type=int, default=3, help="Timeout in seconds")

    args = parser.parse_args()

    try:
        with open("sources.txt", 'r') as f:
            sources = [line.strip() for line in f if line.strip()]
        if not sources:
            print("[-] sources.txt is empty!")
            sys.exit(1)
    except FileNotFoundError:
        print("[-] sources.txt not found!")
        sys.exit(1)
    except Exception as e:
        print(f"[-] Error reading sources.txt: {str(e)}")
        sys.exit(1)

    print(f"[*] Starting proxy collection from {len(sources)} GitHub sources")
    proxies = await collect_proxies(sources, args.timeout, args.concurrency)
    
    if not proxies:
        print("[-] No proxies collected from GitHub!")
        sys.exit(1)
    
    print(f"[*] Checking {len(proxies)} proxies")
    await check_proxies(proxies, args.timeout, args.concurrency, args.output)

if __name__ == "__main__":
    asyncio.run(main())