# Orb

**a libre, massive footprinting tool**

![version](https://img.shields.io/badge/version-v0.4-ffb020)
![release](https://img.shields.io/badge/release-Yellow_Orb!-ffb020)
![python](https://img.shields.io/badge/python-3-ffb020)
![license](https://img.shields.io/badge/license-GPLv3-ffb020)
![browser js](https://img.shields.io/badge/browser_JS-none-ffb020)

[Website](https://orb.03c8.net) · [Source](https://code.03c8.net/epsylon/orb) · [GitHub](https://github.com/epsylon/orb) · [Contact](mailto:epsylon@riseup.net)

![Orb Web GUI](https://orb.03c8.net/orb-gui.png)

---

## What is Orb?

Orb is a massive footprinting tool. It uses passive and active —automated— methods to provide
real information about a target. You only need to set a *concept* to start gathering data. When
finished, Orb builds you some fancy reports.

**Passive**

- Crawl search engines for public records (deep web included)
- Search for registered domains
- Extract whois info (owners, dates)
- Discover subdomains
- Find machines running services
- Resolve DNS records (A, NS, MX, TXT)
- Extract CVE / CVS vulnerability records

**Active**

- Scan for open ports (TCP/UDP, 1–65535)
- Fingerprint banners (state, vendor, OS, version, CPE)

## Features

- **Multiple search engines** — query one source or all of them at once
- **Deep web** — onion (Tor) records through the Ahmia gateway
- **Whois** — registrant, creation, expiration and last-update dates
- **Subdomains** — passive discovery from search-engine results (no bruteforcing)
- **DNS records** — resolve A, NS, MX and TXT, with custom resolvers
- **Port scanning** — Nmap-powered TCP/UDP scanning with service detection
- **Banner grabbing** — state, product, version, name, extra info and CPE
- **CVE / CVS** — vulnerability lookups powered by the NVD API
- **Reports** — raw text and, optionally, structured JSON per target
- **Web GUI** — optional local interface
- **Tor aware** — built-in Tor connection check
- **Self-update** — pull the latest stable version from git

## Install

Orb runs on many platforms. It requires **Python 3** and a few libraries:
`ddgs`, `whois`, `dnspython`, `python-nmap` and `requests`.

```bash
git clone https://github.com/epsylon/orb
cd orb

sudo apt-get install nmap python3-pip
pip3 install -r orb/docs/requeriments.txt

# or install the libraries manually
pip3 install ddgs whois dnspython python-nmap requests --user
```

The Nmap system binary is required for the active port-scanning features.

Source libs:

- Python — https://www.python.org/downloads/
- ddgs — https://pypi.org/project/ddgs/
- whois — https://pypi.org/project/whois/
- dnspython — https://pypi.org/project/dnspython/
- python-nmap — https://pypi.org/project/python-nmap/
- requests — https://pypi.org/project/requests/

## Usage

```bash
# full footprinting of a target
python3 orb --spell='target'

# massive run across several TLDs, using all engines
python3 orb --spell='target' --ext='.com,.net,.org' --sa

# passive-only reconnaissance with a chosen engine
python3 orb --spell='target' --passive --se='bing'

# active only, TCP scan on a custom port range
python3 orb --spell='target' --active --scan-tcp --scan-ports='1-1024'

# custom DNS resolvers and a JSON report
python3 orb --spell='target' --resolver='1.1.1.1,8.8.8.8' --json='target.json'

# pace requests to avoid rate limiting (seconds between requests)
python3 orb --spell='target' --delay='2'

# extra utilities
python3 orb --gui            # local web interface
python3 orb --list-engines   # list supported search engines
python3 orb --check-tor      # verify Tor is used properly
python3 orb --update         # update to the latest stable version
```

## Options

```
 ./orb --help

Usage: Orb.py [options]

Options:
  --version             show program's version number and exit
  -h, --help            show this help message and exit
  -v, --verbose         active verbose on requests
  --check-tor           check to see if Tor is used properly
  --update              check for latest stable version
  --spell=TARGET        start complete footprinting on this target
  --gui                 run GUI (Orb Web Interface)
  --delay=DELAY         set delay in seconds between requests (default: 1)

  *Methods*:
    These options can be used to set some footprinting interaction
    restrictions with target(s). You only can set one:

    --passive           use only -passive- methods
    --active            use only -active- methods

  *Search Engines*:
    These options can be used to specify which search engines use to
    extract information:

    --se=ENGINE         set search engine (default: DuckDuckGo)
    --se-ext=ENGINELOC  set location for search engine (ex: 'fr')
    --sa                search massively using all search engines
    --list-engines      list all supported search engines

  *Public*:
    Orb will search for interesting public records. You can choose
    multiple:

    --no-public         disable search for public records
    --no-deep           disable deep web records
    --no-social         disable social records
    --social-f=SOCIALF  set a list of social sources from file
    --no-news           disable news records
    --news-f=NEWSF      set a list of news sources from file

  *Domains*:
    Orb will search on different databases for registered domains using
    IANA supported by default. You only can set one:

    --ext=EXT           set extensions manually (ex: --ext='.com,.net,.es')
    --ext-f=EXTFILE     set a list of extensions from file

  *Whois*:
    Orb will search on 'Whois' records for registrant information:

    --no-whois          disable extract whois information

  *Subdomains*:
    Orb will try to discover info about subdomains:

    --no-subs           disable try to discover subdomains

  *DNS*:
    Orb will try to discover info about DNS records and machines running
    them. You can choose multiple:

    --no-dns            disable try to discover DNS records
    --resolver=RESOLV   specify custom DNS servers (ex: '8.8.8.8,8.8.8.4')

  *Port Scanning*:
    These options can be used to specify how to perfom port scanning
    tasks. You can choose multiple:

    --no-scanner        disable scanner
    --no-scan-dns       disable scan DNS machines
    --no-scan-ns        disable scan NS records
    --no-scan-mx        disable scan MX records
    --scan-tcp          set scanning protocol to only TCP (default TCP+UDP)
    --scan-ports=PORTS  set range of ports to scan (default 1-65535)
    --show-filtered     show 'filtered' ports on results

  *Banner grabbing*:
    Orb will try to extract interesting information about services running
    on machines discovered (ex: OS, vendor, version, cpe, cvs):

    --no-banner         disable extract banners from services
    --no-cve            disable extract vulnerabilities from CVE
    --no-cvs            disable extract CVS description

  *Reporting*:
    These options can be used to specify exporting methods for your
    results. You can choose multiple:

    --no-log            disable generate reports
    --json=JSON         generate json report (ex: --json='foo.json')
```

## Methods

You can select a set of options organized by footprinting method:

- **Passive** — public, deep web, social, news, whois and subdomain discovery (non-intrusive); no port/DNS scanning and no banner grabbing.

  ```bash
  python3 orb --spell='target' --passive
  ```

- **Active** — the opposite of *passive*.

  ```bash
  python3 orb --spell='target' --active
  ```

## Search engines

Gather public records from multiple sources. Pick one with `--se`, or query them all at once
with `--sa`:

`duck` · `bing` · `brave` · `mojeek` · `yahoo` · `startpage` · `ecosia`

Deep web (onion) records are retrieved through **Ahmia** (ahmia.fi). List all supported engines
with `python3 orb --list-engines`.

```bash
python3 orb --spell='target' --se='bing'
python3 orb --spell='target' --sa
```

You can also target a location with `--se-ext` (france=fr, italy=it, ...):

```bash
python3 orb --spell='target' --se-ext='es'
```

## Public records

Orb searches the WWW for interesting public records. You decide what is "interesting" by building
lists of sources organized in two categories: social and news. An example folder for Spain is
included:

```bash
python3 orb --spell='target' --social-f='core/sources/spain/social.txt' --news-f='core/sources/spain/news.txt'
```

By default it uses a set of most ranked global services sorted by category, so you get a nice
global scope from the beginning.

## Domains

By default Orb uses IANA-supported TLDs, but you can set your own:

```bash
python3 orb --spell='target' --ext='.com,.net,.org'
python3 orb --spell='target' --ext-f='core/sources/user-exts.txt'
```

## Whois

Orb searches 'Whois' records for registrant information.

```
- Domain: microsoft.com
- Registrant: MarkMonitor Inc.
- Creation date: 1991-05-02 00:00:00
- Expiration: 2025-05-03 00:00:00
- Last update: 2024-10-09 00:00:00
```

## Subdomains

Orb discovers subdomains using a passive method with search engines (no bruteforcing).

## DNS

Orb resolves DNS records (A, NS, MX, TXT) and the machines running them. You can set custom
resolvers (Google is used by default):

```bash
python3 orb --spell='target' --resolver='8.8.8.8,8.8.4.4'
```

## Port scanning

Orb uses the Nmap Python wrapper to perform port-scanning tasks. Set TCP only (TCP+UDP by default),
choose a port range, and optionally show 'filtered' ports:

```bash
python3 orb --spell='target' --scan-tcp
python3 orb --spell='target' --scan-ports='21-443'
python3 orb --spell='target' --scan-ports='21-443' --show-filtered
```

Only 'Open' ports are shown by default.

## Banner grabbing

Orb extracts information about services running on discovered machines (OS, vendor, version, CPE)
and correlates them with known vulnerabilities from the NVD:

```
- IP: XXX.XXX.XXX.XXX
  * State : up
   - Protocol : tcp
     + Port: 80 ( open ) - IBM WebSEAL reverse http proxy  |  http-proxy
       + CVE-2014-0963 -> https://nvd.nist.gov/vuln/detail/CVE-2014-0963
         The Reverse Proxy feature in IBM Global Security Kit (aka GSKit) in IBM Security Access
         Manager (ISAM) for Web 7.0 and 8.0 allows remote attackers to cause a denial of service.
```

## Reporting

Orb logs all tasks and results per target under a `reports/` folder.

```bash
python3 orb --spell='target' --no-log          # no reports
python3 orb --spell='target' -v                # verbose output
python3 orb --spell='target' --json='target.json'   # JSON report
```

## Contribute

Orb is free software. If it is useful to you, consider supporting its development:

- **Bitcoin [BTC]:** `19aXfJtoYJUoXEZtjNwsah2JKN9CK5Pcjw`
- **ECOin [ECO]:** `EZnYs33TG87ZzBWgADrj8653s3bPUqreW9`

Found a bug, have a patch or an idea? Reach out to psy (epsylon@riseup.net).

---

**Orb** — massive footprinting tool · 2016 / 2026 · by [psy](https://03c8.net) · Released under the [GNU GPLv3](https://www.gnu.org/licenses/gpl-3.0.html)
