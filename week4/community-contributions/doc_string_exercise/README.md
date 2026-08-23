# Script Overview

The documentation will show you how to run the python script generate_doc_string.py. It is designed to take input
from an existing python file and create a new one with a suffix ('claude' or 'gpt'). If you do not specify and llm 
model, it will default to claude.

# How to run

```powershell
conda activate llms
cd <script_location>
python generate_doc_string -fp <full_file_path> -llm <name_of_model>
```

# Show Help Instructions

```shell
python generate_doc_string --help
```

# Error Checking

1) File Path Existence

If the file path doesn't exist, the script will stop running and print out an error.

2) LLM Model Choice

If you choose something other than 'gpt' or 'claude', it will show and assertion error.