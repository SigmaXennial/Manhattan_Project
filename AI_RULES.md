# AI Rules

## Tech Stack

- Python-based genealogy research toolkit with multiple task-specific scripts.
- Local LLM inference is handled through `langchain-ollama`.
- Prompting and output parsing use `langchain-core`.
- Web research uses `langchain-tavily` for structured search results.
- Supplemental web search uses `duckduckgo-search`.
- Environment variable loading uses `python-dotenv`.
- External archival lookups use `requests` for HTTP API access.
- Historical document transcription supports image input through Ollama vision models.
- Reports and outputs are written as plain text files for easy review and archival.
- The app is organized as standalone command-line workflows launched from `bot.py`.

## Library Rules

- Use `langchain-ollama` for all LLM and vision model interactions.
- Use `ChatOllama` as the default model interface unless a file already requires a different compatible LangChain abstraction.
- Use `langchain-core` for prompt templates, message objects, and output parsers.
- Use `langchain-tavily` when the task requires web search with summarized or structured search results.
- Use `duckduckgo-search` only as a secondary search source or fallback for broader public web discovery.
- Use `requests` for direct calls to public APIs such as NARA or Chronicling America.
- Use `python-dotenv` only for loading local environment variables and API keys from `.env`.
- Use built-in Python libraries for file handling, timestamps, regex parsing, and OS-level workflow control whenever possible.
- Keep outputs in `.txt` files unless a different format is explicitly required.
- Prefer simple standalone scripts over adding new frameworks or services.
- Do not introduce database, web server, or frontend libraries unless the app requirements change.
- Do not add new dependencies if the same task can be handled cleanly with the current stack or the Python standard library.

## Project Conventions

- Keep each script focused on one research workflow or operational task.
- Prefer clear, readable procedural code over heavy abstraction.
- Reuse existing report patterns and naming conventions when creating new outputs.
- Preserve genealogy-specific prompts and factual, source-based output style.
- When adding new research workflows, integrate them through `bot.py` if they are meant to be user-invoked from the console.