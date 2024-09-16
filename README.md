# LLM Engineering - Master AI and LLMs

## Your 8 week journey to proficiency starts today

![Voyage](voyage.jpg){width=500}

I'm so happy you're joining me on this path. We'll be building immensely satisfying projects in the coming weeks. Some will be easy, some will be challenging, many will ASTOUND you! The projects build on each other so you develop deeper and deeper expertise each week. One thing's for sure: you're going to have a lot of fun along the way.

### How this Jupyter Lab is organized

There are folders for each of the "weeks", representing modules of the class.  
Follow the setup instructions below, then open the Week 1 folder and prepare for joy.

### The most important part

The matra of the course is: the best way to learn is by **DOING**. You should work along with me, running each cell, inspecting the objects to get a detailed understanding of what's happening. Then tweak the code and make it your own. There are juicy challenges for you throughout the course. I'd love it if you wanted to push your code so I can follow along with your progress, and I can make your solutions available to others so we share in your progress.

## Setup instructions

By far the recommended approach is to use Anaconda for your environment. Even if you've never used it before, it makes such a difference. Anaconda ensures that you're working with the right version of Python and all your packages are compatible with mine, even if we're on different platforms.

### Getting ready to set up

Clone this repo by clicking on the dropdown in the green 'Code' button in Github, copying the URL to the clip board, and entering `git clone <url>` in your terminal.

Then if you've not used Anaconda before, install it for your platform. You will thank me! It's the best.  
Link to install Anaconda:  
https://docs.anaconda.com/anaconda/install/

### Setup instructions in 4 steps

1. Create a new Anaconda environment for this project. It's like virtualenv, only infinitely better.

`conda env create -f environment.yml`

2. Activate the environment:

`conda activate llms`

3. Start your Jupyter Lab

`jupyter lab`

4. Get a celebratory cup of coffee and prepare for coding!

### When we get to it, creating your API keys

Particularly during weeks 1 and 2 of the course, you'll be writing code to call the APIs of Frontier models. You'll need to join me in setting up accounts and API keys.

- [GPT API](https://platform.openai.com/) from OpenAI
- [Claude API](https://console.anthropic.com/) from Anthropic
- [Gemini API](https://ai.google.dev/gemini-api) from Google

Initially we'll only use OpenAI, so you can start with that, and we'll cover the others soon afterwards.

Later in the course you'll be using a HuggingFace account, which is available for free at https://huggingface.co - you'll need to create an API token from the Avatar menu >> Settings >> Access Tokens.

When you have these keys, please create a new file called `.env` in your project root directory.

It should have contents like this:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

This file is listed in the `.gitignore` file, so it won't get checked in and your keys stay safe.

## And that's it! Happy coding!

### Alternative Setup Instructions if you're a die-hard virtualenv-er

Well if you must! Just be sure to be running python 3.11, or we might hit compatibility snags.

Here are the steps:

After cloning the repo:

1. Create a new virtual environment using something like `python3 -m venv /path/to/new/virtual/environment`
2. Activate the virtual environment with `source /path/to/new/virtual/environment/bin/activate`
3. Create a file called `.env` in the project root directory (this is .gitignored) and add any private API keys, such as below.
   
```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

4. From the repo root directory, run `pip install -r requirements.txt`
5. Run `jupyter lab` to launch Jupyter and head over to the intro folder to get started.

Let me know if you hit problems, and try looking in the environment.yml file to see if there are clues for any other packages that need to be installed in your system.
Or... try Anaconda!!