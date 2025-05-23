# proxygen
Proxy List Generator

## Usage
```
usage: main.py [-h] [-t TIMEOUT] [-c CONCURRENCY] [-o OUTPUT]

options:
  -h, --help            show this help message and exit
  -t, --timeout TIMEOUT
                        Timeout for proxy check (seconds)
  -c, --concurrency CONCURRENCY
                        Number of concurrent checks
  -o, --output OUTPUT   Output file to save proxies
```
## Module usage
```python
async def main():
    collector = ProxyCollector(progress=True)
    proxies = await collector.get_working_proxies()
    print("Working proxies:", proxies)

if __name__ == "__main__":
    asyncio.run(main())
```