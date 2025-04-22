import os
import re

SRC_ROOT = "programs"
DEPLOY_DIR = "target/deploy"

def snake_to_camel(name):
    return ''.join(word.capitalize() for word in name.split('_'))

def is_program_block_active(content: str) -> bool:
    # Finds all #[program] lines NOT in comments
    for line in content.splitlines():
        if "#[program]" in line:
            stripped = line.strip()
            if not stripped.startswith("//") and not stripped.startswith("///"):
                return True
    return False

# 🔍 Step 1: Find all #[program] blocks (non-commented), extract instruction names
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

# 🔍 Step 2: Patch all .so files in target/deploy/
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
        if full.encode() in patched:
            obfuscated = f"Instruction: {'_' * len(name)}".encode()
            patched = patched.replace(full.encode(), obfuscated)
            print(f"  🔹 Stripped: {full}")
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
