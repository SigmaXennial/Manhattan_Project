import requests
import json

def search_nara(query):
    """Searches the National Archives (NARA) Catalog API."""
    print(f"\n[*] Querying National Archives for: {query}...")
    # NARA API endpoint for archival descriptions
    base_url = "https://catalog.archives.gov/api/v2/records/search"
    params = {
        "q": query,
        "limit": 5
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        results = data.get('body', {}).get('hits', {}).get('hits', [])
        
        if not results:
            print("[-] No records found in NARA.")
            return ""
        
        report = "\n--- NARA ARCHIVAL DATA ---\n"
        for hit in results:
            source = hit.get('_source', {}).get('record', {})
            title = source.get('title', 'No Title')
            naid = source.get('naId', 'N/A')
            url = f"https://catalog.archives.gov/id/{naid}"
            report += f"Title: {title}\nID: {naid}\nURL: {url}\n\n"
        return report
    except Exception as e:
        return f"NARA search failed: {e}"

def search_newspapers(query):
    """Searches the Library of Congress Chronicling America API."""
    print(f"[*] Querying Library of Congress Newspapers for: {query}...")
    base_url = "https://chroniclingamerica.loc.gov/search/pages/results/"
    params = {
        "andtext": query,
        "format": "json"
    }
    
    try:
        response = requests.get(base_url, params=params)
        data = response.json()
        items = data.get('items', [])
        
        if not items:
            print("[-] No newspaper mentions found.")
            return ""
        
        report = "\n--- HISTORIC NEWSPAPER DATA ---\n"
        for item in items[:5]:
            title = item.get('title', 'Unknown Paper')
            date = item.get('date', 'Unknown Date')
            city = ", ".join(item.get('city', []))
            url = f"https://chroniclingamerica.loc.gov{item.get('id')}"
            report += f"Paper: {title} ({date})\nLocation: {city}\nURL: {url}\n\n"
        return report
    except Exception as e:
        return f"Newspaper search failed: {e}"

if __name__ == "__main__":
    target = input("Enter name to search (e.g., 'John Bissell Windsor'): ")
    nara_results = search_nara(target)
    news_results = search_newspapers(target)
    
    with open("External_Recon_Report.txt", "w") as f:
        f.write(nara_results + news_results)
    
    print("\n[+] External Recon complete. Data saved to External_Recon_Report.txt")
