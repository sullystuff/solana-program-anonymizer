import os
import re

SRC_ROOT = "programs"
DEPLOY_DIR = "target/deploy"

def snake_to_camel(name):
    return ''.join(word.capitalize() for word in name.split('_'))

def is_program_block_active(content: str) -> bool:
    for line in content.splitlines():
        if "#[program]" in line:
            stripped = line.strip()
            if not stripped.startswith("//") and not stripped.startswith("///"):
                return True
    return False

def build_obfuscated(name: str) -> bytes:
    wizard = "🧙"        # 4 bytes in UTF-8
    pad_byte = b"\x7F"   # 1-byte invisible (DEL)

    target_len = len(name.encode("utf-8"))

    obf = ""
    while len(obf.encode("utf-8")) + len(wizard.encode("utf-8")) <= target_len:
        obf += wizard

    obf_bytes = obf.encode("utf-8")
    remaining = target_len - len(obf_bytes)
    obf_bytes += pad_byte * remaining

    return b"Instruction: " + obf_bytes

# Step 1: Extract instructions
ix_names = []

for root, _, files in os.walk(SRC_ROOT):
    for file in files:
        if file.endswith(".rs"):
            path = os.path.join(root, file)
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
                if is_program_block_active(content):
                    found = re.findall(r"pub fn ([a-zA-Z0-9_]+)\s*\(", content)
                    camelized = [snake_to_camel(fn) for fn in found]
                    if camelized:
                        print(f"✅ Found {len(camelized)} instructions in {path}: {camelized}")
                        ix_names.extend(camelized)

if not ix_names:
    print("❌ No active #[program] blocks or instruction functions found.")
    exit(1)

# Step 2: Patch .so files
so_files = [f for f in os.listdir(DEPLOY_DIR) if f.endswith(".so")]

if not so_files:
    print("❌ No .so files found in target/deploy/")
    exit(1)

for so_name in so_files:
    so_path = os.path.join(DEPLOY_DIR, so_name)
    print(f"\n🔧 Patching: {so_path}")

    with open(so_path, "rb") as f:
        binary = f.read()

    patched = binary
    patched_any = False

    for name in ix_names:
        full = f"Instruction: {name}"
        full_bytes = full.encode("utf-8")
        if full_bytes in patched:
            obfuscated = build_obfuscated(name)
            patched = patched.replace(full_bytes, obfuscated)
            print(f"  🧙 Obfuscated: {full}")
            patched_any = True
        else:
            print(f"  ⚠️  Not found: {full}")

    if patched_any:
        with open(so_path, "wb") as f:
            f.write(patched)
        print(f"  ✅ Wrote patched binary.")
    else:
        print(f"  ℹ️  No changes made.")

print("\n🎉 All done.")
