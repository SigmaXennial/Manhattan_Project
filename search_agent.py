import os
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Setup
os.environ["TAVILY_API_KEY"] = "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"
llm = ChatOllama(model="deepseek-r1:14b", temperature=0)
search = TavilySearch(max_results=5)

# 2. Define the Search Query
query = "John Bissell 1635 Abigail passenger list Olive Tree Genealogy Winthrop Society"

print(f"\n--- Manhattan Project: Executing Direct Recon ---")
print(f"Target: {query}")

# 3. Get Raw Data from the Web
search_results = search.invoke({"query": query})

# 4. Feed data to DeepSeek for analysis
prompt = ChatPromptTemplate.from_template("""
You are a professional genealogist. Analyze the following search results 
regarding John Bissell and the ship Abigail (1635).

SEARCH RESULTS:
{results}

Based ONLY on these results:
1. Is John Bissell listed on the Abigail?
2. If yes, what are the details (age, family, etc.)?
3. Provide the exact URL source.
4. If he is not found, explain what the records DO say about his arrival.
""")

chain = prompt | llm | StrOutputParser()

# 5. Run the analysis
response = chain.invoke({"results": search_results})

print("\n--- ANALYST REPORT ---")
print(response)

# 6. Save to a permanent text file
timestamp = datetime.now().strftime("%Y-%m-%d_%H%M")
filename = f"Recon_Report_{timestamp}.txt"

with open(filename, "w") as file:
    file.write(f"MISSION DATE: {timestamp}\n")
    file.write(f"TARGET QUERY: {query}\n\n")
    file.write("--- ANALYST REPORT ---\n")
    file.write(response)

print(f"\n[+] Success: Report securely logged to {filename}")
