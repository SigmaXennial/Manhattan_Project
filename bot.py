# ... (inside main_menu print statements) ...
    print("7. [INVENTORY]  - Run System Health Check")
    print("8. [EXT RECON]  - Search NARA & Historic Newspapers") # NEW
    print("9. [EXIT]       - Power Down")

# ... (inside the choice blocks) ...
    elif choice == "8":
        log_event("EXT RECON", "Initiated NARA and Newspaper search.")
        os.system("python3 external_recon.py")
        input("\nPress Enter to return to Console...")
        main_menu()
    elif choice == "9":
        log_event("SHUTDOWN", "Operation terminated.")
        sys.exit()
