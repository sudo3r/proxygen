import asyncio
import argparse
from proxygen import ProxyCollector

async def main(args):
    collector = ProxyCollector(
        timeout=args.timeout,
        concurrency=args.concurrency,
        progress=True
    )
    output_file = None
    if args.output:
        output_file = open(args.output, "w")
    count = 0
    async for proxy in collector.iter_working_proxies():
        count += 1
        if output_file:
            output_file.write(str(proxy) + "\n")
            output_file.flush()
        else:
            print(proxy)
    if output_file:
        output_file.close()
        print(f"\n==> Saved {count} proxies to {args.output}")
    else:
        print(f"\n==> Found {count} working proxies.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Proxy List Generator")
    parser.add_argument("-t", "--timeout", type=int, default=3, help="Timeout for proxy check (seconds)")
    parser.add_argument("-c", "--concurrency", type=int, default=30, help="Number of concurrent checks")
    parser.add_argument("-o", "--output", type=str, help="Output file to save proxies")
    args = parser.parse_args()
    asyncio.run(main(args))