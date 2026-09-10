Copy/merge these files into:
C:\Users\Admin\Documents\ResearchIntelligence

This package:
- fixes scripts\ship.ps1
- adds backend\content_integrity.py
- adds backend\evidence_certificate.py
- adds tests for both

Then run:
python -m pytest

Then:
.\scripts\ship.ps1 "Add content integrity and evidence certificates"
