# proxygen
Proxy List Generator

## Installation
```shell
pip install aiohttp
```
## Usage
```
usage: proxygen.py [-h] [-o OUTPUT] [-s SOURCES [SOURCES ...]] [-w WORKERS] [-t TIMEOUT]

ProxyGen - Proxy List Generator

options:
  -h, --help            show this help message and exit
  -o, --output OUTPUT   Output file path (default: proxies.txt)
  -s, --sources SOURCES [SOURCES ...]
                        Custom proxy list URLs (space separated)
  -w, --workers WORKERS
                        Number of concurrent workers (default: 200)
  -t, --timeout TIMEOUT
                        Timeout in seconds (default: 10)
```
