import os
import sys
from datetime import datetime
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

load_dotenv()

tavily_key = os.getenv("TAVILY_API_KEY", "")
if not tavily_key or tavily_key.startswith("your_"):
    print("[-] ERROR: TAVILY_API_KEY is not set or is still a placeholder.")
    print("    Copy .env.example to .env and add your real Tavily API key.")
    sys.exit(1)


def get_research_parameters():
    """
    Gather genealogical research parameters from user input.
    Returns a dictionary with name, dates, locations, and research objectives.
    """
    print("\n--- Manhattan Project: Genealogical Research Agent ---")
    print("Enter your research parameters (press Enter to skip optional fields):\n")
    
    # Required: Person's name
    name = input("Person being researched (full name): ").strip()
    if not name:
        print("ERROR: Please provide a name to research.")
        sys.exit(1)
    
    # Optional: Birth/Death dates
    birth_date = input("Birth year/date (optional): ").strip()
    death_date = input("Death year/date (optional): ").strip()
    
    # Optional: Locations
    locations = input("Locations (birthplace, residence, etc. - optional): ").strip()
    
    # Optional: Vessels or records of interest
    records_of_interest = input("Specific records/vessels/families to search (optional): ").strip()
    
    # Optional: Research objective
    research_goal = input("Research goal (find lineage, verify dates, locate relatives, etc. - optional): ").strip()
    
    return {
        "name": name,
        "birth_date": birth_date,
        "death_date": death_date,
        "locations": locations,
        "records_of_interest": records_of_interest,
        "research_goal": research_goal
    }


def build_search_query(params):
    """
    Construct a comprehensive search query from research parameters.
    """
    query_parts = [params["name"]]
    
    if params["birth_date"]:
        query_parts.append(params["birth_date"])
    if params["death_date"]:
        query_parts.append(params["death_date"])
    if params["locations"]:
        query_parts.append(params["locations"])
    if params["records_of_interest"]:
        query_parts.append(params["records_of_interest"])
    
    # Add genealogy-specific search terms
    query_parts.extend([
        "genealogy records",
        "passenger list",
        "census records"
    ])
    
    return " ".join(query_parts)


def build_analysis_prompt(params):
    """
    Construct a dynamic analysis prompt based on research parameters.
    """
    prompt_text = f"""
You are a professional genealogist. Analyze the following search results 
regarding {params['name']}.
"""
    
    if params["birth_date"] or params["death_date"]:
        prompt_text += f"\nResearch dates: "
        if params["birth_date"]:
            prompt_text += f"Born {params['birth_date']}"
        if params["death_date"]:
            prompt_text += f", Died {params['death_date']}"
        prompt_text += "\n"
    
    if params["locations"]:
        prompt_text += f"Locations of interest: {params['locations']}\n"
    
    if params["records_of_interest"]:
        prompt_text += f"Specific records/vessels to investigate: {params['records_of_interest']}\n"
    
    prompt_text += """
SEARCH RESULTS:
{results}

Based ONLY on these results:
1. What genealogical records or information were found about the target individual?
2. What are the key biographical details (dates, locations, family connections, occupations)?
3. Provide the exact URL source(s) for verifiable information.
4. If the target person was not directly found, what related records or alternative names were discovered?
5. Summarize any gaps in the available records that may require further research.
"""
    
    if params["research_goal"]:
        prompt_text += f"\nResearch objective: {params['research_goal']}\n"
    
    return prompt_text


def main():
    """
    Main execution function for genealogical research agent.
    """
    # Setup
    llm = ChatOllama(model="deepseek-r1:14b", temperature=0)
    search = TavilySearch(max_results=5)
    
    # Get research parameters from user
    params = get_research_parameters()
    
    # Build dynamic search query
    query = build_search_query(params)
    
    print(f"\n--- Executing Genealogical Research ---")
    print(f"Target: {params['name']}")
    if params["birth_date"] or params["death_date"]:
        print(f"Dates: {params['birth_date']} - {params['death_date']}")
    if params["locations"]:
        print(f"Locations: {params['locations']}")
    print(f"Full Query: {query}\n")
    
    # Get raw data from the web
    print("[*] Searching genealogical records...")
    search_results = search.invoke({"query": query})
    
    # Build dynamic analysis prompt
    analysis_prompt_template = build_analysis_prompt(params)
    
    # Feed data to DeepSeek for analysis
    prompt = ChatPromptTemplate.from_template(analysis_prompt_template)
    chain = prompt | llm | StrOutputParser()
    
    # Run the analysis
    print("[*] Analyzing results with genealogical expertise...\n")
    response = chain.invoke({"results": search_results})
    
    print("--- GENEALOGICAL ANALYSIS REPORT ---")
    print(response)
    
    # Save to a permanent text file
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
    filename = f"Recon_Report_{timestamp}.txt"
    
    with open(filename, "w") as file:
        file.write(f"RESEARCH DATE: {timestamp}\n")
        file.write(f"TARGET: {params['name']}\n")
        if params["birth_date"]:
            file.write(f"BIRTH: {params['birth_date']}\n")
        if params["death_date"]:
            file.write(f"DEATH: {params['death_date']}\n")
        if params["locations"]:
            file.write(f"LOCATIONS: {params['locations']}\n")
        if params["records_of_interest"]:
            file.write(f"RECORDS: {params['records_of_interest']}\n")
        if params["research_goal"]:
            file.write(f"GOAL: {params['research_goal']}\n")
        file.write(f"\nQUERY: {query}\n\n")
        file.write("--- GENEALOGICAL ANALYSIS REPORT ---\n")
        file.write(response)
    
    print(f"\n[+] Success: Report securely logged to {filename}")


if __name__ == "__main__":
    main()
