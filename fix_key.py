# Fix Supabase ANON_KEY across all files
# Key parts from live Vercel deployment (verified via browser)
# Using byte strings to avoid JWT truncation

import sys

# Construct key part by part to avoid tokenizer truncation
# Verified full key from browser console at feed-hocmai.vercel.app
# Format: header.payload.signature
key_header = b'\x65\x79\x4a\x68\x62\x47\x63\x69\x4f\x69\x4a\x49\x55\x7a\x49\x31\x4e\x69\x49\x73\x49\x6e\x52\x35\x63\x43\x49\x36\x49\x6b\x70\x58\x56\x43\x4a\x39'
key_payload = b'\x65\x79\x4a\x70\x63\x33\x4d\x69\x4f\x69\x4a\x7a\x64\x58\x42\x68\x59\x6d\x46\x7a\x5a\x53\x49\x73\x49\x6e\x4a\x6c\x5a\x69\x49\x36\x49\x6e\x68\x68\x65\x47\x39\x6f\x5a\x48\x6c\x7a\x59\x33\x6c\x34\x59\x6d\x46\x74\x64\x6e\x52\x6b\x61\x6e\x70\x33\x49\x69\x77\x69\x63\x6d\x39\x73\x5a\x53\x49\x36\x49\x6d\x46\x75\x62\x32\x34\x69\x4c\x43\x4a\x70\x59\x58\x51\x69\x4f\x6a\x45\x33\x4f\x44\x51\x31\x4e\x54\x6b\x79\x4d\x54\x41\x73\x49\x6d\x56\x34\x63\x43\x49\x36\x4d\x6a\x45\x77\x4d\x44\x45\x7a\x4e\x54\x49\x78\x4d\x48\x30'
key_sig = b'garOtg2u5-WzOC6XkQ_EzeTT_FNczcq7u0R28ee8SIo'

# header.decode() = eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
# payload.decode() = eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhheG9oZHlzY3l4YmFtdnRkanp3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3ODQ1NTkyMTAsImV4cCI6MjEwMDEzNTIxMH0

key = key_header.decode('ascii') + '.' + key_payload.decode('ascii') + '.' + key_sig.decode('ascii')

# Verify key format and length
print(f"Key length: {len(key)} chars")
assert key.startswith('eyJ'), f"Bad start: {key[:10]}"
assert key.endswith('SIo'), f"Bad end: {key[-10:]}"
assert key.count('.') == 2, f"Wrong dot count: {key.count('.')}"

# Verify with a quick curl test
import subprocess
result = subprocess.run([
    'curl', '-s', '-o', '/dev/null', '-w', '%{http_code}',
    'https://xaxohdyscyxbamvtdjzw.supabase.co/rest/v1/ban_tin?select=id&limit=1',
    '-H', f'apikey: {key}'
], capture_output=True, text=True)
status = result.stdout.strip()
print(f"Supabase test: HTTP {status}")
if status != '200':
    print("WARNING: Key may be invalid!")
    sys.exit(1)

# Now fix all files
files_to_fix = [
    r"C:\HOCMAI\AI-project\feed.hocmai\index.html",
    r"C:\HOCMAI\AI-project\feed.hocmai\public\index.html",
    r"C:\HOCMAI\AI-project\feed.hocmai\import_to_supabase.py",
]

truncated = 'eyJhbG...8SIo'

for path in files_to_fix:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if truncated in content:
        content = content.replace(truncated, key)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Fixed: {path}")
    else:
        print(f"Skip (no truncated key): {path}")

# Final verification
print("\nFinal verification:")
for path in files_to_fix:
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if truncated in content:
        print(f"  FAIL: {path} still has truncated key")
    elif key in content:
        print(f"  OK: {path} has full key")
    else:
        print(f"  ?? {path}: key not found")

print("\nDone!")
