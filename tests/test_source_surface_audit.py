from __future__ import annotations
import subprocess, sys
from pathlib import Path
ROOT=Path(__file__).parents[1]
def test_source_surface_audit_runs():
    out=ROOT/".runtime/test-source-audit.json"; out.parent.mkdir(exist_ok=True)
    subprocess.check_call([sys.executable,str(ROOT/"tools/source_surface_audit.py"),"--root",str(ROOT),"--root",str(ROOT.parent/"operations"),"--output",str(out)]) if (ROOT.parent/"operations").exists() else subprocess.check_call([sys.executable,str(ROOT/"tools/source_surface_audit.py"),"--root",str(ROOT),"--output",str(out)])
    assert out.exists()