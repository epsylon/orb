#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
"""
This file is part of the orb project, https://orb.03c8.net

Orb - 2016/2026 - by psy (epsylon@riseup.net)

You should have received a copy of the GNU General Public License along
with Orb; if not, write to the Free Software Foundation, Inc., 51
Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import webbrowser, socket, traceback, sys, re, os, datetime, random, json, ssl, time, logging
import urllib.request, urllib.parse
from urllib.parse import urlencode, urlparse, unquote
from .options import OrbOptions
from .update import Updater
from .orb import ClientThread

for _noisy in ("ddgs", "httpx", "httpcore", "primp"): # silence 3rd party request loggers
    logging.getLogger(_noisy).setLevel(logging.CRITICAL)

DEBUG = 0
MAX_RESULTS = 30 # max results to retrieve from search engines

class Orb(object):
    def __init__(self):
        self.GIT_REPOSITORY = 'https://code.03c8.net/epsylon/orb' # oficial code source [OK! 26/01/2019]
        self.GIT_REPOSITORY2 = 'https://github.com/epsylon/orb' # mirror source [since: 04/06/2018]
        self.search_engines = [] # available search engines
        self.search_engines.append('duck') # [01/07/2026]
        self.search_engines.append('bing') # [01/07/2026]
        self.search_engines.append('brave') # [01/07/2026]
        self.search_engines.append('mojeek') # [01/07/2026]
        self.search_engines.append('yahoo') # [01/07/2026]
        self.search_engines.append('startpage') # [01/07/2026]
        self.search_engines.append('ecosia') # [01/07/2026]
        self.referer = '127.0.0.1' # set referer to localhost / WAF black magic!
        self.ctx = ssl.create_default_context() # ssl context for requests
        self.ctx.check_hostname = False
        self.ctx.verify_mode = ssl.CERT_NONE
        self.last_request = 0.0 # timestamp of last outbound request (rate limiting)
        self.engine_fail = False # search engines controller
        self.dns_Amachines = [] # used to check if ip = DNS-A records
        self.socials = None # used to get social links from source file
        self.news = None # used to get news links from source file
        self.url_links = [] #  urls extracted from search engines
        self.sub_links = [] #  subdomains extracted from search engines
        self.extract_wikipedia_record = True # used to not repeat wikipedia descriptions
        self.extract_ranked_links = False # used to extract ranked links on search engines
        self.top_ranked = {}
        self.wikipedia_texts = [] # wikipedia descriptions
        self.social_links = {}
        self.news_links = {}
        self.ranked_record = 0
        self.agents = [] # user-agents
        self.ips_scanner = [] # IPs related with scanner without dns records
        f = open("core/sources/user-agents.txt").readlines()
        for line in f:
            self.agents.append(line)

    def set_options(self, options):
        self.options = options

    def create_options(self, args=None):
        self.optionParser = OrbOptions()
        self.options = self.optionParser.get_options(args)
        if not self.options:
            return False
        return self.options

    def banner(self):
        self.optionParser.banner()

    def try_running(self, func, error, args=None):
        options = self.options
        args = args or []
        try:
            return func(*args)
        except Exception as e:
            print(error, "error")
            if DEBUG != 0:
                traceback.print_exc()

    def generate_report(self): # generate raw log/report
        if not os.path.exists('reports/'):
            os.makedirs('reports/')
        if not self.options.gui: # generate report when no gui
            if not os.path.exists('reports/' + self.options.target):
                os.makedirs('reports/' + self.options.target)
            namefile = self.options.target + "_" + str(datetime.datetime.now())
            if self.options.verbose:
                print("\n[Verbose] - Generating log: " + 'reports/' + self.options.target + "/" + namefile + ".raw", "\n")
            self.report = open('reports/' + self.options.target + "/" + namefile + ".raw", 'a') # generate .raw file

    def generate_json(self): # generate json report
        if not os.path.exists('reports/'):
            os.makedirs('reports/')
        if not self.options.gui: # generate report when no gui
            if not os.path.exists('reports/' + self.options.target):
                os.makedirs('reports/' + self.options.target)
            namefile = self.options.json
            if self.options.verbose:
                print("[Verbose] - Generating JSON: " + 'reports/' + self.options.target + "/" + namefile, "\n")
            if os.path.exists('reports/' + self.options.target + "/" + namefile):
                os.remove('reports/' + self.options.target + "/" + namefile) # remove previous report if exists
            self.json_report = open('reports/' + self.options.target + "/" + namefile, 'w') # generate new .json file each time
            self.json_records = [] # accumulate records to emit a single valid JSON array

    def _throttle(self): # pace outbound requests to avoid rate limiting
        try:
            delay = float(self.options.delay) if self.options.delay else 1.0
        except:
            delay = 1.0
        if delay <= 0:
            return
        elapsed = time.time() - self.last_request
        if elapsed < delay:
            time.sleep(delay - elapsed)
        self.last_request = time.time()

    def send_request(self, url): # send requests unique point
        self._throttle() # respect delay between requests
        user_agent = random.choice(self.agents).strip() # set random user-agent
        headers = {'User-Agent' : user_agent, 'Referer' : self.referer, 'Accept' : 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8', 'Accept-Language' : 'en-US,en;q=0.5'}
        req = urllib.request.Request(url, None, headers)
        req_reply = urllib.request.urlopen(req, context=self.ctx, timeout=15).read().decode('utf-8', errors='replace')
        return req_reply

    def _build_query(self, target): # build query term depending on the task
        if self.extract_ranked_links == True: # extract ranked links
            return str(target) # ex: target
        else: # extract subdomains
            return 'site:.' + str(target) # ex: site:.target.com

    def _bing_decode(self, raw): # bing wraps real urls on: ?u=a1<base64>
        raw = raw.replace('&amp;', '&')
        m = re.search(r'[?&]u=a1([^&]+)', raw)
        if not m:
            return raw
        token = m.group(1)
        try:
            b64 = token + '=' * ((4 - len(token) % 4) % 4)
            import base64
            return base64.urlsafe_b64decode(b64).decode('utf-8', errors='replace')
        except:
            return raw

    def _yahoo_decode(self, raw): # yahoo wraps real urls between: RU= .. /RK=
        if 'RU=' in raw:
            piece = raw.rsplit('RU=', 1)[1]
            piece = piece.split('/RK=', 1)[0]
            return urllib.parse.unquote(piece)
        return raw

    def search_using_duck(self, q): # duckduckgo.com (using 'ddgs' library) [01/07/2026]
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter('ignore')
                try:
                    from ddgs import DDGS
                except ImportError:
                    from duckduckgo_search import DDGS
        except ImportError:
            print("\n[Error] - Python library 'ddgs' is not installed. Try: pip3 install ddgs\n")
            return
        region = 'wt-wt' # worldwide by default
        if self.options.engineloc: # set location (ex: 'es' -> 'es-es')
            loc = str(self.options.engineloc).lower()
            region = loc + '-' + loc
        self._throttle() # respect delay between requests
        attempt = 0
        req_reply = None
        while attempt < 3:
            try:
                req_reply = list(DDGS().text(q, region=region, safesearch='off', max_results=MAX_RESULTS))
                break
            except Exception as e:
                attempt = attempt + 1
                if 'Ratelimit' in str(e) or '202' in str(e): # backoff on ratelimit
                    time.sleep(3 * attempt)
                    continue
                return
        if req_reply is None:
            return
        return [ r.get('href') for r in req_reply if isinstance(r, dict) and r.get('href') ]

    def search_using_bing(self, q): # bing.com [01/07/2026]
        query_string = {'q':q, 'first':0}
        if self.options.engineloc: # add search engine location on query: &cc=
            query_string['cc'] = self.options.engineloc
        url = 'https://www.bing.com/search?' + urlencode(query_string)
        try:
            req_reply = self.send_request(url)
        except:
            return
        raw = re.findall(r'<a\s+class="tilk"[^>]*href="([^"]+)"', req_reply)
        if not raw:
            raw = re.findall(r'<h2><a[^>]+href="([^"]+)"[^>]*>', req_reply)
        return [ self._bing_decode(r) for r in raw ]

    def search_using_brave(self, q): # search.brave.com [01/07/2026]
        url = 'https://search.brave.com/search?' + urlencode({'q':q})
        try:
            req_reply = self.send_request(url)
        except:
            return
        for pat in (r'<a\s+href="([^"]+)"[^>]*class="(?:h|result-header|snippet-title)"',
                    r'<a class="(?:h|result-header|snippet-title)"\s+href="([^"]+)"',
                    r'<a\s+href="(https?://[^"]+)"\s+rel="noopener'):
            url_links = re.findall(pat, req_reply)
            if url_links:
                return url_links
        return []

    def search_using_mojeek(self, q): # mojeek.com [01/07/2026]
        url = 'https://www.mojeek.com/search?' + urlencode({'q':q})
        try:
            req_reply = self.send_request(url)
        except:
            return
        for pat in (r'<a class="ob"\s+href="([^"]+)"',
                    r'<a class="title"\s+href="([^"]+)"',
                    r'<a\s+href="(https?://[^"]+)"[^>]*class="title"'):
            url_links = re.findall(pat, req_reply)
            if url_links:
                return url_links
        return []

    def search_using_yahoo(self, q): # search.yahoo.com [01/07/2026]
        url = 'https://search.yahoo.com/search?' + urlencode({'p':q, 'b':1})
        try:
            req_reply = self.send_request(url)
        except:
            return
        for pat in (r'<a class="d-ib[^"]*"\s+href="([^"]+)"',
                    r'<h3 class="title"[^>]*>\s*<a\s+href="([^"]+)"',
                    r'<a\s+href="(https?://[^"]+RU=[^"]+)"'):
            raw = re.findall(pat, req_reply)
            if raw:
                return [ self._yahoo_decode(r) for r in raw ]
        return []

    def search_using_startpage(self, q): # startpage.com [01/07/2026]
        url = 'https://www.startpage.com/do/search?' + urlencode({'query':q})
        try:
            req_reply = self.send_request(url)
        except:
            return
        for pat in (r'<a class="w-gl__result-title result-link"\s+href="([^"]+)"',
                    r'<a class="result-link"\s+href="([^"]+)"',
                    r'<a\s+href="([^"]+)"\s+class="result-link"'):
            url_links = re.findall(pat, req_reply)
            if url_links:
                return url_links
        return []

    def search_using_ecosia(self, q): # ecosia.org [01/07/2026]
        url = 'https://www.ecosia.org/search?' + urlencode({'q':q})
        try:
            req_reply = self.send_request(url)
        except:
            return
        for pat in (r'<a class="result-title"\s+href="([^"]+)"',
                    r'<a\s+href="([^"]+)"[^>]*class="result__title"',
                    r'<a\s+data-test-id="result-link"\s+href="([^"]+)"'):
            url_links = re.findall(pat, req_reply)
            if url_links:
                return url_links
        return []

    def _run_engine(self, engine, q): # dispatch query to selected search engine
        if engine == "duck":
            return self.search_using_duck(q)
        if engine == "bing":
            return self.search_using_bing(q)
        if engine == "brave":
            return self.search_using_brave(q)
        if engine == "mojeek":
            return self.search_using_mojeek(q)
        if engine == "yahoo":
            return self.search_using_yahoo(q)
        if engine == "startpage":
            return self.search_using_startpage(q)
        if engine == "ecosia":
            return self.search_using_ecosia(q)
        return None

    def search_using_torch(self, target): # ahmia.fi (clearnet gateway to onion services) [01/07/2026]
        try:
            url = 'https://ahmia.fi/search/?' + urlencode({'q':str(target)})
            try:
                req_reply = self.send_request(url)
            except:
                print("- Not found!")
                if not self.options.nolog: # generate log
                    self.report.write("\n- Deep Web: Not found!\n\n")
                return
            onions = re.findall(r'redirect_url=(https?%3A%2F%2F[^"&]+\.onion[^"&]*)', req_reply) # extract onion redirects
            onions = [ urllib.parse.unquote(o) for o in onions ]
            if not onions: # fallback: extract raw onion urls
                onions = re.findall(r'(https?://[a-z2-7]{16,56}\.onion[^\s"<]*)', req_reply)
            onions = list(dict.fromkeys(onions)) # remove duplicates keeping order
            if not onions: # no records found
                print("[Info] - No documents were found!")
                if not self.options.nolog: # generate log
                    self.report.write("- Deep Web: Not found!\n\n")
            else:
                for url in onions:
                    print("- Onion URL -> "+ url)
                    if not self.options.nolog: # generate log
                        self.report.write("- Onion URL -> " + url + "\n")
                        if self.options.json: # write reply to json
                            self.json_records.append(['Deep Web',{'Onion': url}])
                if not self.options.nolog: # generate log
                    self.report.write("\n") # zen
        except: # return when fails
            print("- Not found!")
            if not self.options.nolog: # generate log
                self.report.write("\n- Deep Web: Not found!\n\n")
            return

    def _url_host(self, url): # extract lowercase hostname from url
        try:
            return (urlparse(url).hostname or "").lower()
        except:
            return ""

    def extract_social(self, url): # extract social links
        if self.options.public: # safe/return when no extract public records option
            return
        if self.options.social: # safe/return when no extract social records option
            return
        host = self._url_host(url)
        for s in self.socials:
            s = s.lower()
            if host == s or host.endswith("." + s): # match domain, not substring
                self.social_links[s] = url # add s/url to dict

    def extract_news(self, url): # extract news links (using a list from file)
        if self.options.public: # safe/return when no extract public records option
            return
        if self.options.news: # safe/return when no extract news records option
            return
        host = self._url_host(url)
        for n in self.news:
            n = n.lower()
            if host == n or host.endswith("." + n): # match domain, not substring
                self.news_links[n] = url # add n/url to dict

    def extract_wikipedia(self, target): # extract wikipedia summary (REST API)
        title = urllib.parse.quote(str(target).replace(' ', '_'))
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + title
        try:
            data = json.loads(self.send_request(url))
        except:
            return
        if data.get('type') == 'disambiguation': # ambiguous term, skip
            return
        extract = data.get('extract', '')
        if not extract:
            return
        return extract

    def extract_from_engine(self, engine, target): # search using engine
        q = self._build_query(target) # build query term (ranked / subdomains)
        url_links = self._run_engine(engine, q) # retrieve clean urls from engine
        if not url_links: # not records found
            self.engine_fail = True
        else:
            for url in url_links:
                url = urllib.parse.unquote(url)
                if not url.startswith('http'): # discard non absolute urls
                    continue
                if self.extract_ranked_links == True: # ranked links
                    self.url_links.append(url) # collect every result (used for social/news matching)
                    if target in url: # top ranked must relate to target
                        if self.ranked_record == 0:
                            self.top_ranked[engine] = url # add s/url to dict
                            self.ranked_record = self.ranked_record + 1
                else: # subdomains
                    self.sub_links.append(url)
            self.engine_fail = False

    def extract_ranked(self, target, engine): # extract ranked link
        if self.options.public: # safe/return when no extract public records option
            return
        self.extract_ranked_links = True # used to perform different queries to search engines
        self.ranked_record = 0 # extract ranked link
        self.extract_from_engine(engine, target)
        self.extract_ranked_links = False # list semaphore to off

    def public_records_output(self): # output public records after parsing
        # extract and order data gathered + report when found
        print("="*14)
        print("*Top Ranked*:")
        print("="*14)
        if not self.top_ranked:
            print("- Not found!")
            if not self.options.nolog: # generate log
                self.report.write("\n- Top Ranked: Not found!\n\n")
        else:
            for key,val in list(self.top_ranked.items()):
                print("- {} -> {}".format(key, val))
                if not self.options.nolog: # generate log
                    self.report.write("- Top ranked: " + key + " -> " + val + "\n")
                    if self.options.json: # write reply to json
                        self.json_records.append(['Ranked',{'Engine': key, 'Top': val}])
            if not self.options.nolog: # generate log
                self.report.write("\n") # raw format task
        if self.extract_wikipedia_record == True: # not need to repeat wikipedia descriptions on each extension
            print("="*14)
            print("*Wikipedia*:")
            print("="*14)
            if not self.wikipedia_texts:
                print("- Not found!")
                if not self.options.nolog: # generate log
                    self.report.write("- Wikipedia: Not found!\n\n")
            else:
                for wikipedia in self.wikipedia_texts:
                    if wikipedia is not None:
                        print("-", wikipedia + "\n")
                        if not self.options.nolog: # generate log
                            self.report.write("- " + wikipedia + "\n")
                            if self.options.json: # write reply to json (non parsed ascii)
                                self.json_records.append(['Wikipedia',{'Description': wikipedia}])
                if wikipedia is None:
                    print("- Not found!")
                if not self.options.nolog: # generate log
                    self.report.write("\n") # raw format task
        if not self.options.social:
            print("="*14)
            print("*Social*:")
            print("="*14)
            if not self.social_links:
                print("- Not found!")
                if not self.options.nolog: # generate log
                    self.report.write("- Social: Not found!\n\n")
            else:
                for key,val in list(self.social_links.items()):
                    print("- {} -> {}".format(key, val))
                    if not self.options.nolog: # generate log
                        self.report.write("- " + key + " -> " + val + "\n")
                        if self.options.json: # write reply to json
                            self.json_records.append(['Social',{key:val}])
                if not self.options.nolog: # generate log
                    self.report.write("\n") # raw format task
        if not self.options.news:
            print("="*14)
            print("*News*:")
            print("="*14)
            if not self.news_links:
                print("- Not found!")
                if not self.options.nolog: # generate log
                    self.report.write("- News: Not found!\n\n")
            else:
                for key,val in list(self.news_links.items()):
                    print("- {} -> {}".format(key, val))
                    if not self.options.nolog: # generate log
                        self.report.write("- " + key + " -> " + val + "\n")
                        if self.options.json: # write reply to json
                            self.json_records.append(['News',{key:val}])
                if not self.options.nolog: # generate log
                    self.report.write("\n") # raw format task

    def extract_public(self, target): # extract general public records
        if self.options.public: # safe/return when no extract public records option
            return
        if self.options.allengines: # search using all search engines available (pass to next when fails)
            for engine in self.search_engines:
                self.extract_ranked(target, engine)
        else:
            if self.options.engine:
                if self.options.engine in self.search_engines:
                    engine = str(self.options.engine)
                else:
                    engine = "duck" # default search engine
                    print("\n- You are setting a non supported search engine. Using default: " + engine + "\n")
            else:
                engine = "duck" # default search engine
            self.extract_ranked(target, engine)
        if not self.url_links: # pass other tests when no urls found by any engine
            if not self.options.allengines:
                print("\n- [" + target + "] -> Not any link found using: "+  engine + "\n")
            if not self.options.nolog: # generate log
                self.report.write("\n***[Info] - [" + target + "] -> Not any link found using: " + engine + "\n\n")
        else:
            for url in self.url_links: # search on results retrieved by all engines used
                if not self.options.social:
                    self.extract_social(url)
                if not self.options.news:
                    self.extract_news(url)
            if self.extract_wikipedia_record == True: # visit directly to wikipedia when is not located any record by search engines
                url_wiki = "https://en.wikipedia.org/wiki/" + str(target).title() # wikipedia default path to extract records
                if self.options.verbose:
                    print("\n[Verbose] - Wikipedia query used: "+ url_wiki + "\n")
                wikipedia = self.extract_wikipedia(str(target).title()) # extract data from wikipedia
                if wikipedia not in self.wikipedia_texts: # not repeat entries
                    self.wikipedia_texts.append(wikipedia)
        self.public_records_output() # output parsed public records
        if not self.options.deep: # search for deep web records
            print("="*14)
            print("*Deep Web*:")
            print("="*14)
            self.search_using_torch(target)

    def extract_whois(self, target): # extract whois data from target domain
        print("="*14)
        print("*Whois*:")
        print("="*14)
        try:
            import whois
            domain = whois.query(target, ignore_returncode=True) # ignore return code
            if domain.creation_date is None: # return when no creation date
                print("- Not found!\n")
                if not self.options.nolog: # generate log
                    self.report.write("- Whois: Not found!\n\n")
                return
        except: # return when fails performing query
            print("- Not found!")
            if not self.options.nolog: # generate log
                self.report.write("- Whois: Not found!\n\n")
            return
        else:
            print("- Domain: " + str(domain.name))
            print("- Registrant: " + str(domain.registrar))
            print("- Creation date: " + str(domain.creation_date))
            print("- Expiration: " + str(domain.expiration_date))
            print("- Last update: " + str(domain.last_updated))
            if not self.options.nolog: # write reply to log
                self.report.write("- Domain: " + str(domain.name) + "\n")
                self.report.write("- Registrant: " + str(domain.registrar) + "\n")
                self.report.write("- Creation date: " + str(domain.creation_date) + "\n")
                self.report.write("- Expiration: " + str(domain.expiration_date) + "\n")
                self.report.write("- Last update: " + str(domain.last_updated) + "\n")
                if self.options.json: # write reply to json
                    self.json_records.append(['Whois',{'Domain': str(domain.name), 'Registrant': str(domain.registrar),'Creation date': str(domain.creation_date),'Expiration': str(domain.expiration_date),'Last update': str(domain.last_updated)}])

    def extract_cvs(self, cve_id, cvs_desc): # write CVE extended detail (description from NVD API)
        if not cvs_desc: # no description available
            return
        print("          "+ cvs_desc) # 10 tab for zen
        if not self.options.nolog: # write reply to log
            self.report.write("          " + cvs_desc + "\n")
            if self.options.json: # write reply to json
                self.json_records.append(['CVS',{'Description': str(cvs_desc)}])

    def extract_cve(self, product): # extract vulnerabilities from NVD (National Vulnerability Database) API 2.0
        if not product or product == "None": # nothing to query
            return
        url = 'https://services.nvd.nist.gov/rest/json/cves/2.0?' + urlencode({'keywordSearch':str(product), 'resultsPerPage':MAX_RESULTS})
        if self.options.verbose:
            print("\n[Verbose] - CVE database query used: "+ url)
        attempt = 0
        data = None
        while attempt < 3:
            try:
                req_reply = self.send_request(url)
                data = json.loads(req_reply)
                break
            except Exception as e:
                attempt = attempt + 1
                if '403' in str(e) or '429' in str(e): # NVD rate limit (~5 req/30s without API key)
                    time.sleep(6 * attempt)
                    continue
                if self.options.verbose:
                    print('\n[Error] - Cannot resolve CVE records...\n')
                return
        if data is None:
            return
        vulns = data.get('vulnerabilities', [])
        if not vulns: # no records found
            print("- Not any record found on CVE database!")
            if not self.options.nolog: # write reply to log
                self.report.write("- Not any record found on CVE database!" + "\n")
            return
        for v in vulns:
            cve = v.get('cve', {})
            cve_id = cve.get('id', '')
            link = "https://nvd.nist.gov/vuln/detail/" + cve_id
            print("\n        + "+ cve_id+ " -> "+ link) # 8 tab for zen
            if not self.options.nolog: # write reply to log
                self.report.write("\n        + " + cve_id + "->" + link + "\n")
                if self.options.json: # write reply to json
                    self.json_records.append(['CVE',{'ID': str(cve_id), 'Link': str(link)}])
            if not self.options.cvs: # extract description from vulnerability (CVS)
                cvs_desc = ""
                for d in cve.get('descriptions', []):
                    if d.get('lang') == 'en':
                        cvs_desc = d.get('value', ''); break
                self.extract_cvs(cve_id, cvs_desc)

    def search_subdomains(self, target): # try to extract subdomains from target domain (1. using search engines)
        # extract subdomains using search engines results (taking data from 'past')
        self.extract_ranked_links = False # use correct subdomains query term on search engines
        print("="*14)
        print("*Subdomains*:")
        print("="*14)
        for engine in self.search_engines:
            self.extract_from_engine(engine, target)
        if not self.sub_links: # not records found
            print("- Not any subdomain found!")
            if not self.options.nolog: # write reply to log
                self.report.write("- Subdomains: Not any found!" + "\n\n")
        else:
            record_s = 0
            short = "." + str(target)
            subdomains = []
            for url in self.sub_links:
                if "www." in url:
                    url = url.replace("www.", "") # remove www.
                if short in url: # subdomain
                    url_s = urlparse(url)
                    subdomain = str(url_s.hostname.split('.')[0] + "." + str(target))
                    if not subdomain in subdomains:
                        subdomains.append(subdomain)
            for s in subdomains:
                print("- " + s)
                if not self.options.nolog: # write reply to log
                    self.report.write("- Subdomain: " + s + "\n")
                    if self.options.json: # write reply to json
                        self.json_records.append(['Subdomains',{'Subdomain': str(s)}])
                record_s = record_s + 1
            if not self.options.nolog: # generate log
                self.report.write("\n") # zen
            if record_s == 0:
                print("- Not any subdomain found!")
                if not self.options.nolog: # write reply to log
                    self.report.write("- Subdomains: Not any found!" + "\n\n")

    def resolve_ip(self, target): # try to resolve an ip from target domain
        data = socket.gethostbyname_ex(target) # reverse resolve target
        for ip in data[2]:
            self.ip = ip
            self.ips_scanner.append(ip) # add to list of scanner found IPs without DNS
            print("- " + str(ip))
            if not self.options.nolog: # write reply to log
                self.report.write("- IP: " + str(ip) + "\n")
                if self.options.json: # write reply to json
                    self.json_records.append(['Server',{'IP': str(ip)}])
        if not self.options.nolog: # generate log
            self.report.write("\n") # zen
        return ip

    def scan_target(self, target): # try to discover Open Ports
        if self.options.scanner: # safe/return when no scanning option
            return
        import nmap
        open_ports = 0 # open ports counter
        if not self.options.proto:
            proto = "TCP+UDP"
        else:
            proto = "TCP"
        nm = nmap.PortScanner()
        if self.options.ports:
            ports = self.options.ports
        else:
            ports = '1-65535' # scanning all ports by default (1-65535)
        if proto == "TCP": # scan TCP ports (TCP connect()+Service scan)   
            nm.scan(str(target), str(ports), arguments='-sT -sV', sudo=False)
            if self.options.verbose:
                print("-Using: "+ nm.command_line())
        elif proto == "TCP+UDP": # scan TCP+UDP ports (NoPing+Service scan)
            nm.scan(str(target), str(ports), arguments='-PN -sV', sudo=False)
            if self.options.verbose:
                print("-Using: "+ nm.command_line())
        for host in nm.all_hosts():
            print('\n   * Host : %s' % host)
            if not self.options.nolog: # write reply to log
                self.report.write('\n   * Host : ' + str(host) + "\n")
            print('   * State : %s' % nm[host].state())
            if not self.options.nolog: # write reply to log
                self.report.write('   * State : ' + str(nm[host].state()) + "\n")
            for proto in nm[host].all_protocols():
                print('    - Protocol : %s' % proto)
                if not self.options.nolog: # write reply to log
                    self.report.write("    - Protocol: " + proto + "\n")
                    if self.options.json: # write json report
                        self.json_records.append(['Scanner',{'Protocol': str(proto)}])
                lport = list(nm[host][proto].keys())
                lport.sort()
                for port in lport:
                    if not self.options.banner: # extract banners from services discovered
                        if str(nm[host][proto][port]['state']) == "open": # results open ports+banner
                            print("      + Port: "+ str(port)+ " (", nm[host][proto][port]['state']+ ") -", nm[host][proto][port]['product']+ " | "+ nm[host][proto][port]['version']+ nm[host][proto][port]['name']+ nm[host][proto][port]['extrainfo']+ nm[host][proto][port]['cpe'])
                            if not self.options.nolog: # write reply to log
                                self.report.write("      + Port:" + str(port) + "(" + str(nm[host][proto][port]['state']) + ") - " +  str(nm[host][proto][port]['product']) + str(nm[host][proto][port]['version']) + str(nm[host][proto][port]['name']) + str(nm[host][proto][port]['extrainfo']) + str(nm[host][proto][port]['cpe']) + "\n")
                                if self.options.json: # write json report
                                    self.json_records.append(['Scanner',{'Port': str(port), 'State': str(nm[host][proto][port]['state']), 'Version': str(nm[host][proto][port]['version']), 'Name': str(nm[host][proto][port]['name']), 'Info': str(nm[host][proto][port]['extrainfo']), 'CPE': str(nm[host][proto][port]['cpe'])}])
                            open_ports = open_ports + 1
                            if not self.options.cve: # extract vulnerabilities from CVE (Common Vulnerabilities and Exposures)
                                product = str(nm[host][proto][port]['product'])
                                cve = self.extract_cve(product)
                                print("") # zen output
                    else: # not extract banners
                        if str(nm[host][proto][port]['state']) == "open": # only results when open port
                            print("      + Port: "+ str(port)+ " ("+ nm[host][proto][port]['state']+ ") ")
                            if not self.options.nolog: # write reply to log
                                self.report.write("     + Port:" + str(port) + "(" + str(nm[host][proto][port]['state']) + ")")
                                if self.options.json: # write json report
                                    self.json_records.append(['Scanner',{'Port': str(port), 'State': str(nm[host][proto][port]['state'])}])
                            open_ports = open_ports + 1
                        if self.options.filtered: # add filtered ports to results
                            if str(nm[host][proto][port]['state']) == "filtered": # results filtered ports (no banners)
                                print("      + Port: "+ str(port)+ " ("+ nm[host][proto][port]['state']+ ") ")
                                if not self.options.nolog: # write reply to log
                                    self.report.write("     + Port:" + str(port) + "(" + str(nm[host][proto][port]['state']) + ")")
                                    if self.options.json: # write json report
                                        self.json_records.append(['Scanner',{'Port': str(port), 'State': str(nm[host][proto][port]['state'])}])
                if not open_ports > 0:
                    print("\n- Not any open port found!")
                    if not self.options.nolog: # write reply to log
                        self.report.write("\n- Not any open port found + \n\n")

    def resolve_dns(self, target): # try to discover DNS records + perform portscanning
        import dns.resolver
        resolver = dns.resolver.Resolver()
        if self.options.resolv: # use DNS resolver provided by user
            resolvers = str(self.options.resolv)
            resolvers = resolvers.split(",")
            resolver.nameservers = resolvers
            if self.options.verbose:
                print("[Verbose] - Using DNS resolvers: [" + self.options.resolv + "]\n")
        else: # use default Google Inc. DNS resolvers (8.8.8.8, 8.8.4.4)
            resolver.nameservers = ['8.8.8.8', '8.8.4.4'] # google DNS resolvers
            if self.options.verbose:
                print("[Verbose] - Using DNS resolvers: [8.8.8.8, 8.8.4.4]\n")
        try:
            answers = resolver.resolve(target, "A") # A records
            for rdata in answers:
                print("- [A]: "+ str(rdata))
                self.dns_Amachines.append(rdata)
                if not self.options.nolog: # write reply to log
                    self.report.write("- DNS [A]: " + str(rdata) + "\n")
                    if self.options.json: # write json report
                        self.json_records.append(['DNS',{'A': str(rdata)}])
                if not self.options.scanner: # try port-scanner on DNS-A records
                    if not self.options.scandns:
                        scanner = self.scan_target(rdata)
            print("-"*12)
            if not self.options.nolog: # write reply to log
                self.report.write("-"*12 + "\n")
        except:
            pass
        try:
            answers = resolver.resolve(target, "NS") # NS records
            for rdata in answers:
                rdata = str(rdata) # NS records ends with "." (removing)
                rdata = rdata[:-1]
                data = socket.gethostbyname_ex(rdata) # reverse resolve NS server
                for ip in data[2]:
                    self.ip = ip
                print("- [NS]: "+ rdata+ " (" + str(self.ip) + ") ")
                if not self.options.nolog: # write reply to log
                    self.report.write("- DNS [NS]: " + str(rdata) + "(" + str(self.ip) + ")" + "\n")
                    if self.options.json: # write json report
                        self.json_records.append(['DNS',{'NS': str(rdata)}])
                if not self.options.scanner:
                    if not self.options.scandns:
                        if not self.options.scanns: # try port-scanner on DNS-NS records
                            scanner = self.scan_target(rdata)
            print("-"*12)
            if not self.options.nolog: # write reply to log
                self.report.write("-"*12 + "\n")
        except:
            pass
        try:
            answers = resolver.resolve(target, "MX") # MX records
            for rdata in answers:
                rdata = str(rdata) # MX records ends with "." (removing)
                rdata = rdata[:-1]
                rdata = rdata.replace("10 ", "") # MX records starts with "10 " (removing)
                data = socket.gethostbyname_ex(rdata) # reverse resolve MX server (mailserver)
                for ip in data[2]:
                    self.ip = ip
                print("- [MX]: "+ rdata+ " (" + str(self.ip) + ") ")
                if not self.options.nolog: # write reply to log
                    self.report.write("- DNS [MX]: " + str(rdata) + "(" + str(self.ip) + ")" + "\n")
                    if self.options.json: # write json report
                        self.json_records.append(['DNS',{'MX': str(rdata)}])
                if not self.options.scanner: # try port-scanner on DNS-MX records
                    if not self.options.scandns:
                        if not self.options.scanmx:
                            scanner = self.scan_target(rdata)
            print("-"*12)
            if not self.options.nolog: # write reply to log
                self.report.write("-"*12 + "\n")
        except: #pass when no MX records
            pass
        try:
            answers = resolver.resolve(target, "TXT") # TXT records
            for rdata in answers:
                print("- [TXT]: "+ str(rdata))
                if not self.options.nolog: # write reply to log
                    self.report.write("- DNS [TXT]: " + str(rdata) + "\n")
                    if self.options.json: # write json report
                        self.json_records.append(['DNS',{'TXT': str(rdata)}])
            print("-"*12)
            if not self.options.nolog: # write reply to log
                self.report.write("-"*12 + "\n")
        except: #pass when no TXT records
            pass

    def run(self, opts=None):
        if opts:
            options = self.create_options(opts)
            self.set_options(options)
        options = self.options
        if not self.options.gui: # generate report when no gui
            self.banner()
        # list supported search engines
        if options.listengines:
            print("\nSearch engines supported:\n")
            print('-'*25)
            for e in self.search_engines:
                print("+ "+e)
            print('-'*25 + "\n")
            sys.exit(2)
        # check tor connection
        if options.checktor:
            try:
                print("\nSending request to: https://check.torproject.org\n")
                tor_reply = urllib.request.urlopen("https://check.torproject.org").read().decode('utf-8')
                your_ip = tor_reply.split('<strong>')[1].split('</strong>')[0].strip()
                if not tor_reply or 'Congratulations' not in tor_reply:
                    print("It seems that Tor is not properly set.\n")
                    print("Your IP address appears to be: " + your_ip + "\n")
                else:
                    print("Congratulations!. Tor is properly being used :-)\n")
                    print("Your IP address appears to be: " + your_ip + "\n")
            except:
                print("Cannot reach TOR checker system!. Are you correctly connected?\n")
            sys.exit(2)
        # check/update for latest stable version
        if options.update:
            self.banner()
            try:
                print("\nTrying to update automatically to the latest stable version\n")
                Updater() 
            except:
                print("Not any .git repository found!\n")
                print("="*30)
                print("\nTo have working this feature, you should clone Orb with:\n")
                print("$ git clone %s" % self.GIT_REPOSITORY)
                print("\nAlso you can try this other mirror:\n")
                print("$ git clone %s" % self.GIT_REPOSITORY2 + "\n")
        # logging / reporting
        if not options.nolog: # generate log
            self.generate_report()
            if options.json: # generate json report
                self.generate_json()
        # footprinting (only passive)
        if options.passive:
            self.options.scanner = True # not scan ports on machines
            self.options.scandns = True # not scan on DNS records
            self.options.scanns = True # not scan on NS records
            self.options.scanmx = True # not scan on MX records
            self.options.banner = True # not banner grabbing
            self.options.cve = True # not CVE
            self.options.cvs = True # not CVS
        # footprinting (only active)
        if options.active:
            self.options.public = True # not search for public records
            self.options.deep = True # not search for deep web records
            self.options.social = True # not search for social records
            self.options.news = True # not search for news records
            self.options.whois = True # not extract whois information
            self.options.subs = True # not try to discover subdomains (with passive methods) / bruteforce ¿next release? :)
        # footprinting (full) / by default
        if options.target:
            # public records / deepweb, social, news ...
            if not options.public: # search for public records
                print("="*60)
                print("[Info] - Retrieving general data ...")
                print("="*60)
                if not options.social: # retrieve social urls
                    if not options.socialf: # try default list
                        f = open('core/sources/social.txt')
                    else: # extract social links from list provided by user
                        try:
                            f = open(options.socialf)
                        except:
                            if os.path.exists(options.socialf) == True:
                                print('[Error] - Cannot open: '+ options.socialf+ "\n")
                                return
                            else:
                                print('[Error] - Cannot found: '+ options.socialf+ "\n")
                                return
                    self.socials = f.readlines()
                    self.socials = [ social.replace('\n','') for social in self.socials ]
                    f.close()
                if not options.news: # retrieve news urls
                    if not options.newsf: # try default list
                        f = open('core/sources/news.txt')
                    else: # extract social news from list provided by user
                        try:
                            f = open(options.newsf)
                        except:
                            if os.path.exists(options.newsf) == True:
                                print('[Error] - Cannot open: '+ options.newsf+ "\n")
                                return
                            else:
                                print('[Error] - Cannot found: '+ options.newsf+ "\n")
                                return
                    self.news = f.readlines()
                    self.news = [ new.replace('\n','') for new in self.news ]
                    f.close()
                public = self.extract_public(options.target)
                if not options.nolog: # generate log
                    self.report.write("-"*22 + "\n")
            # domains / extract extensions from source provided (comma separated)
            print("="*60)
            print("[Info] - Retrieving data by TLDs ...")
            print("="*60)
            tld_record = False # tld records
            self.extract_wikipedia_record = False
            if options.ext: # by user
                extensions = [str(options.ext)]
                extensions = options.ext.split(",")
                print("\n[Info] - Using extensions provided by user...\n")
            elif options.extfile: # from file
                try:
                    print("\n[Info] - Extracting extensions from file...\n")
                    f = open(options.extfile)
                    extensions = f.readlines()
                    extensions = [ ext.replace('\n','') for ext in extensions ]
                    f.close()
                    if not extensions:
                        print("[Error] - Cannot extract 'extensions' from file.\n")
                        return
                except:
                    if os.path.exists(options.extfile) == True:
                        print('[Error] - Cannot open: '+ options.extfile+ "\n")
                        return 
                    else:
                        print('[Error] - Cannot found: '+ options.extfile+ "\n")
                        return
            else: # IANA (default) original + country (09/03/2016)
                print("\n[Info] - Using extensions supported by IANA...\n")
                f = open("core/sources/iana-exts.txt") # extract IANA list provided by default
                extensions = f.readlines()
                extensions = [ ext.replace('\n','') for ext in extensions ]
                f.close()
                if not extensions:
                    print("[Error] - Cannot extract 'IANA extensions' from file.\n")
                    return
            for e in extensions: # extract domain info and perform different tasks
                target = str(options.target + e)
                print("="*40)
                print("[Info] - Trying TLD: "+ target)
                print("="*40)
                # public records (by extension)
                if not options.public: # search for public records
                    # clear previous data to reuse containers
                    self.url_links[:] = [] # clear a list / black magic!
                    self.top_ranked.clear() # clear top ranked dict
                    self.social_links.clear() # clear social dict
                    self.news_links.clear() # clear news dict
                    public = self.extract_public(target)
                # whois
                if not options.whois: # try to extract whois data
                    if options.verbose:
                        print("\n[Verbose] - Trying whois to: " + target + "\n")
                    whois = self.extract_whois(target)
                # subdomains
                if not options.subs: # try to discover subdomains on target domain
                    if options.verbose:
                        print("\n[Verbose] - Trying to resolve subdomains for: "+ target+ "\n")
                    self.sub_links[:] = [] # clear subs list
                    try:
                        subdomains = self.search_subdomains(target)
                    except:
                        print("- Not any subdomain found using TLD: "+ target)
                        if not options.nolog: # generate log
                            self.report.write("- Subdomains: Not any subdomain found using TLD provided: " + target + "\n\n")
                            if options.json: # generate json
                                self.json_records.append(['Subdomains',{target: 'not any subdomain found'}])
                # ip
                print("="*14)
                print("*IP*:")
                print("="*14)
                if options.verbose:
                    print("\n[Verbose] - Trying to resolve IP for: "+ target+ "\n")
                try:
                    ip = self.resolve_ip(target) # try to resolve an ip from target domain
                    tld_record = True
                except:
                    print("- Not any IP found using TLD: "+ target+"\n")
                    if not options.nolog: # generate log
                        self.report.write("- IP: Not any IP found using TLD provided: " + target + "\n\n")
                        if options.json: # generate json
                            self.json_records.append(['TLD',{target: 'not any IP found'}])
                    tld_record = False
                # dns + scanning
                if not options.dns: # try to discover DNS records
                    print("="*14)
                    print("*DNS records*:")
                    print("="*14)
                    if options.verbose:
                        print("\n[Verbose] - Trying to resolve DNS records for: "+ target+ "\n")
                    try:
                        dns = self.resolve_dns(target)
                    except:
                        print("- Not any DNS record found using TLD: "+ target)
                        if not options.nolog: # generate log
                            self.report.write("- DNS: Not any DNS record found using TLD provided: " + target + "\n\n")
                            if options.json: # generate json
                                self.json_records.append(['DNS',{target: 'not any DNS record found'}])
                # rest of scanning tasks (when ip != DNS[A])
                if not options.scanner and tld_record == True: # try port-scanner on IP
                    if not options.dns: # using DNS A
                        for Amachine in self.dns_Amachines:
                            if str(Amachine) == str(ip):
                                if not options.scandns: # pass when DNS was scanned                               
                                    pass
                                else:
                                    print("[Info] - Trying to discover open ports on: "+ ip+ "\n")
                                    scanner = self.scan_target(ip)
                            else:
                                print("[Info] - Trying to discover open ports on: "+ ip+ "\n")
                                scanner = self.scan_target(ip)
                    else: # only IP test
                        for ip in self.ips_scanner: # scan all ips found without DNS
                            if options.verbose:
                                print("\n[Verbose] - Trying to discover open ports on: "+ ip+ "\n")
                            scanner = self.scan_target(ip)
                print("") # zen output extensions separator
                if not options.nolog:
                    self.report.write("-"*22 + "\n")
            if not options.nolog: # close log (.raw)
                self.report.close()
                if options.json: # close json
                    self.json_report.write(json.dumps(self.json_records, separators=(',', ':'), ensure_ascii=False))
                    self.json_report.close()
        # start web-gui
        if options.gui:
            host = '0.0.0.0' # local network
            port = 9999 # local port
            webbrowser.open('http://127.0.0.1:9999', new=1)
            tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            tcpsock.bind((host, port))
            while True:
                tcpsock.listen(4)
                (clientsock, (ip, c_port)) = tcpsock.accept()
                newthread = ClientThread(ip, c_port, clientsock)
                newthread.start()

if __name__ == "__main__":
    app = Orb()
    options = app.create_options()
    if options:
        app.set_options(options)
        app.run()
