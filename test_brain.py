from langchain_ollama import ChatOllama

# Connect to your local DeepSeek model
llm = ChatOllama(model="deepseek-r1:14b", temperature=0)

print("Connecting to the Probate Unit...")

# Send a test query
response = llm.invoke("What is the legal definition of a widow's third in 18th-century colonial America? Keep the answer to two sentences.")

print("\nResponse received:\n")
print(response.content)
