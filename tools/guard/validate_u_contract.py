import sys, json, pathlib, re
from jsonschema import validate, exceptions as je
u = json.load(open(sys.argv[1])); schema = json.load(open(sys.argv[2]))
try:
    validate(u, schema)
except je.ValidationError as e:
    print(f"[FAIL] schema: {e.message}"); sys.exit(1)
for c in u.get("citations", []):
    p=c.get("path"); lines=c.get("lines","")
    if not p: continue
    f = pathlib.Path(p)
    if not f.exists(): print(f"[WARN] citation missing: {p}")
    if lines and not re.match(r"^(\\d+)(-(\\d+))?$", lines): print(f"[WARN] bad lines: {lines}")
print("[PASS] U-Contract validated")
