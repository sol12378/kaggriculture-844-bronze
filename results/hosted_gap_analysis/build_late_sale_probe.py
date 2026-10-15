"""Build experimental late-sale policies for local diagnosis only."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "second_meta_agent_20260930" / "main.py"
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == "bf695ed7591c5ae1cd88f7b847c5188fc6e0a51da84c36e2a1b6d16e25e0b8eb"
base = SOURCE.read_text(encoding="utf-8")
suffix = '''

# Diagnostic: relax the blanket future-first-sale protection only late in the
# season, while leaving the native resource/cash/slot guards in place.
_LATE_PROBE_PARENT=agent
def agent(observation,configuration=None):
    global _ADV_PROTECT
    _ADV_PROTECT=int(observation['step'])<600
    return _LATE_PROBE_PARENT(observation,configuration)
submission_agent_late_probe=agent
'''
variants = {
    "late_unprotect": base + suffix,
    "late_unprotect_look5": base.replace("_ADV_LOOK=3 if _COND_MIRROR.get(seat) else 5", "_ADV_LOOK=5") + suffix,
}
out = {}
for name, content in variants.items():
    path = HERE / "probes" / name / "main.py"
    path.parent.mkdir(parents=True, exist_ok=True)
    compile(content, str(path), "exec")
    path.write_text(content, encoding="utf-8")
    out[name] = {"path": str(path), "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
(HERE / "LATE_PROBE_BUILD.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
print(json.dumps(out, indent=2))
