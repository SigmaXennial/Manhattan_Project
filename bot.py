import os
import sys
from datetime import datetime

# --- CONFIGURATION ---
LOG_FILE = "Master_Case_Log.txt"

def log_event(event_name, details="No additional details provided."):
    """Securely logs activity to the Master Case File."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a") as f:
        f.write(f"[{timestamp}] PROTOCOL: {event_name}\n")
        f.write(f"DETAILS: {details}\n")
        f.write("-" * 40 + "\n")

def clear_screen():
    os.system('clear')

def main_menu():
    clear_screen()
    print("--- MANHATTAN PROJECT: GENEALOGY INTELLIGENCE CONSOLE ---")
    print("Directing M4 Max Neural Engine...")
    print(f"Log Destination: {LOG_FILE}")
    print("-" * 55)
    print("1. [RECON]      - Execute Multi-Engine Web Search")
    print("2. [ANALYSIS]   - Parse GEDCOM Tree (Agentic Loop)")
    print("3. [VISION]     - Transcribe Historical Document")
    print("4. [VIEW LOG]   - Open Master Case Log")
    print("5. [COMPILER]   - Generate Mayflower Submission Draft")
    print("6. [LOCKER]     - Organize Evidence & Exhibits")
    print("7. [INVENTORY]  - Run System Health Check")
    print("8. [EXT RECON]  - Search NARA & Historic Newspapers")
    print("9. [EXIT]       - Power Down")
    print("-" * 55)
    
    choice = input("\nSelect Protocol (1-9): ")
    
    if choice == "1":
        log_event("RECON", "Initiated web search.")
        os.system("python3 master_investigator.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "2":
        log_event("ANALYSIS", "Initiated tree parsing.")
        os.system("python3 analyze_tree.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "3":
        log_event("VISION", "Initiated transcription.")
        os.system("python3 transcribe_doc.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "4":
        # Cross-platform file open
        if sys.platform == "darwin":
            os.system(f"open {LOG_FILE}")
        elif sys.platform == "win32":
            os.system(f"start {LOG_FILE}")
        else:
            os.system(f"xdg-open {LOG_FILE} 2>/dev/null || cat {LOG_FILE}")
        main_menu()
    elif choice == "5":
        log_event("COMPILER", "Generated submission draft.")
        os.system("python3 compiler.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "6":
        log_event("LOCKER", "Synchronized exhibits.")
        os.system("python3 evidence_locker.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "7":
        os.system("python3 inventory.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "8":
        log_event("EXT RECON", "Initiated NARA and Newspaper search.")
        os.system("python3 external_recon.py")
        input("\nPress Enter to return...")
        main_menu()
    elif choice == "9":
        log_event("SHUTDOWN", "Operation terminated.")
        sys.exit()
    else:
        print("[-] Invalid selection.")
        input("\nPress Enter to try again...")
        main_menu()

if __name__ == "__main__":
    main_menu()
