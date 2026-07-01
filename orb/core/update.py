#!/usr/bin/env python3
# -*- coding: utf-8 -*-"
"""
This file is part of the orb project, https://orb.03c8.net

Orb - 2016/2026 - by psy (epsylon@riseup.net)

You should have received a copy of the GNU General Public License along
with Orb; if not, write to the Free Software Foundation, Inc., 51
Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
"""
import os
from subprocess import PIPE
from subprocess import Popen as execute

class Updater(object):
    """
    Update Orb automatically from a .git repository
    """
    def find_repo(self): # walk up dirs looking for a .git repository
        path = os.path.abspath(os.path.dirname(__file__))
        while True:
            if os.path.exists(os.path.join(path, ".git")):
                return path
            parent = os.path.dirname(path)
            if parent == path:
                return None
            path = parent

    def __init__(self):
        GIT_REPOSITORY = "https://code.03c8.net/epsylon/orb"
        GIT_REPOSITORY2 = "https://github.com/epsylon/orb"
        rootDir = self.find_repo()
        if not rootDir:
            print("-"*22)
            print("\n[Info] Not any .git repository found!")
            print("\nTo have working this feature, you should clone Orb with:\n")
            print("$ git clone %s" % GIT_REPOSITORY)
            print("\nAlso you can try this other mirror:\n")
            print("$ git clone %s" % GIT_REPOSITORY2 + "\n")
        else:
            env = dict(os.environ, LC_ALL="C") # force English git output
            checkout = execute("git checkout . && git pull", cwd=rootDir, env=env, shell=True, stdout=PIPE, stderr=PIPE).communicate()[0]
            checkout = checkout.decode("utf-8", errors="replace") # bytes -> str (Python3)
            print(checkout)
            if not "Already up to date" in checkout and not "Already up-to-date" in checkout:
                print("Congratulations!! Orb has been updated... ;-)\n")
            else:
                print("Your Orb doesn't need to be updated... ;-)\n")
