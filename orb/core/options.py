#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
"""
This file is part of the orb project, https://orb.03c8.net

Orb - 2016/2026 - by psy (epsylon@riseup.net)

You should have received a copy of the GNU General Public License along
with Orb; if not, write to the Free Software Foundation, Inc., 51
Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import optparse

class OrbOptions(optparse.OptionParser):
    def __init__(self, *args):
        optparse.OptionParser.__init__(self, 
                           description='\nOrb: massive footprinting tool - by psy (https://03c8.net)',
                           prog='Orb.py',
                           version='\nVersion: v0.4 (2026) - "Yellow Orb! - https://orb.03c8.net"\n')
        self.add_option("-v", "--verbose", action="store_true", dest="verbose", help="active verbose on requests")
        self.add_option("--check-tor", action="store_true", dest="checktor", help="check to see if Tor is used properly")
        self.add_option("--update", action="store_true", dest="update", help="check for latest stable version")
        self.add_option("--spell", action="store", dest="target", help="start complete footprinting on this target")
        self.add_option("--gui", action="store_true", dest="gui", help="run GUI (Orb Web Interface)")
        self.add_option("--delay", action="store", dest="delay", help="set delay in seconds between requests (default: 1)")

        group10 = optparse.OptionGroup(self, "*Methods*",
        "These options can be used to set some footprinting interaction restrictions with target(s). You only can set one:")
        group10.add_option("--passive", action="store_true", dest="passive", help="use only -passive- methods")
        group10.add_option("--active", action="store_true", dest="active", help="use only -active- methods")
        self.add_option_group(group10)

        group1 = optparse.OptionGroup(self, "*Search Engines*",
        "These options can be used to specify which search engines use to extract information:")
        group1.add_option("--se", action="store", dest="engine", help="set search engine (default: DuckDuckGo)")
        group1.add_option("--se-ext", action="store", dest="engineloc", help="set location for search engine (ex: 'fr')")
        group1.add_option("--sa", action="store_true", dest="allengines", help="search massively using all search engines")
        group1.add_option("--list-engines", action="store_true", dest="listengines", help="list all supported search engines")
        self.add_option_group(group1)

        group2 = optparse.OptionGroup(self, "*Public*", 
        "Orb will search for interesting public records. You can choose multiple:")
        group2.add_option("--no-public", action="store_true", dest="public", help="disable search for public records")
        group2.add_option("--no-deep", action="store_true", dest="deep", help="disable deep web records") 
        group2.add_option("--no-social", action="store_true", dest="social", help="disable social records")
        group2.add_option("--social-f", action="store", dest="socialf", help="set a list of social sources from file")
        group2.add_option("--no-news", action="store_true", dest="news", help="disable news records")
        group2.add_option("--news-f", action="store", dest="newsf", help="set a list of news sources from file")
        self.add_option_group(group2)

        group3 = optparse.OptionGroup(self, "*Domains*",
        "Orb will search on different databases for registered domains using IANA supported by default. You only can set one:")  
        group3.add_option("--ext", action="store", dest="ext", help="set extensions manually (ex: --ext='.com,.net,.es')")
        group3.add_option("--ext-f", action="store", dest="extfile", help="set a list of extensions from file")
        self.add_option_group(group3)

        group4 = optparse.OptionGroup(self, "*Whois*",
        "Orb will search on 'Whois' records for registrant information:")            
        group4.add_option("--no-whois", action="store_true", dest="whois", help="disable extract whois information")
        self.add_option_group(group4)

        group5 = optparse.OptionGroup(self, "*Subdomains*",
        "Orb will try to discover info about subdomains:")   
        group5.add_option("--no-subs", action="store_true", dest="subs", help="disable try to discover subdomains")
        self.add_option_group(group5)

        group6 = optparse.OptionGroup(self, "*DNS*",
        "Orb will try to discover info about DNS records and machines running them. You can choose multiple:")
        group6.add_option("--no-dns", action="store_true", dest="dns", help="disable try to discover DNS records")
        group6.add_option("--resolver", action="store", dest="resolv", help="specify custom DNS servers (ex: '8.8.8.8,8.8.8.4')")
        self.add_option_group(group6)

        group7 = optparse.OptionGroup(self, "*Port Scanning*",
        "These options can be used to specify how to perfom port scanning tasks. You can choose multiple:")
        group7.add_option("--no-scanner", action="store_true", dest="scanner", help="disable scanner")
        group7.add_option("--no-scan-dns", action="store_true", dest="scandns", help="disable scan DNS machines")
        group7.add_option("--no-scan-ns", action="store_true", dest="scanns", help="disable scan NS records")
        group7.add_option("--no-scan-mx", action="store_true", dest="scanmx", help="disable scan MX records")
        group7.add_option("--scan-tcp", action="store_true", dest="proto", help="set scanning protocol to only TCP (default TCP+UDP)")
        group7.add_option("--scan-ports", action="store", dest="ports", help="set range of ports to scan (default 1-65535)")
        group7.add_option("--show-filtered", action="store_true", dest="filtered", help="show 'filtered' ports on results")
        self.add_option_group(group7)

        group8 = optparse.OptionGroup(self, "*Banner grabbing*",
        "Orb will try to extract interesting information about services running on machines discovered (ex: OS, vendor, version, cpe, cvs):")
        group8.add_option("--no-banner", action="store_true", dest="banner", help="disable extract banners from services")
        group8.add_option("--no-cve", action="store_true", dest="cve", help="disable extract vulnerabilities from CVE")
        group8.add_option("--no-cvs", action="store_true", dest="cvs", help="disable extract CVS description")
        self.add_option_group(group8)

        group9 = optparse.OptionGroup(self, "*Reporting*",
        "These options can be used to specify exporting methods for your results. You can choose multiple:")
        group9.add_option("--no-log", action="store_true", dest="nolog", help="disable generate reports")
        group9.add_option("--json", action="store", dest="json", help="generate json report (ex: --json='foo.json')")
        self.add_option_group(group9)

    def banner(self):
        print('='*75)
        print("")
        print("  _|_|              _|        ")
        print("_|    _|  _|  _|_|  _|_|_|    ")
        print("_|    _|  _|_|      _|    _|  ")
        print("_|    _|  _|        _|    _|  ")
        print("  _|_|    _|        _|_|_|    ")
        print("")
        print(" Orb: massive footprinting tool - 2016/2026 - by psy (https://03c8.net)")
        print("")
        print(' + Version : v0.4 (2026) - "Yellow Orb!"')
        print(" + Website : https://orb.03c8.net")
        print(" + Code    : https://github.com/epsylon/orb")
        print(" + License : GNU General Public License v3 (GPLv3)")
        print("")
        print('='*75)

    def get_options(self, user_args=None):
        (options, args) = self.parse_args(user_args)
        if (not options.checktor and not options.target and not options.gui and not options.update and not options.listengines):
            print("")
            self.banner()
            print("")
            return False
        return options
