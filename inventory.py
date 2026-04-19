import os
from dotenv import load_dotenv

# --- TARGET ASSETS ---
SCRIPTS = [
    "bot.py", "master_investigator.py", "analyze_tree.py", 
    "transcribe_doc.py", "compiler.py", "evidence_locker.py",
    "search_agent.py", "external_recon.py", "test_brain.py"
]

DATA_FILES = ["bissell.ged", "document.jpg"]

# Environment variables required by the application
REQUIRED_ENV_VARS = ["TAVILY_API_KEY"]

def check_system():
    load_dotenv()

    print("\n--- MANHATTAN PROJECT: SYSTEM INVENTORY ---")
    print("Scanning local environment for core assets...\n")
    
    missing = []

    print("[*] Checking Environment Variables:")
    env_ok = True
    for var in REQUIRED_ENV_VARS:
        value = os.getenv(var, "")
        if not value or value.startswith("your_"):
            print(f"  [!!]  UNSET/PLACEHOLDER: {var}")
            env_ok = False
        else:
            print(f"  [OK]  {var}")
    if env_ok:
        print("  All required environment variables are configured.")

    print("\n[*] Checking Intelligence Modules:")
    for script in SCRIPTS:
        if os.path.exists(script):
            print(f"  [OK]  {script}")
        else:
            print(f"  [!!]  MISSING: {script}")
            missing.append(script)

    print("\n[*] Checking Primary Source Data:")
    for data in DATA_FILES:
        # Check root folder
        if os.path.exists(data):
            print(f"  [OK]  {data}")
        # Check Evidence Locker subfolders
        elif any(os.path.exists(os.path.join("Evidence_Locker", sub, data)) for sub in ["Probate_Records", "Vital_Records"]):
            print(f"  [OK]  {data} (Located in Evidence Locker)")
        else:
            print(f"  [!!]  MISSING: {data}")
            missing.append(data)

    if not missing:
        print("\n[+] SYSTEM READY: All protocols and data files accounted for.")
    else:
        print(f"\n[-] SYSTEM INCOMPLETE: {len(missing)} assets are missing or displaced.")

if __name__ == "__main__":
    check_system()
