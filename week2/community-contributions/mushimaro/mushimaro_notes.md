# I want an assistant who can help me in Japanese.

I am not good at English, so I was thinking of translating the teaching material program into Japanese.
As an AI beginner, I thought I needed to translate prompts in codes into Japanese.
However, if I enter Japanese directly into the chat of the teaching material program, the AI assistant will answer in Japanese.
I realized that LLMs are multilingual from the beginning. This is a great discovery for me as an AI beginner.

However, even if I asked for the ticket price to Tokyo in Japanese, I didn't get a reply.
The assistant's answer was, "I don't know the price of the ticket to Tokyo."
Even if it is Japanese, the assistant understands that the destination is Tokyo.

I noticed it when I looked at the logs of the tool that searches for ticket prices.
The city name to be searched for is Tokyo in kanji.

I see, even though the assistant is multilingual, the tool is written in traditional programming methods.
It means that the assistant can only speak English.

I tried translating the city name entered in any language into English in the chat and then passing it to the tool as a parameter.

* Function to translate city names to English: translate_city_in_english
* Call translate_city_in_english from handle_tool_calls_and_return_cities

Even if you ask in other languages such as Japanese, Chinese, and Spanish, they will answer your questions.
