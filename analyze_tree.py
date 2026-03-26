import os
import re
from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 1. Initialize the Uncensored Brain
llm = ChatOllama(model="dolphin-mixtral", temperature=0.1)

filename = "bissell.ged"
report_file = "Bissell_Lineage_Report.txt"
print(f"\n[+] Parsing {filename} with structural integrity...")

try:
    individuals = {}
    families = []
    current_id = None
    current_type = None
    current_event = None

    # 2. Database Extraction Logic
    indi_re = re.compile(r"0 (@[A-Za-z0-9_]+@) INDI")
    fam_re = re.compile(r"0 (@[A-Za-z0-9_]+@) FAM")
    name_re = re.compile(r"1 NAME (.*)")
    date_re = re.compile(r"2 DATE (.*)")
    husb_re = re.compile(r"1 HUSB (@[A-Za-z0-9_]+@)")
    wife_re = re.compile(r"1 WIFE (@[A-Za-z0-9_]+@)")
    chil_re = re.compile(r"1 CHIL (@[A-Za-z0-9_]+@)")

    with open(filename, 'r', encoding='utf-8', errors='replace') as f:
        for line in f:
            line = line.strip()
            
            indi_match = indi_re.match(line)
            if indi_match:
                current_id = indi_match.group(1)
                current_type = "INDI"
                individuals[current_id] = {"name": "Unknown", "birth": "Unknown", "death": "Unknown"}
                continue
                
            fam_match = fam_re.match(line)
            if fam_match:
                current_type = "FAM"
                families.append({"husb": None, "wife": None, "chil": []})
                continue
                
            if current_type == "INDI":
                if line.startswith("1 BIRT"): current_event = "BIRT"
                elif line.startswith("1 DEAT"): current_event = "DEAT"
                elif line.startswith("1 "): current_event = None 
                    
                name_match = name_re.match(line)
                if name_match: individuals[current_id]["name"] = name_match.group(1).replace("/", "").strip()
                    
                date_match = date_re.match(line)
                if date_match and current_event == "BIRT": individuals[current_id]["birth"] = date_match.group(1)
                elif date_match and current_event == "DEAT": individuals[current_id]["death"] = date_match.group(1)
                    
            elif current_type == "FAM":
                husb_match = husb_re.match(line)
                if husb_match: families[-1]["husb"] = husb_match.group(1)
                wife_match = wife_re.match(line)
                if wife_match: families[-1]["wife"] = wife_match.group(1)
                chil_match = chil_re.match(line)
                if chil_match: families[-1]["chil"].append(chil_match.group(1))

    # 3. Format Data into Individual Family Blocks
    family_blocks = []
    for fam in families:
        husb = individuals.get(fam["husb"])
        wife = individuals.get(fam["wife"])
        husb_str = f"{husb['name']} (b. {husb['birth']}, d. {husb['death']})" if husb else "Unknown"
        wife_str = f"{wife['name']} (b. {wife['birth']}, d. {wife['death']})" if wife else "Unknown"
        children = [individuals.get(c_id, {}).get("name", "Unknown") for c_id in fam["chil"]]
        
        block = f"Husband: {husb_str}\nWife: {wife_str}\nChildren: {', '.join(children) if children else 'None'}\n"
        family_blocks.append(block)

    print(f"[+] Extracted {len(family_blocks)} family unions. Initiating Agentic Loop...")

    # 4. The Agentic Loop
    prompt = ChatPromptTemplate.from_template("""
    You are an expert genealogical investigator. 
    Draft a professional, factual narrative paragraph for the following family records. 
    State the successions clearly. Do not use conclusion blocks or introductory fluff.

    RECORDS:
    {data}
    """)
    chain = prompt | llm | StrOutputParser()

    # Clear previous report if it exists
    open(report_file, 'w').close()

    batch_size = 5
    for i in range(0, len(family_blocks), batch_size):
        batch = family_blocks[i:i + batch_size]
        batch_text = "\n".join(batch)
        
        print(f"[*] Processing batch {i // batch_size + 1} of {(len(family_blocks) + batch_size - 1) // batch_size}...")
        
        response = chain.invoke({"data": batch_text})
        
        # Save to hard drive progressively
        with open(report_file, 'a', encoding='utf-8') as f:
            f.write(response + "\n\n")

    print(f"\n[+] OPERATION COMPLETE. Full narrative securely written to {report_file}")

except Exception as e:
    print(f"[-] CRITICAL ERROR: {e}")
