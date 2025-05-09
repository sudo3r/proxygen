import argparse
import asyncio
import aiohttp
import time
from typing import List, Tuple
import sys
import signal

# Configuration
TEST_URL = "http://httpbin.org/ip"
DEFAULT_TIMEOUT = 10
MAX_WORKERS = 200
MIN_RESPONSE_SIZE = 10

# Global variables
proxies: List[str] = []
verified_proxies: List[Tuple[str, float]] = []
session = None
output_file = "proxies.txt"
stop_flag = False
total_proxies = 0
checked_proxies = 0
last_update_time = 0

def handle_signal(sig, frame):
    global stop_flag
    print("\n[!] Received shutdown signal, saving collected proxies...")
    stop_flag = True
    save_proxies()
    sys.exit(0)

def print_progress():
    global checked_proxies, total_proxies, last_update_time
    current_time = time.time()
    if current_time - last_update_time < 1 and checked_proxies < total_proxies:
        return
    
    last_update_time = current_time
    remaining = total_proxies - checked_proxies
    progress = (checked_proxies / total_proxies) * 100
    print(f"\r[*] Progress: {checked_proxies}/{total_proxies} ({progress:.1f}%) | "
          f"Working: {len(verified_proxies)} | "
          f"Remaining: {remaining} ", end="", flush=True)

async def init_session(timeout: int):
    global session
    session = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=timeout),
        connector=aiohttp.TCPConnector(force_close=True, limit=0)
    )

async def close_session():
    if session:
        await session.close()

async def fetch_proxies(sources: List[str], timeout: int):
    print("[*] Fetching proxies from sources...")
    if not session:
        await init_session(timeout)

    tasks = []
    for source in sources:
        tasks.append(_fetch_source(source, timeout))

    await asyncio.gather(*tasks)
    proxies[:] = list(set(proxies))
    print(f"[+] Found {len(proxies)} unique proxies")

async def _fetch_source(source: str, timeout: int):
    try:
        async with session.get(source, timeout=aiohttp.ClientTimeout(total=timeout)) as response:
            if response.status == 200:
                text = await response.text()
                new_proxies = []
                for line in text.splitlines():
                    line = line.strip()
                    if line:
                        if '://' not in line:
                            line = f"http://{line}"
                        new_proxies.append(line)
                proxies.extend(new_proxies)
                print(f"[+] Added {len(new_proxies)} proxies from {source}")
    except Exception:
        pass

async def verify_proxy(proxy: str, semaphore: asyncio.Semaphore, timeout: int):
    global verified_proxies, checked_proxies, stop_flag
    
    if stop_flag:
        return

    async with semaphore:
        try:
            start_time = time.perf_counter()
            async with session.get(
                TEST_URL,
                proxy=proxy,
                timeout=aiohttp.ClientTimeout(total=timeout)
            ) as response:
                if response.status == 200:
                    data = await response.read()
                    if len(data) >= MIN_RESPONSE_SIZE:
                        response_time = time.perf_counter() - start_time
                        verified_proxies.append((proxy, response_time))
        except Exception:
            pass
        finally:
            checked_proxies += 1
            print_progress()

def save_proxies():
    try:
        with open(output_file, 'w') as f:
            for proxy, _ in sorted(verified_proxies, key=lambda x: x[1]):
                f.write(f"{proxy}\n")
    except Exception as e:
        print(f"\n[-] Error saving proxies: {e}")

async def main():
    global total_proxies, checked_proxies
    
    parser = argparse.ArgumentParser(description='ProxyGen - Ultra-Fast Proxy Checker')
    parser.add_argument('-o', '--output', default='proxies.txt', 
                       help='Output file path (default: proxies.txt)')
    parser.add_argument('-s', '--sources', nargs='+', default=None,
                       help='Custom proxy list URLs (space separated)')
    parser.add_argument('-w', '--workers', type=int, default=MAX_WORKERS,
                       help=f'Number of concurrent workers (default: {MAX_WORKERS})')
    parser.add_argument('-t', '--timeout', type=int, default=DEFAULT_TIMEOUT,
                       help=f'Timeout in seconds (default: {DEFAULT_TIMEOUT})')
    
    args = parser.parse_args()
    global output_file
    output_file = args.output

    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)

    default_sources = [
        "https://raw.githubusercontent.com/proxifly/free-proxy-list/main/proxies/all/data.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/all.txt",
        "https://raw.githubusercontent.com/officialputuid/KangProxy/KangProxy/xResults/RAW.txt",
        "https://raw.githubusercontent.com/dpangestuw/Free-Proxy/main/All_proxies.txt"
    ]

    sources = args.sources if args.sources else default_sources

    try:
        await init_session(args.timeout)
        await fetch_proxies(sources, args.timeout)

        if not proxies:
            print("[!] No proxies found to check")
            return

        total_proxies = len(proxies)
        checked_proxies = 0
        
        print(f"[*] Checking {total_proxies} proxies with {args.workers} workers (timeout: {args.timeout}s)")
        print("[*] Press Ctrl+C to save and exit early")
        
        semaphore = asyncio.Semaphore(args.workers)
        tasks = [verify_proxy(proxy, semaphore, args.timeout) for proxy in proxies]
        
        await asyncio.gather(*tasks)
        
        print(f"\n[+] Verification complete. Working proxies: {len(verified_proxies)}")
        save_proxies()

    except Exception as e:
        print(f"\n[!] Error: {e}", file=sys.stderr)
    finally:
        await close_session()

if __name__ == "__main__":
    asyncio.run(main())