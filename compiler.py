import os
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Initialize the Brain
llm = ChatOllama(model="dolphin-mixtral", temperature=0.3)

print("\n[+] Initiating Mayflower Compiler...")

# 2. Gather Intelligence from existing reports
intelligence = ""
files_to_read = ["Bissell_Lineage_Report.txt", "Transcription_Report.txt"]

for filename in files_to_read:
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            intelligence += f"\n--- DATA FROM {filename} ---\n"
            intelligence += f.read()
    else:
        print(f"[-] Warning: {filename} not found. Ensure you have run Analysis and Vision first.")

if not intelligence:
    print("[-] ERROR: No intelligence reports found to compile.")
else:
    # 3. Command the Synthesis
    prompt = ChatPromptTemplate.from_template("""
    You are a Senior Genealogist preparing a formal application for a lineage society.
    Synthesize the following research into a professional Genealogical Proof Summary.
    
    Focus on:
    - Establishing the direct line of descent.
    - Citing the primary evidence (like the 1673 Will and Codicil).
    - Resolving any discrepancies in birth or death dates.
    
    Format this as a formal draft. Do not use conversational filler or conclusions.

    RAW RESEARCH DATA:
    {data}
    """)

    chain = prompt | llm | StrOutputParser()
    
    print("[+] Synthesizing master draft...")
    response = chain.invoke({"data": intelligence})
    
    with open("MAYFLOWER_SUBMISSION_DRAFT.txt", "w") as f:
        f.write(response)
        
    print("\n[+] SUCCESS: Master draft written to MAYFLOWER_SUBMISSION_DRAFT.txt")
