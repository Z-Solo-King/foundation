from pathlib import Path

path = Path("scripts/patch_chatbot_provider_runtime.py")
text = path.read_text(encoding="utf-8")
marker = 'ux_test = ROOT / "tests" / "test_frontend_ux_completeness.py"'
writeback = 'ux.write_text(ux_text, encoding="utf-8")\n\n'
if writeback not in text:
    if marker not in text:
        raise SystemExit("UX test marker missing in patcher")
    text = text.replace(marker, writeback + marker, 1)
    path.write_text(text, encoding="utf-8")
print("patcher write-back contract: PASS")
