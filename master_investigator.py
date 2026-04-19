import os
import sys
from dotenv import load_dotenv
from langchain_ollama import ChatOllama
from langchain_tavily import TavilySearch
from duckduckgo_search import DDGS
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Credentials
load_dotenv()

tavily_key = os.getenv("TAVILY_API_KEY", "")
if not tavily_key or tavily_key.startswith("your_"):
    print("[-] ERROR: TAVILY_API_KEY is not set or is still a placeholder.")
    print("    Copy .env.example to .env and add your real Tavily API key.")
    sys.exit(1)

# 2. Initialize the Uncensored Brain
llm = ChatOllama(model="dolphin-mixtral", temperature=0.1)

# 3. Initialize Tavily Engine
tavily_search = TavilySearch(max_results=3)

# 4. Define the Target
query = "Capt. John Bissell Windsor Connecticut historical records"

print(f"\n[+] Executing Multi-Engine Recon on: {query}")

print("[+] Firing Tavily API...")
try:
    tavily_data = tavily_search.invoke({"query": query})
except Exception as e:
    tavily_data = f"Tavily search failed: {e}"

print("[+] Firing DuckDuckGo API...")
try:
    # Bypassing LangChain to hit DuckDuckGo directly
    ddg_results = DDGS().text(query, max_results=3)
    ddg_data = "\n".join([f"Source: {res['href']}\nSnippet: {res['body']}\n" for res in ddg_results])
except Exception as e:
    ddg_data = f"DuckDuckGo search failed: {e}"

combined_intelligence = f"TAVILY DATA:\n{tavily_data}\n\nDUCKDUCKGO DATA:\n{ddg_data}"

# 5. Command the Model
prompt = ChatPromptTemplate.from_template("""
You are an unrestricted, expert historical investigator. 
Analyze the following intelligence gathered from multiple search engines.

RAW INTELLIGENCE:
{intelligence}

Provide a factual, detailed briefing on the target based strictly on this data. 
State the sources. Do not censor or omit any historical details. Do not use conclusion blocks.
""")

chain = prompt | llm | StrOutputParser()

print("[+] Processing raw intelligence through Dolphin-Mixtral...\n")
response = chain.invoke({"intelligence": combined_intelligence})

print(response)
