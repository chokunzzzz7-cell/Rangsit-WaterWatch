#!/usr/bin/env python3
"""Fetch IPCamLive snapshot, detect gauge color bands, and update status.json."""
import json, os, urllib.request, datetime, math
from PIL import Image

CONFIG = {
  "snapshot_url": "https://s130.ipcamlive.com/streams/82jsgpz8k0si3ynwc/snapshot.jpg",
  "camera_page": "https://www.ipcamlive.com/68c13eaeec104",
  "ref_width": 1920,
  "night_min_brightness": 45,
  "min_fraction": 0.35,
  "bands": {
    "red": {"box": [1036,389,1099,482], "hue": [[330,352]], "sat": 0.5, "val": 0.5},
    "orange": {"box": [1036,507,1099,557], "hue": [[354,360],[0,30]], "sat": 0.5, "val": 0.5},
    "yellow": {"box": [1036,582,1099,632], "hue": [[40,65]], "sat": 0.5, "val": 0.5}
  }
}
STATUS_FILE = "status.json"
UTC = datetime.timezone.utc
now = datetime.datetime.now(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")

def load_status():
    try:
        with open(STATUS_FILE, encoding="utf-8") as f: return json.load(f)
    except Exception:
        return {"ok":False,"note":"Waiting for the first check","history":[]}

def snapshot():
    req = urllib.request.Request(CONFIG["snapshot_url"], headers={
        "User-Agent":"Mozilla/5.0 (compatible; RangsitWaterWatch/1.0)",
        "Referer":CONFIG["camera_page"]
    })
    with urllib.request.urlopen(req, timeout=30) as r:
        return Image.open(r).convert("RGB")

def brightness(im):
    small=im.resize((32,18))
    return sum(0.299*r+0.587*g+0.114*b for r,g,b in small.getdata())/(32*18)

def hsv_fraction(im, band):
    x1,y1,x2,y2=band["box"]
    scale=im.width/CONFIG["ref_width"]
    x1,y1,x2,y2=[int(v*scale) for v in (x1,y1,x2,y2)]
    x1=max(0,min(im.width,x1)); x2=max(0,min(im.width,x2))
    y1=max(0,min(im.height,y1)); y2=max(0,min(im.height,y2))
    if x2<=x1 or y2<=y1: return 0.0
    crop=im.crop((x1,y1,x2,y2)).resize((40,40))
    matches=0
    for r,g,b in crop.getdata():
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255); h*=360
        if s>=band["sat"] and v>=band["val"] and any(lo<=h<=hi for lo,hi in band["hue"]): matches+=1
    return matches/1600

import colorsys

def main():
    st=load_status()
    try: im=snapshot()
    except Exception as e:
        st.update({"ok":False,"note":f"Camera error: {e}","checked_at":now})
        write(st); return
    try:
        if brightness(im)<CONFIG["night_min_brightness"]:
            st.update({"ok":False,"note":"Image too dark to read","checked_at":now})
            write(st); return
        fractions={name:round(hsv_fraction(im,b),2) for name,b in CONFIG["bands"].items()}
        hidden={n for n,v in fractions.items() if v<CONFIG["min_fraction"]}
        level=next((n for n in ("red","orange","yellow") if n in hidden),"green")
        confirmed=st.get("level")
        pending=st.get("pending")
        if level==confirmed: st["pending"]=None
        elif pending==level or confirmed is None:
            st["level"]=level; st["pending"]=None; st["changed_at"]=now
        else: st["pending"]=level
        history=st.get("history") or []
        history.append({"t":now,"level":st.get("level",level)})
        cutoff=datetime.datetime.now(UTC)-datetime.timedelta(hours=24)
        def parse_t(entry):
            try: return datetime.datetime.fromisoformat(entry["t"].replace("Z","+00:00"))
            except Exception: return cutoff-datetime.timedelta(seconds=1)
        history=[h for h in history if parse_t(h)>=cutoff][-288:]
        st.update({"ok":True,"note":"","checked_at":now,"fractions":fractions,"history":history})
        write(st)
    except Exception as e:
        st.update({"ok":False,"note":f"Processing error: {e}","checked_at":now})
        write(st)

def write(st):
    with open(STATUS_FILE,"w",encoding="utf-8") as f: json.dump(st,f,ensure_ascii=False,indent=2)

if __name__=="__main__": main()
