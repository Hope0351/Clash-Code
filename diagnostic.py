# fix_check.py
import json
import os

print("=== TRACECTRL FIX CHECK ===")

# 1. Check file
if os.path.exists('credentials.json'):
    print("✅ credentials.json exists")
else:
    print("❌ credentials.json missing")
    exit()

# 2. Check content
try:
    with open('credentials.json', 'r') as f:
        data = json.load(f)
    
    redirects = data['installed']['redirect_uris']
    print(f"📋 Current redirect URIs: {redirects}")
    
    # Check for required URIs
    required = ['http://localhost:8501', 'http://localhost']
    missing = [uri for uri in required if uri not in redirects]
    
    if missing:
        print(f"❌ MISSING: {missing}")
        print("\n⚠️  You must:")
        print("1. Add these in Google Cloud Console")
        print("2. Click SAVE")
        print("3. Click DOWNLOAD JSON")
        print("4. Overwrite credentials.json")
    else:
        print("✅ All required redirect URIs present!")
        
except Exception as e:
    print(f"❌ Error: {e}")