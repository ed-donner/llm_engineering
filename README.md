# LLM Engineering - Master AI and LLMs

## Your 8 week journey to proficiency starts today

![Voyage](assets/voyage.jpg)

_If you're looking at this in Cursor, please right click on the filename in the Explorer on the left, and select "Open preview", to view the formatted version._

I'm so happy you're joining me on this path. We'll be building immensely satisfying projects in the coming weeks. Some will be easy, some will be challenging, many will ASTOUND you! The projects build on each other so you develop deeper and deeper expertise each week. One thing's for sure: you're going to have a lot of fun along the way.

## IMPORTANT ANNOUNCEMENT - DECEMBER 2025 - PLEASE READ

The course material has been completely refreshed with all new weeks. If you'd prefer to stick with the code for the original videos, simply do this from your Anaconda Prompt or Terminal:  
`git fetch`  
`git checkout original`

Any questions, please ask me on Udemy or at ed@edwarddonner.com. More details at the top of the course resources [here](https://edwarddonner.com/2024/11/13/llm-engineering-resources/).

### Before you begin

I'm here to help you be most successful with your learning. If you hit any snafus, or if you have any ideas on how I can improve the course, please do reach out in the platform or by emailing me direct (ed@edwarddonner.com). It's always great to connect with people on LinkedIn to build up the community - you'll find me here:  
https://www.linkedin.com/in/eddonner/  
And this is new to me, but I'm also trying out X/Twitter at [@edwarddonner](https://x.com/edwarddonner) - if you're on X, please show me how it's done 😂  

Resources to accompany the course, including the slides and useful links, are here:  
https://edwarddonner.com/2024/11/13/llm-engineering-resources/

And a useful FAQ with common questions is here:  
https://edwarddonner.com/faq/

## Instant Gratification instructions for Week 1, Day 1 - with Llama 3.2 **not** Llama 3.3

### Important note: see my warning about Llama3.3 below - it's too large for home computers! Stick with llama3.2 - several students have missed this warning...

We will start the course by installing Ollama so you can see results immediately!
1. Download and install Ollama from https://ollama.com noting that on a PC you might need to have administrator permissions for the install to work properly
2. On a PC, start a Command prompt / Powershell (Press Win + R, type `cmd`, and press Enter). On a Mac, start a Terminal (Applications > Utilities > Terminal).
3. Run `ollama run llama3.2` or for smaller machines try `ollama run llama3.2:1b` - **please note** steer clear of Meta's latest model llama3.3 because at 70B parameters that's way too large for most home computers!  
4. If this doesn't work: you may need to run `ollama serve` in another Powershell (Windows) or Terminal (Mac), and try step 3 again. On a PC, you may need to be running in an Admin instance of Powershell.  
5. And if that doesn't work on your box, I've set up this on the cloud. This is on Google Colab, which will need you to have a Google account to sign in, but is free:  https://colab.research.google.com/drive/1-_f5XZPsChvfU1sJ0QqCePtIuc55LSdu?usp=sharing

Any problems, please contact me!

## Before the Setup instructions - a special note

Early on in the course (on Day 2), I give a demo of a very cool, popular product called Claude Code. It's an AI coding tool, similar to Cursor that we use on the course. I'm only showing this as an example of Agentic AI in action; it's not a tool that's covered explicitly on this course, particularly as we're in Cursor. But if you want to use Claude Code yourself, the Quick Start guide from Anthropic is [here](https://docs.claude.com/en/docs/claude-code/quickstart).

## OK - now on to Setup instructions

After we do the Ollama quick project, and after I introduce myself and the course, we get to work with the full environment setup.  

Hopefully I've done a decent job of making these guides bulletproof - but please contact me right away if you hit roadblocks:

NEW INSTRUCTIONS for new version of the course (rolled out October 2025): [New Setup Instructions All Platforms](setup/SETUP-new.md)

ORIGINAL INSTRUCTIONS for people on the version prior to October 2025:  
- PC people please follow the instructions here: [Original PC instructions](setup/SETUP-PC.md)
- Mac people please follow the instructions here: [Original Mac instructions](setup/SETUP-mac.md)  
- Linux people please follow the instructions here: [Original Linux instructions](setup/SETUP-linux.md)

### An important point on API costs (which are optional! No need to spend if you don't wish)

During the course, I'll suggest you try out the leading models at the forefront of progress, known as the Frontier models. I'll also suggest you run open-source models using Google Colab. These services have some charges, but I'll keep cost minimal - like, a few cents at a time. And I'll provide alternatives if you'd prefer not to use them.

Please do monitor your API usage to ensure you're comfortable with spend; I've included links below. There's no need to spend anything more than a couple of dollars for the entire course. Some AI providers such as OpenAI require a minimum credit like \$5 or local equivalent; we should only spend a fraction of it, and you'll have plenty of opportunity to put it to good use in your own projects. During Week 7 you have an option to spend a bit more if you're enjoying the process - I spend about \$10 myself and the results make me very happy indeed! But it's not necessary in the least; the important part is that you focus on learning.

### Free alternative to Paid APIs

See [Guide 9](guides/09_ai_apis_and_ollama.ipynb) in the guides directory for the detailed approach with exact code for Ollama, Gemini, OpenRouter and more!

### How this Repo is organized

There are folders for each of the "weeks", representing modules of the class, culminating in a powerful autonomous Agentic AI solution in Week 8 that draws on many of the prior weeks.    
Follow the setup instructions above, then open the Week 1 folder and prepare for joy.

### The most important part

The mantra of the course is: the best way to learn is by **DOING**. I don't type all the code during the course; I execute it for you to see the results. You should work along with me or after each lecture, running each cell, inspecting the objects to get a detailed understanding of what's happening. Then tweak the code and make it your own. There are juicy challenges for you throughout the course. I'd love it if you wanted to submit a Pull Request for your code (see the Github guide in the guides folder) and I can make your solutions available to others so we share in your progress; as an added benefit, you'll be recognized in GitHub for your contribution to the repo. While the projects are enjoyable, they are first and foremost designed to be _educational_, teaching you business skills that can be put into practice in your work.

## Starting in Week 3, we'll also be using Google Colab for running with GPUs

You should be able to use the free tier or minimal spend to complete all the projects in the class. I personally signed up for Colab Pro+ and I'm loving it - but it's not required.

Learn about Google Colab and set up a Google account (if you don't already have one) [here](https://colab.research.google.com/)

The colab links are in the folders for Week 3 and Week 7 - if you open up the lab for each day, you'll find a direct link to the colab.

### Monitoring API charges

You can keep your API spend very low throughout this course; you can monitor spend at the dashboards: [here](https://platform.openai.com/usage) for OpenAI, [here](https://console.anthropic.com/settings/cost) for Anthropic.

The charges for the exercsies in this course should always be quite low, but if you'd prefer to keep them minimal, then be sure to always choose the cheapest versions of models:
1. For OpenAI: Always use model `gpt-4.1-nano` in the code
2. For Anthropic: Always use model `claude-3-haiku-20240307` in the code instead of the other Claude models
3. During week 7, look out for my instructions for using the cheaper dataset

Please do message me or email me at ed@edwarddonner.com if this doesn't work or if I can help with anything. I can't wait to hear how you get on.

<table style="margin: 0; text-align: left;">
    <tr>
        <td style="width: 150px; height: 150px; vertical-align: middle;">
            <img src="assets/resources.jpg" width="150" height="150" style="display: block;" />
        </td>
        <td>
            <h2 style="color:#f71;">Other resources</h2>
            <span style="color:#f71;">I've put together this webpage with useful resources for the course. This includes links to all the slides.<br/>
            <a href="https://edwarddonner.com/2024/11/13/llm-engineering-resources/">https://edwarddonner.com/2024/11/13/llm-engineering-resources/</a><br/>
            Please keep this bookmarked, and I'll continue to add more useful links there over time.
            </span>
        </td>
    </tr>
</table>
