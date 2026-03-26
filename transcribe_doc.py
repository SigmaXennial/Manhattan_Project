import base64
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage

# 1. Initialize the Vision Brain 
llm = ChatOllama(model="llama3.2-vision", temperature=0.4)

filename = "document.jpg"
print(f"\n[+] Initializing Vision Module. Target acquired: {filename}")

try:
    with open(filename, "rb") as image_file:
        image_data = base64.b64encode(image_file.read()).decode("utf-8")

    print("[+] Image encoded. Establishing live stream with Llama 3.2 Vision...\n")

    message = HumanMessage(
        content=[
            {
                "type": "text", 
                "text": "You are an expert historical archivist. Transcribe the handwriting in this document exactly as written, line by line. If a word is illegible, write [illegible]. DO NOT repeat the same phrase over and over. Move systematically down the page. Preserve original spelling."
            },
            {
                "type": "image_url", 
                "image_url": {"url": f"data:image/jpeg;base64,{image_data}"}
            }
        ]
    )

    print("--- LIVE ARCHIVAL TRANSCRIPTION ---\n")
    
    # 3. Stream the Output Live
    for chunk in llm.stream([message]):
        print(chunk.content, end="", flush=True)
        
    print("\n\n[+] Transcription complete.")

except FileNotFoundError:
    print(f"[-] ERROR: '{filename}' not found.")
except Exception as e:
    print(f"[-] CRITICAL ERROR: {e}")
