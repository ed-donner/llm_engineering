# LLM Engineering - Master AI and LLMs

## Your 8 week journey to proficiency starts today

![Voyage](voyage.jpg)

I'm so happy you're joining me on this path. We'll be building immensely satisfying projects in the coming weeks. Some will be easy, some will be challenging, many will ASTOUND you! The projects build on each other so you develop deeper and deeper expertise each week. One thing's for sure: you're going to have a lot of fun along the way.

### A note before you begin

I'm here to help you be most successful with your learning! If you hit any snafus, or if you have any ideas on how I can improve the course, please do reach out in the platform or by emailing me direct (ed@edwarddonner.com). It's always great to connect with people on LinkedIn to build up the community - you'll find me here:  
https://www.linkedin.com/in/eddonner/

I'm still polishing up Week 8's code, but it's looking really terrific and I'll push it in the coming days.

### An important point on API costs

During the course, I'll suggest you try out the leading models at the forefront of progress, known as the Frontier models. I'll also suggest you run open-source models using Google Colab. These services have some charges, but I'll keep cost minimal - like, a few cents at a time.

Please do monitor your API usage to ensure you're comfortable with spend; I've included links below. There's no need to spend anything more than a couple of dollars for the entire course. During Week 7 you have an option to spend a bit more if you're enjoying the process - I spend about $10 myself and the results make me very happy indeed! But it's not necessary in the least; the important part is that you focus on learning.

### How this Repo is organized

There are folders for each of the "weeks", representing modules of the class.  
Follow the setup instructions below, then open the Week 1 folder and prepare for joy.

### The most important part

The mantra of the course is: the best way to learn is by **DOING**. You should work along with me, running each cell, inspecting the objects to get a detailed understanding of what's happening. Then tweak the code and make it your own. There are juicy challenges for you throughout the course. I'd love it if you wanted to push your code so I can follow along with your progress, and I can make your solutions available to others so we share in your progress.

## Setup instructions

By far the recommended approach is to use Anaconda for your environment. Even if you've never used it before, it makes such a difference. Anaconda ensures that you're working with the right version of Python and all your packages are compatible with mine, even if we're on different platforms.

**Update** Some people have had problems with Anaconda - horrors! The idea of Anaconda is to make it really smooth and simple to be working with the same environment. If you hit any problems with the instructions below, please skip to near the end of this README for the alternative approach using `pip`, and hopefully you'll be up and running fast. And please do message me if I can help with anything.

We'll be mostly using Jupyter Lab in this course. For those new to Jupyter Lab / Jupyter Notebook, it's a delightful Data Science environment where you can simply hit shift+enter in any cell to run it; start at the top and work your way down! When we move to Google Colab in Week 3, you'll experience the same interface for Python runtimes in the cloud.

### For PC Users

1. **Install Git** (if not already installed):

- Download Git from https://git-scm.com/download/win
- Run the installer and follow the prompts, using default options

2. **Open Command Prompt:**

- Press Win + R, type `cmd`, and press Enter

3. **Navigate to your projects folder:**

If you have a specific folder for projects, navigate to it using the cd command. For example:  
`cd C:\Users\YourUsername\Documents\Projects`

If you don't have a projects folder, you can create one:
```
mkdir C:\Users\YourUsername\Documents\Projects
cd C:\Users\YourUsername\Documents\Projects
```
(Replace YourUsername with your actual Windows username)

3. **Clone the repository:**

- Go to the course's GitHub page
- Click the green 'Code' button and copy the URL
- In the Command Prompt, type: `git clone <paste-url-here>`

4. **Install Anaconda:**

- Download Anaconda from https://docs.anaconda.com/anaconda/install/windows/
- Run the installer and follow the prompts
- A student mentioned that if you are prompted to upgrade Anaconda to a newer version during the install, you shouldn't do it, as there might be problems with the very latest update for PC. (Thanks for the pro-tip!)

5. **Set up the environment:**

