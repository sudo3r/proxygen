import asyncio
import argparse
from proxygen import ProxyCollector

async def main(args):
    collector = ProxyCollector(
        timeout=args.timeout,
        concurrency=args.concurrency,
        progress=True
    )
    proxies = await collector.get_working_proxies()
    print(f"\n==> Found {len(proxies)} working proxies.")
    if args.output:
        with open(args.output, "w") as f:
            for proxy in proxies:
                f.write(str(proxy) + "\n")
        print(f"==> Saved to {args.output}")
    else:
        print("==> Working proxies:")
        for proxy in proxies:
            print(proxy)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proxy List Generator")
    parser.add_argument("-t", "--timeout", type=int, default=3, help="Timeout for proxy check (seconds)")
    parser.add_argument("-c", "--concurrency", type=int, default=30, help="Number of concurrent checks")
    parser.add_argument("-o", "--output", type=str, help="Output file to save proxies")
    args = parser.parse_args()
    asyncio.run(main(args))