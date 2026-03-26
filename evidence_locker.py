import os
import shutil

# --- CONFIGURATION ---
BASE_DIR = "Evidence_Locker"
CATEGORIES = ["Vital_Records", "Probate_Records", "Census_Records", "Military_Records"]

def setup_locker():
    print(f"\n[+] Initializing Evidence Locker in: {BASE_DIR}")
    
    if not os.path.exists(BASE_DIR):
        os.makedirs(BASE_DIR)
        
    for category in CATEGORIES:
        path = os.path.join(BASE_DIR, category)
        if not os.path.exists(path):
            os.makedirs(path)
            print(f"[*] Created Category: {category}")

    # Logic to move files if they exist in the root
    files_to_organize = {
        "document.jpg": "Probate_Records",
        "document_Page_6.jpg": "Probate_Records",
        "document_Page_5.jpg": "Probate_Records",
        "bissell.ged": "Vital_Records"
    }

    for filename, folder in files_to_organize.items():
        if os.path.exists(filename):
            dest = os.path.join(BASE_DIR, folder, filename)
            shutil.move(filename, dest)
            print(f"[->] Filed {filename} into {folder}")

    print("\n[+] Locker synchronization complete.")

if __name__ == "__main__":
    setup_locker()
