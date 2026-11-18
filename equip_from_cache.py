import json, socket, struct, time
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad

# Cache load karo
try:
    with open("local_cache.json") as f:
        cache = json.load(f)
except:
    print("[-] local_cache.json nahi mili!"); exit()

UID = int(cache["uid"])
KEY = bytes.fromhex(cache["key"])
IV  = bytes.fromhex(cache["iv"])
IP  = cache["online_ip"]
PORT = int(cache["online_port"])
JWT = cache["token"]
TS  = int(cache["timestamp"])

# Emote ID (Yahan tu apna emote ID daal sakta hai)
EMOTE_ID = 909000098 

def _vi(n):
    r = []
    while True:
        b = n & 0x7F; n >>= 7
        if n: b |= 0x80
        r.append(b)
        if not n: break
    return bytes(r)

def _pf(k, v):
    if isinstance(v, int): return _vi((k << 3) | 0) + _vi(v)
    if isinstance(v, str):
        e = v.encode(); return _vi((k << 3) | 2) + _vi(len(e)) + e
    if isinstance(v, (bytes, bytearray)):
        e = bytes(v); return _vi((k << 3) | 2) + _vi(len(e)) + e
    return b""

def _bp(fields): return b"".join(_pf(k, v) for k, v in fields.items())

def frame(ptype_hex, payload, key, iv):
    ct = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(payload, 16))
    return bytes.fromhex(ptype_hex) + struct.pack(">I", len(ct)) + ct

# 1. Auth Packet (Online Socket connect karne ke liye)
def build_auth(uid, kts, jwt, key, iv):
    enc = AES.new(key, AES.MODE_CBC, iv).encrypt(pad(jwt.encode(), 16))
    return (bytes([0x8D, 0x14]) + int(uid).to_bytes(8, "big")
            + int(kts).to_bytes(4, "big") + b"\x00\x00\x00\x00" 
            + struct.pack(">I", len(enc)) + enc)

# 2. Equip Packet (Action 72)
def build_equip_packet(uid, emote_id, key, iv):
    inner = _bp({1: uid, 2: emote_id})
    top = _bp({1: 72, 2: inner})
    return frame("0515", top, key, iv)

print(f"[*] Emote Equip Starting for UID: {UID}")
print(f"[*] Connecting to {IP}:{PORT}...")

try:
    s = socket.create_connection((IP, PORT), timeout=10)
    s.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    
    print("[*] Sending Auth...")
    s.sendall(build_auth(UID, TS, JWT, KEY, IV))
    time.sleep(1.5)
    
    print(f"[*] Equipping Emote ID: {EMOTE_ID}...")
    s.sendall(build_equip_packet(UID, EMOTE_ID, KEY, IV))
    time.sleep(1.5)
    
    print("[+] Emote Equip Packet Sent Successfully!")
    s.close()
    
except Exception as e:
    print(f"[-] Error: {e}")
