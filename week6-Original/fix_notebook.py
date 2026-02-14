import json

notebook_path = "f:\\Ai agent model projects\\llm_engineering\\week6-Original\\day4.ipynb"

try:
    with open(notebook_path, 'r', encoding='utf-8') as f:
        nb = json.load(f)

    # New source code for cells
    run_gemini_source = [
        "#gemini = OpenAI(base_url=gemini_url, api_key=google_api_key)\n",
        "def run_gemini(item):\n",
        "    try:\n",
        "        response = gemini.chat.completions.create(\n",
        "            model=\"gemini-1.5-flash\", \n",
        "            messages=messages_for(item),\n",
        "            temperature=0,\n",
        "            max_tokens=10\n",
        "        )\n",
        "        reply = response.choices[0].message.content\n",
        "        return get_price(reply)\n",
        "    except Exception as e:\n",
        "        print(f\"Gemini Error: {e}\")\n",
        "        return 0\n"
    ]

    test_gemini_source = [
        "Tester.test(run_gemini, test)"
    ]

    run_openrouter_source = [
        "def run_openrouter(item):\n",
        "    try:\n",
        "        response = openrouter.chat.completions.create(\n",
        "            model=\"gpt-oss-20b:free\", \n",
        "            messages=messages_for(item),\n",
        "            temperature=0,\n",
        "            max_tokens=10,\n",
        "            extra_headers={\n",
        "                \"HTTP-Referer\": \"https://localhost\", \n",
        "                \"X-Title\": \"Local Testing\"\n",
        "            }\n",
        "        )\n",
        "        reply = response.choices[0].message.content\n",
        "        return get_price(reply)\n",
        "    except Exception as e:\n",
        "        print(f\"OpenRouter Error: {e}\")\n",
        "        return 0"
    ]

    test_openrouter_source = [
        "Tester.test(run_openrouter, test)"
    ]

    # Update cells
    updated = 0
    for cell in nb['cells']:
        if cell.get('id') == "3acbefb3-0404-490e-8905-cd913c34f7b0":
            cell['source'] = run_gemini_source
            cell['outputs'] = [] # Clear outputs
            updated += 1
        elif cell.get('id') == "ac222cd7-9f6d-4388-8d7e-a941019336a0":
            cell['source'] = test_gemini_source
            cell['outputs'] = []
            updated += 1
        elif cell.get('id') == "c3ff6e9b-4da8-4d93-93f9-499125bdceab":
            cell['source'] = run_openrouter_source
            cell['outputs'] = []
            updated += 1
        elif cell.get('id') == "e2eca9da-0a0d-4bf0-9204-0fd40bafb0e8":
            cell['source'] = test_openrouter_source
            cell['outputs'] = []
            updated += 1

    with open(notebook_path, 'w', encoding='utf-8') as f:
        json.dump(nb, f, indent=1)

    print(f"Notebook updated successfully. {updated} cells modified.")

except Exception as e:
    print(f"Error: {e}")
