#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
"""
This file is part of the orb project, https://orb.03c8.net

Orb - 2016/2026 - by psy (epsylon@riseup.net)

You should have received a copy of the GNU General Public License along
with Orb; if not, write to the Free Software Foundation, Inc., 51
Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import socket, threading, re, os
import subprocess, sys
import urllib.parse as urlparse
from .options import OrbOptions

host = "0.0.0.0"
port = 9999

class ClientThread(threading.Thread):
    def __init__(self, ip, port, socket):
        threading.Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.socket = socket
        self.pages = Pages()

    def run(self):
        req = self.socket.recv(8192)
        res = self.pages.get(req)
        if res is None:
            self.socket.close()
            return
        out = "HTTP/1.0 %s\r\n" % res["code"]
        out += "Content-Type: %s\r\n\r\n" % res["ctype"]
        out += "%s" % res["html"]
        try:
            self.socket.send(out.encode('utf-8'))
        except:
            self.socket.send(out)
        self.socket.close()
        if "run" in res and len(res["run"]):
            subprocess.Popen(res["run"], shell=True)

class Pages():

    def __init__(self):
        self.options = OrbOptions()
        self.pages = {}

        self.pages["/header"] = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<link rel="icon" type="image/ico" href="data:image/ico;base64,AAABAAEAEBAAAAEAIABoBAAAFgAAACgAAAAQAAAAIAAAAAEAIAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABQIDA6sBX9r/AWrk/wFn4f8BXdb/AzR/5AAAAA8AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYgKY/f8BRbL/ASBR/wEKFP8BCRH/ARtD/wE9pP8DnP3/AQAAjwAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAZgFz6/8BM4z/AR1F/wEPH/8BBgv/AQMF/wELGf8BGTv/ATCA/wFm4v8EHkG7AAAAAAAAAAAAAAAAAAAABwF98f8BMYH/ARtD/wIMGv8DBQj/AwYK/wQHC/8DBgn/AgoU/wEYOf8BMH3/AWXh/wAAACUAAAAAAAAAAAFRx/4BMoX/ARxF/wINGv8DBgv/CRAY/w8ZKf8QGyv/ChMd/wQJD/8CCxX/ARpA/wEvfP8BUcb/AAAAAAAAAAABUMj/AR9L/wESJf8DCA//CRAY/xkwTf8uWpT/MWCd/x86X/8MFSH/BAkP/wERJP8BHUb/AT+k/wAAAAEAAAABASVe/wEVMv8BChb/BAgO/xIgMv81aKf/ZLzt/2vE8/9BgsL/FyxG/wYMEv8CCxX/ARUx/wEfTP8AAAAWAAAAAgEWNP8BDx3/AgkQ/wUJDv8VJz3/QYLC/33U+v+G2/3/UJ7Z/x02V/8IDRX/AggQ/wEPIP8BFCv/AAEBHQAAAAABDBr/AQwZ/wEHDf8EBwv/EB0s/y5Zk/9VqOH/XLHn/zhvr/8VJj3/BgsR/wIGDP8BChP/ARQw/wAAAAQAAAAAAQwY/wESJf8BBAj/AwQH/wcNE/8UJDn/I0Nt/yVHdf8XLEb/ChEZ/wMGCf8BBQj/AQsY/wEHDP8AAAAAAAAAAAISI4EBQq3/AQUI/wEDA/8CAwX/BQoP/woRGf8KEhv/BgwR/wMEB/8CAwT/AQME/wEwgv8BCxX/AAAAAAAAAAAAAAAAAUrA/wEqbf8BAQL/AAEB/wECA/8CAwT/AgME/wIDA/8AAQH/AAAA/wEdSf8EgfL/AAAAAAAAAAAAAAAAAAAAAAAAAABA4/3/AUzA/wEHDf8AAAD/AAAA/wAAAP8AAAD/AQQH/wE6n/9c6v3/AAAAAQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAADiz8f97/f//AZL8/wFRyP8BTsP/AYX1/172//9dzfn/AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAGrK/Gml5///s+r//2/R+9MAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA+B8AAPAHAADgAwAAwAMAAIABAACAAQAAgAEAAIABAACAAQAAgAEAAIABAADAAwAA4AcAAPAPAAD+PwAA//8AAA==">
<title>Orb - footprinting tool</title>
<style>
  :root{
    --bg:#0a0e14; --panel:#121a25; --panel2:#0d131c; --border:#1e2a3a;
    --fg:#e6ecf3; --dim:#8b97a8; --accent:#ffb020; --accent2:#ffd24a; --green:#43d17a;
    --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,"Liberation Mono",monospace;
    --sans:system-ui,-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;
  }
  *{box-sizing:border-box}
  body{margin:0;background:var(--bg);color:var(--fg);font-family:var(--sans);line-height:1.5}
  a{color:var(--accent2);text-decoration:none}
  header{padding:16px 22px;border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between;gap:14px;
    background:radial-gradient(600px 120px at 0% -40%, rgba(255,176,32,.15), transparent 70%)}
  header .brand{font-size:1.8rem;font-weight:900;letter-spacing:2px;color:var(--fg);text-decoration:none;line-height:1}
  header .brand:hover{color:var(--accent)}
  header .brand b{color:var(--accent)}
  header .sub{color:var(--dim);font-size:.9rem;margin-top:4px}
  header .meta{text-align:right;font-size:.78rem;color:var(--dim);line-height:1.6}
  header .meta .lic{color:var(--accent2)}
  .layout{display:grid;grid-template-columns:400px 1fr;gap:0;min-height:calc(100vh - 62px)}
  .controls{border-right:1px solid var(--border);padding:20px;overflow-y:auto;max-height:calc(100vh - 62px)}
  label{display:block;font-size:.78rem;text-transform:uppercase;letter-spacing:.5px;color:var(--dim);margin:14px 0 5px}
  input[type=text],input[type=number],select{width:100%;background:var(--panel2);border:1px solid var(--border);
    color:var(--fg);border-radius:7px;padding:9px 11px;font-family:var(--mono);font-size:.9rem}
  input:focus,select:focus{outline:none;border-color:var(--accent)}
  .row{display:flex;gap:10px}
  .row>div{flex:1}
  .methods{display:flex;gap:8px;margin-top:6px}
  .methods label{flex:1;margin:0;text-transform:none;letter-spacing:0;color:var(--fg);font-size:.85rem;
    text-align:center;background:var(--panel2);border:1px solid var(--border);border-radius:7px;
    padding:8px 4px;cursor:pointer}
  .methods input{display:none}
  .methods input:checked+span{color:var(--accent);font-weight:700}
  button.run{width:100%;margin-top:18px;padding:12px;border:none;border-radius:8px;cursor:pointer;
    font-weight:800;font-size:1rem;letter-spacing:1px;color:#1a1204;
    background:linear-gradient(180deg,var(--accent2),var(--accent))}
  button.run:hover{filter:brightness(1.08)}
  details{border:1px solid var(--border);border-radius:8px;margin-top:12px;background:var(--panel2)}
  summary{cursor:pointer;padding:11px 13px;font-weight:600;font-size:.9rem;list-style:none}
  summary::-webkit-details-marker{display:none}
  summary::before{content:"+ ";color:var(--accent)}
  details[open] summary::before{content:"- "}
  .box{padding:2px 13px 13px}
  .chk{display:flex;align-items:center;gap:8px;margin:8px 0;font-size:.88rem;color:var(--fg)}
  .chk input{accent-color:var(--accent);width:16px;height:16px}
  .console{display:flex;flex-direction:column;min-width:0}
  .console-head{padding:12px 18px;border-bottom:1px solid var(--border);font-family:var(--mono);
    font-size:.82rem;color:var(--dim);display:flex;justify-content:space-between;align-items:center}
  .console-head #status{color:var(--accent2)}
  #cmdOut{flex:1;margin:0;padding:18px;overflow:auto;background:#070b10;color:#cdd7e3;
    font-family:var(--mono);font-size:.85rem;white-space:pre-wrap;word-break:break-word}
  @media(max-width:820px){.layout{grid-template-columns:1fr}.controls{max-height:none;border-right:none;
    border-bottom:1px solid var(--border)}#cmdOut{min-height:50vh}}
</style>
</head>
<body>
<script src="/lib.js"></script>
"""

        self.pages["/footer"] = """</body>
</html>
"""

        self.pages["/"] = self.pages["/header"] + """
<header>
  <div>
    <a class="brand" href="https://orb.03c8.net" target="_blank" rel="noopener">Or<b>b</b></a>
    <div class="sub">massive footprinting tool</div>
  </div>
  <div class="meta">
    <div class="lic">GNU General Public License v3</div>
    <div class="by">2016 / 2026 &mdash; by <a href="https://03c8.net" target="_blank" rel="noopener">psy</a></div>
  </div>
</header>
<div class="layout">
  <form class="controls" onsubmit="return false">
    <label for="target">Target</label>
    <input type="text" id="target" placeholder="microsoft, instagram ..." autofocus>
    <label for="extens">TLD extension(s)</label>
    <input type="text" id="extens" value=".com,.net" title="comma separated (ex: .com,.net,.es)">
    <div class="methods">
      <label><input type="radio" name="method" value="both" checked><span>Both</span></label>
      <label><input type="radio" name="method" value="passive"><span>Passive</span></label>
      <label><input type="radio" name="method" value="active"><span>Active</span></label>
    </div>
    <button type="button" class="run" onclick="Start()">SPELL</button>

    <details open>
      <summary>Search engines</summary>
      <div class="box">
        <label for="se">Engine</label>
        <select id="se">
          <option value="">duck (default)</option>
          <option value="bing">bing</option>
          <option value="brave">brave</option>
          <option value="mojeek">mojeek</option>
          <option value="yahoo">yahoo</option>
          <option value="startpage">startpage</option>
          <option value="ecosia">ecosia</option>
        </select>
        <div class="chk"><input type="checkbox" id="sa"><label for="sa" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">Use all engines (--sa)</label></div>
        <div class="row">
          <div><label for="engineloc">Location</label><input type="text" id="engineloc" placeholder="es, fr ..."></div>
          <div><label for="delay">Delay (s)</label><input type="number" id="delay" value="1" min="0" step="1"></div>
        </div>
      </div>
    </details>

    <details>
      <summary>Public records</summary>
      <div class="box">
        <div class="chk"><input type="checkbox" id="nopublic"><label for="nopublic" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No public records</label></div>
        <div class="chk"><input type="checkbox" id="nodeep"><label for="nodeep" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No deep web</label></div>
        <div class="chk"><input type="checkbox" id="nosocial"><label for="nosocial" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No social</label></div>
        <div class="chk"><input type="checkbox" id="nonews"><label for="nonews" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No news</label></div>
        <div class="chk"><input type="checkbox" id="nowhois"><label for="nowhois" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No whois</label></div>
        <div class="chk"><input type="checkbox" id="nosubs"><label for="nosubs" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No subdomains</label></div>
        <div class="chk"><input type="checkbox" id="nodns"><label for="nodns" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No DNS records</label></div>
      </div>
    </details>

    <details>
      <summary>Port scanning</summary>
      <div class="box">
        <div class="chk"><input type="checkbox" id="noscanner"><label for="noscanner" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No scanner</label></div>
        <label for="scanports">Ports</label>
        <input type="text" id="scanports" value="1-65535" title="range or list (ex: 1-1024 or 22,80,443)">
        <div class="chk"><input type="checkbox" id="scantcp"><label for="scantcp" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">TCP only</label></div>
        <div class="chk"><input type="checkbox" id="showfiltered"><label for="showfiltered" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">Show filtered ports</label></div>
        <div class="chk"><input type="checkbox" id="noscandns"><label for="noscandns" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No scan DNS machines</label></div>
        <div class="chk"><input type="checkbox" id="noscanns"><label for="noscanns" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No scan NS</label></div>
        <div class="chk"><input type="checkbox" id="noscanmx"><label for="noscanmx" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No scan MX</label></div>
      </div>
    </details>

    <details>
      <summary>Banner grabbing</summary>
      <div class="box">
        <div class="chk"><input type="checkbox" id="nobanner"><label for="nobanner" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No banners</label></div>
        <div class="chk"><input type="checkbox" id="nocve"><label for="nocve" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No CVE lookups</label></div>
        <div class="chk"><input type="checkbox" id="nocvs"><label for="nocvs" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">No CVS descriptions</label></div>
      </div>
    </details>

    <details>
      <summary>Report</summary>
      <div class="box">
        <div class="chk"><input type="checkbox" id="json"><label for="json" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">Generate JSON report</label></div>
        <div class="chk"><input type="checkbox" id="autoscroll" checked><label for="autoscroll" style="margin:0;text-transform:none;letter-spacing:0;color:var(--fg)">Auto-scroll output</label></div>
      </div>
    </details>
  </form>

  <section class="console">
    <div class="console-head"><span>output</span><span id="status">idle</span></div>
    <pre id="cmdOut">Set a target and press SPELL to start ...</pre>
  </section>
</div>
""" + self.pages["/footer"]

        self.pages["/lib.js"] = """
var polling = false;
function val(id){var e=document.getElementById(id);return e?e.value:"";}
function chk(id){var e=document.getElementById(id);return (e&&e.checked)?"on":"off";}
function method(){var r=document.getElementsByName("method");for(var i=0;i<r.length;i++){if(r[i].checked)return r[i].value;}return "both";}
function strip(t){return t.replace(/<\\/?pre>/g,"");}
function Start(){
  var t = val("target").trim();
  if(t===""){document.getElementById("status").textContent="enter a target!";return;}
  var p = "target="+encodeURIComponent(t);
  p += "&method="+method();
  p += "&se="+encodeURIComponent(val("se"));
  p += "&engineloc="+encodeURIComponent(val("engineloc"));
  p += "&delay="+encodeURIComponent(val("delay"));
  p += "&extens="+encodeURIComponent(val("extens"));
  p += "&scanports="+encodeURIComponent(val("scanports"));
  var flags = ["sa","nopublic","nodeep","nosocial","nonews","nowhois","nosubs","nodns","noscanner","scantcp","showfiltered","noscandns","noscanns","noscanmx","nobanner","nocve","nocvs","json"];
  for(var i=0;i<flags.length;i++){p += "&"+flags[i]+"="+chk(flags[i]);}
  document.getElementById("status").textContent="running ...";
  document.getElementById("cmdOut").textContent="Launching orb ...";
  var x = new XMLHttpRequest();
  x.onreadystatechange = function(){
    if(x.readyState==4 && x.status==200){
      if(!polling){polling=true;poll();}
    }
  };
  x.open("GET","/cmd_spell?"+p,true);
  x.send();
}
function poll(){
  var x = new XMLHttpRequest();
  x.onreadystatechange = function(){
    if(x.readyState==4 && x.status==200){
      var out = strip(x.responseText);
      var c = document.getElementById("cmdOut");
      c.textContent = out;
      document.getElementById("status").textContent = "streaming ("+out.length+" bytes)";
      if(document.getElementById("autoscroll").checked){c.scrollTop = c.scrollHeight;}
      setTimeout(poll,2000);
    }
  };
  x.open("GET","/cmd_spell_update",true);
  x.send();
}
"""

    def _clean(self, value): # strip shell-breaking characters from user input
        return re.sub(r"[\\'\";|&$`\n\r]", "", value).strip()

    def buildGetParams(self, request):
        params = {}
        try:
            path = re.findall(r"^GET ([^\s]+)", request)
        except:
            path = re.findall(r"^GET ([^\s]+)", request.decode('utf-8'))
        if path:
            path = path[0]
            start = path.find("?")
            if start != -1:
                for param in path[start+1:].split("&"):
                    f = param.split("=")
                    if len(f) == 2:
                        params[f[0]] = urlparse.unquote(f[1].replace("+", " "))
        return params

    def get(self, request):
        runcmd = ""
        try:
            res = re.findall(r"^GET ([^\s]+)", request)
        except:
            res = re.findall(r"^GET ([^\s]+)", request.decode('utf-8'))
        if res is None or len(res) == 0:
            return None
        pGet = {}
        page = res[0]
        paramStart = page.find("?")
        if paramStart != -1:
            page = page[:paramStart]
            pGet = self.buildGetParams(request)
        if page == "/cmd_spell":
            target = self._clean(pGet.get("target", ""))
            if target == "":
                return dict(run="", code="200 OK", html="<pre>No target provided.</pre>", ctype="text/html")
            cmd = ""
            method = pGet.get("method", "both")
            if method == "passive":
                cmd += " --passive"
            elif method == "active":
                cmd += " --active"
            if pGet.get("sa") == "on":
                cmd += " --sa"
            elif pGet.get("se", ""):
                cmd += " --se=" + self._clean(pGet["se"])
            if pGet.get("engineloc", ""):
                cmd += " --se-ext=" + self._clean(pGet["engineloc"])
            if pGet.get("delay", ""):
                cmd += " --delay=" + self._clean(pGet["delay"])
            if pGet.get("extens", ""):
                cmd += " --ext=" + self._clean(pGet["extens"])
            toggles = {"nopublic": "--no-public", "nodeep": "--no-deep", "nosocial": "--no-social",
                       "nonews": "--no-news", "nowhois": "--no-whois", "nosubs": "--no-subs",
                       "nodns": "--no-dns", "noscanner": "--no-scanner", "scantcp": "--scan-tcp",
                       "showfiltered": "--show-filtered", "noscandns": "--no-scan-dns",
                       "noscanns": "--no-scan-ns", "noscanmx": "--no-scan-mx", "nobanner": "--no-banner",
                       "nocve": "--no-cve", "nocvs": "--no-cvs"}
            for key, opt in toggles.items():
                if pGet.get(key) == "on":
                    cmd += " " + opt
            if pGet.get("scanports", ""):
                cmd += " --scan-ports=" + self._clean(pGet["scanports"])
            if pGet.get("json") == "on":
                cmd += " --json=" + target + ".json"
            open('/tmp/out', 'w').close() # reset previous output
            runcmd = "(python3 -i orb --spell '" + target + "'" + cmd + " 2>&1 | tee /tmp/out) &"
            return dict(run=runcmd, code="200 OK", html="<pre>Launching orb ...</pre>", ctype="text/html")
        if page == "/cmd_spell_update":
            if not os.path.exists('/tmp/out'):
                open('/tmp/out', 'w').close()
            with open('/tmp/out', 'r') as f:
                return dict(run="", code="200 OK", html="<pre>" + f.read() + "</pre>", ctype="text/html")
        ctype = "text/html"
        if page.find(".js") != -1:
            ctype = "application/javascript"
        if page in self.pages:
            return dict(run="", code="200 OK", html=self.pages[page], ctype=ctype)
        return dict(run="", code="404 Error", html="404 Error - Page not found ...", ctype=ctype)

if __name__ == "__main__":
    tcpsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcpsock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    tcpsock.bind((host, port))
    while True:
        tcpsock.listen(4)
        (clientsock, (ip, c_port)) = tcpsock.accept()
        newthread = ClientThread(ip, c_port, clientsock)
        newthread.start()