- Open Anaconda Prompt (search for it in the Start menu)
- Navigate to the cloned repository folder using `cd path\to\repo`
- Create the environment: `conda env create -f environment.yml`
- Wait for a few minutes for all packages to be installed
- Activate the environment: `conda activate llms`  

You should see `(llms)` in your prompt, which indicates you've activated your new environment.

6. **Start Jupyter Lab:**

- In the Anaconda Prompt, type: `jupyter lab`

Congratulations! You're now ready to start coding. Enjoy your celebratory cup of coffee!

### For Mac Users

1. **Install Git** if not already installed (it will be in most cases)

- Open Terminal (Applications > Utilities > Terminal)
- Type `git --version` If not installed, you'll be prompted to install it

2. **Navigate to your projects folder:**

If you have a specific folder for projects, navigate to it using the cd command. For example:
`cd ~/Documents/Projects`

If you don't have a projects folder, you can create one:
```
mkdir ~/Documents/Projects
cd ~/Documents/Projects
```

3. **Clone the repository**

- Go to the course's GitHub page
- Click the green 'Code' button and copy the URL
- In Terminal, type: `git clone <paste-url-here>`

4. **Install Anaconda:**

- Download Anaconda from https://docs.anaconda.com/anaconda/install/mac-os/
- Double-click the downloaded file and follow the installation prompts

5. **Set up the environment:**

- Open Terminal
- Navigate to the cloned repository folder using `cd path/to/repo`
- Create the environment: `conda env create -f environment.yml`
- Wait for a few minutes for all packages to be installed
- Activate the environment: `conda activate llms`

You should see `(llms)` in your prompt, which indicates you've activated your new environment.

6. **Start Jupyter Lab:**

- In Terminal, type: `jupyter lab`

Congratulations! You're now ready to start coding. Enjoy your celebratory cup of coffee!

### When we get to it, creating your API keys

Particularly during weeks 1 and 2 of the course, you'll be writing code to call the APIs of Frontier models (models at the forefront of progress). You'll need to join me in setting up accounts and API keys.

- [GPT API](https://platform.openai.com/) from OpenAI
- [Claude API](https://console.anthropic.com/) from Anthropic
- [Gemini API](https://ai.google.dev/gemini-api) from Google

Initially we'll only use OpenAI, so you can start with that, and we'll cover the others soon afterwards. The webpage where you set up your OpenAI key is [here](https://platform.openai.com/api-keys). See the extra note on API costs below if that's a concern. One student mentioned to me that OpenAI can take a few minutes to register; if you initially get an error about being out of quota, wait a few minutes and try again. Another reason you might encounter the out of quota error is if you haven't yet added a valid payment method to your OpenAI account. You can do this by clicking your profile picture on the OpenAI website then clicking "Your profile." Once you are redirected to your profile page, choose "Billing" on the left-pane menu. You will need to enter a valid payment method and charge your account with a small advance payment. It is recommended that you **disable** the automatic recharge as an extra failsafe. If it's still a problem, see more troubleshooting tips in the Week 1 Day 1 notebook, and/or message me!

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

Learn about Google Colab and set up a Google account (if you don't already have one) [here](https://colab.research.google.com/)

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

### Alternative Setup Instructions if Anaconda is giving you problems

First please run:
`python --version`  
To find out which python you're on. Ideally you'd be using Python 3.11.x, so we're completely in sync. You can download python at  
https://www.python.org/downloads/

Here are the steps:

After cloning the repo, cd into the project root directory `llm_engineering`.
Then:

1. Create a new virtual environment: `python -m venv venv`  
2. Activate the virtual environment with  
On a Mac: `source venv/bin/activate`  
On a PC: `venv\Scripts\activate`
3. Run `pip install -r requirements.txt`
4. Create a file called `.env` in the project root directory and add any private API keys, such as below. (The next section has more detailed instructions for this, if you prefer.)
   
```
OPENAI_API_KEY=xxxx
GOOGLE_API_KEY=xxxx
ANTHROPIC_API_KEY=xxxx
HF_TOKEN=xxxx
```

5. Run `jupyter lab` to launch Jupyter and head over to the intro folder to get started.

Let me know if you hit problems.

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
