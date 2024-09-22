# LLM Engineering - Master AI and LLMs

## Your 8 week journey to proficiency starts today

![Voyage](voyage.jpg)

I'm so happy you're joining me on this path. We'll be building immensely satisfying projects in the coming weeks. Some will be easy, some will be challenging, many will ASTOUND you! The projects build on each other so you develop deeper and deeper expertise each week. One thing's for sure: you're going to have a lot of fun along the way.

### A note before you begin

I'm here to help you be most successful with your learning! If you hit any snafus, or if you have any ideas on how I can improve the course, please do reach out in the platform or by emailing me direct (ed@edwarddonner.com). It's always great to connect with people on LinkedIn to build up the community - you'll find me here:  
https://www.linkedin.com/in/eddonner/

I'm still polishing up the last couple of weeks of code, but it's looking really terrific and I'll push it in the coming days.

### An important point on API costs

During the course, I'll suggest you try out the leading models at the forefront of progress, known as the Frontier models. I'll also suggest you run open-source models using Google Colab. These services have some charges, but I'll keep cost minimal - like, a few cents at a time.

Please do monitor your API usage to ensure you're comfortable with spend; I've included links below. There's no need to spend anything more than a couple of dollars for the entire course. During Week 7 you have an option to spend a bit more if you're enjoying the process - I spend about $10 myself and the results make me very happy indeed! But it's not necessary in the least; the important part is that you focus on learning.

### How this Jupyter Lab is organized

There are folders for each of the "weeks", representing modules of the class.  
Follow the setup instructions below, then open the Week 1 folder and prepare for joy.

### The most important part

The mantra of the course is: the best way to learn is by **DOING**. You should work along with me, running each cell, inspecting the objects to get a detailed understanding of what's happening. Then tweak the code and make it your own. There are juicy challenges for you throughout the course. I'd love it if you wanted to push your code so I can follow along with your progress, and I can make your solutions available to others so we share in your progress.

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

Particularly during weeks 1 and 2 of the course, you'll be writing code to call the APIs of Frontier models (models at the forefront of progress). You'll need to join me in setting up accounts and API keys.

- [GPT API](https://platform.openai.com/) from OpenAI
- [Claude API](https://console.anthropic.com/) from Anthropic
- [Gemini API](https://ai.google.dev/gemini-api) from Google

Initially we'll only use OpenAI, so you can start with that, and we'll cover the others soon afterwards. See the extra note on API costs below if that's a concern. One student mentioned to me that OpenAI can take a few minutes to register; if you initially get an error about being out of quota, wait a few minutes and try again. If it's still a problem, message me!

Later in the course you'll be using the fabulous HuggingFace platform; an account is available for free at [HuggingFace](https://huggingface.co) - you can create an API token from the Avatar menu >> Settings >> Access Tokens.

And in Week 6/7 you'll be using the terrific [Weights & Biases](https://wandb.ai) platform to watch over your training batches. Accounts are also free, and you can set up a token in a similar way.

When you have these keys, please create a new file called `.env` in your project root directory. This file won't appear in Jupyter Lab because it's a hidden file; you should create it using something like Notepad (PC) or nano (Mac / Linux). I've put detailed instructions at the end of this README.

It should have contents like this, and to start with you only need the first line:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

This file is listed in the `.gitignore` file, so it won't get checked in and your keys stay safe.
If you have any problems with this process, there's a simple workaround which I explain in the video.

### Starting in Week 3, we'll also be using Google Colab for running with GPUs

You should be able to use the free tier or minimal spend to complete all the projects in the class. I personally signed up for Colab Pro+ and I'm loving it - but it's not required.

The colab links are in the Week folders and also here:  
- For week 3 day 1, this Google Colab shows what [colab can do](https://colab.research.google.com/drive/1DjcrYDZldAXKJ08x1uYIVCtItoLPk1Wr?usp=sharing)
- For week 3 day 2, here is a colab for the HuggingFace [pipelines API](https://colab.research.google.com/drive/1aMaEw8A56xs0bRM4lu8z7ou18jqyybGm?usp=sharing)
- For week 3 day 3, here's the colab on [Tokenizers](https://colab.research.google.com/drive/1WD6Y2N7ctQi1X9wa6rpkg8UfyA4iSVuz?usp=sharing)
- For week 3 day 4, we go to a colab with HuggingFace [models](https://colab.research.google.com/drive/1hhR9Z-yiqjUe7pJjVQw4c74z_V3VchLy?usp=sharing)
- For week 3 day 5, we return to colab to make our [Meeting Minutes product](https://colab.research.google.com/drive/1KSMxOCprsl1QRpt_Rq0UqCAyMtPqDQYx?usp=sharing)
- For week 7, we will use these Colab books: [Day 1](https://colab.research.google.com/drive/15rqdMTJwK76icPBxNoqhI7Ww8UM-Y7ni?usp=sharing) | [Day 2](https://colab.research.google.com/drive/1T72pbfZw32fq-clQEp-p8YQ4_qFKv4TP?usp=sharing) | [Days 3 and 4](https://colab.research.google.com/drive/1csEdaECRtjV_1p9zMkaKKjCpYnltlN3M?usp=sharing) | [Day 5](https://colab.research.google.com/drive/1igA0HF0gvQqbdBD4GkcK3GpHtuDLijYn?usp=sharing)

### Monitoring API charges

You can keep your API spend very low throughout this course; you can monitor spend at the dashboards: [here](https://platform.openai.com/usage) for OpenAI, [here](https://console.anthropic.com/settings/cost) for Anthropic and [here](https://console.cloud.google.com/apis/api/generativelanguage.googleapis.com/cost) for Google Gemini.

The charges for the exercsies in this course should always be quite low, but if you'd prefer to keep them minimal, then be sure to always choose the cheapest versions of models:
1. For OpenAI: Always use model `gpt-4o-mini` in the code instead of `gpt-4o`
2. For Anthropic: Always use model `claude-3-haiku-20240307` in the code instead of the other Claude models
3. During week 7, look out for my instructions for using the cheaper dataset

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

### Guide to creating the `.env` file

**For PC users:**

1. Open the Notepad (Windows + R to open the Run box, enter notepad)

2. In the Notepad, type the contents of the file, such as:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

3. Go to File > Save As. In the "Save as type" dropdown, select All Files. In the "File name" field, type ".env". Choose the root of the project folder and click Save.

4. Navigate to the foler where you saved the file in Explorer and ensure it was saved as ".env" not ".env.txt" - if necessary rename it to ".env"

**For Mac users:**

1. Open Terminal (Command + Space to open Spotlight, type Terminal and press Enter)

2. cd to your project root directory

cd /path/to/your/project

3. Create the .env file with

nano .env

4. Then type your API keys into nano:

```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Save the file:

Control + O  
Enter (to confirm save the file)  
Control + X to exit the editor

6. Use this command to list files in your file

`ls -a`

And confirm that the `.env` file is there.

Please do message me or email me at ed@edwarddonner.com if this doesn't work or if I can help with anything. I can't wait to hear how you get on.