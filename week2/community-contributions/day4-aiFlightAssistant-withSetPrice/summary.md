# Day 11 – Upgrading the AI Flight Assistant

Today I continued improving the mini **Airline AI Flight Assistant** that I built on Day 10.

The main goal was to extend the assistant from only being able to **read ticket prices** to also being able to **update ticket prices** using another tool. Earlier, the assistant could call a `get_ticket_price` tool to fetch prices from an SQLite database. Today, I added a second tool that allows the assistant to set or update the ticket price for a destination city when the user provides both the city name and the new price.

For example, if the user says something like:

```text
Set the ticket price for Delhi to $599
```

the LLM can detect that a tool is needed, call the correct function, and update the price inside the SQLite database.

While testing this, I also ran into an error where the database update was working correctly, but the function was not returning a proper response. Since Python functions return `None` by default when there is no explicit return statement, the tool response content became `None`, which caused the API to throw an error. This helped me understand that every tool function should return a clear string response after execution.

Another important improvement was making the tool handler more modular. Instead of using a long `if/elif` chain to check which tool was called, I learned how to use a dictionary-based tool registry. This allows tool names to be mapped directly to Python functions.

The flow became much cleaner:

```text
Tool name from LLM
        ↓
Find matching function in dictionary
        ↓
Pass arguments dynamically
        ↓
Execute the function
        ↓
Return result to the LLM
```

This makes the code easier to scale. If I add more tools later, I do not need to keep expanding the tool handler with more conditions. I can simply register the new tool in the dictionary.

## Key Learnings

* Added a new tool to update ticket prices in an SQLite database.
* Understood how tool functions can modify application data, not just retrieve it.
* Learned that tool responses must return valid string content.
* Fixed an error caused by a tool function returning `None`.
* Refactored the tool handler using a dictionary-based tool registry.
* Understood how modular tool handling makes agentic applications easier to scale.

## Biggest Takeaway

Building agents is not just about giving an LLM access to tools. It is also about designing the surrounding code properly so that tools can be added, executed, and managed cleanly as the application grows.
