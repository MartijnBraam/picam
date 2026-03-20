import os
import re
import queue
import subprocess

regex = re.compile(r"astats\.(\d)\.RMS_level=(.+)")

def audiothread(q: queue.Queue):
    root = os.path.dirname(os.path.abspath(__file__))
    script = os.path.join(root, "audio.sh")
    p  = subprocess.Popen(script, stdout=subprocess.PIPE)
    latest = [0,0]
    for line in p.stdout:
        val = regex.search(line)
        chan = int(val.group(0))
        level = float(val.group(1))
        latest[chan-1] = level
        if chan == 2:
            q.put(tuple(latest))