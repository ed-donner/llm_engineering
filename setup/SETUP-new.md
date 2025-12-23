# LLM Engineering - Master AI and LLMs

## New Setup instructions for PC, Mac and Linux

**These are the Setup instructions for the new version of the course as of October 2025. For the original versions (Anaconda) please see the other files in this directory for your platform.**

_If you're looking at this in Cursor, please right click on the filename in the Explorer on the left, and select "Open preview", to view the formatted version._

Welcome, LLM engineers in the making!

I should confess up-front: setting up a powerful environment to work at the forefront of AI is not as simple as I'd like. For most people these instructions will go great; but in some cases, for whatever reason, you'll hit a problem. Please don't hesitate to reach out - I am here to get you up and running quickly. There's nothing worse than feeling _stuck_. Message me in Udemy or email me and I will unstick you quickly!

Email: ed@edwarddonner.com  
LinkedIn: https://www.linkedin.com/in/eddonner/  

## Step 0 - Before we begin - addressing the "GOTCHAS" which trip up many people:

Ignore this section at your peril! 80% of the questions I get about setup are solved by these very common system issues.

1. PC people: Permissions. Please take a look at this [tutorial](https://chatgpt.com/share/67b0ae58-d1a8-8012-82ca-74762b0408b0) on permissions on Windows. If you ever have an error that you don't have the rights / permissions / ability to run a script or install software, then read this first. ChatGPT can tell you everything you need to know about Permissions on Windows.

2. Anti-virus, Firewall, VPN. These can interfere with installations and network access; try temporarily disabling them as needed. Use a hotspot on your phone to prove whether it's a network issue.

3. PC people: The evil Windows 260 character limit to filenames - here is a full [explanation and fix](https://chatgpt.com/share/67b0afb9-1b60-8012-a9f7-f968a5a910c7)! 

4. PC people: If you've not worked with Data Science packages on your computer before, you might need to install Microsoft Build Tools. Here are [instructions](https://chatgpt.com/share/67b0b762-327c-8012-b809-b4ec3b9e7be0). A student also mentioned that [these instructions](https://github.com/bycloudai/InstallVSBuildToolsWindows) might be helpful for people on Windows 11. 

5. Mac people: If you're new to developing on your Mac, you may need to install XCode developer tools. Here are [instructions](https://chatgpt.com/share/67b0b8d7-8eec-8012-9a37-6973b9db11f5).

6. SSL and other network issues due to Corporate Security: if you ever get issues with SSL, such as an API Connection issue or any certificate issue, or an error trying to download files from Ollama (a Cloudflare error) then see Q15 [here](https://edwarddonner.com/faq)

## STEP 1 - installing git, projects directory, Cursor

This is the only section with separate steps for PC people and Mac/Linux people! Please pick your section below, then reconvene for Step 2...

___

**STEP 1 FOR PC people:**

1. **Install Git** (if not already installed):

- Open a new Powershell Prompt (start menu >> Powershell). If you ever have permissions errors, try opening the Powershell by right clicking and selecting "run as Administrator"
- Run the command `git` and see if it responds with details of the command or an error
- If you get an error, download Git from https://git-scm.com/download/win
- Run the installer and follow the prompts, using default options (press OK lots of times!)

2. **Create projects directory as needed**

- Open a new Powershell prompt, as in prior step. You should be in your home directory, like `C:\Users\YourUserName`
- Do you have a projects directory? Find out by typing `cd projects`
- If that has an error, then create a projects directory: `mkdir projects` then `cd projects`
- Now you should be in `C:\Users\YourUserName\projects`
- You can locate this anywhere convenient for you, but avoid any directories that are on your OneDrive

3. **Do a git clone:**

Enter the clone command below in the command prompt in the `projects` folder. If this gives you an error about long filenames, please do #3 in the "gotchas" section at the top, and then restart your computer, and you might also need to run this: `git config --system core.longpaths true`

Here's the clone command:

`git clone https://github.com/ed-donner/llm_engineering.git`

This creates a new directory `llm_engineering` within your projects folder and downloads the code for the class.  
Do `cd llm_engineering` to go into it. This `llm_engineering` directory is known as the "project root directory".

4. **Cursor** Install Cursor if needed and open the project:

Visit https://cursor.com

Click Download for Windows. Then run the installer. Accept and pick defaults for everything..

Then go to Start menu, enter cursor. Cursor will come up, and you might need to answer questions. Then you should see the 'new window' screen where you can click "Open Project". If not, go to File menu >> New Window. Then click "Open Project".

Find your llm_engineering directory within your projects directory. Double click on llm_engineering so you're looking at the contents of llm_engineering. Then click Open or Open Folder.

Cursor should then open up llm_engineering. You know you're in good shape if you see LLM_ENGINEERING in block caps on the top left.

___

**STEP 1 FOR MAC/LINUX PEOPLE**

1. **Install Git** (if not already installed):

Open a Terminal: on Mac, open a Finder window, go to Applications >> Utilities >> Terminal. On Linux, you people live in Terminals.. you hardly need instructions from me!

- Run `git --version` and you should see a git version number. If not, you should get instructions on how to install it, or follow gotcha #5 at the top of this doc.

2.  **Create projects directory as needed**

- Open a new Terminal window, as in prior step. Type `pwd` to see where you are. You should be in your home directory, like `/Users/username`
- Do you have a projects directory? Find out by typing `cd projects`
- If that has an error, then create a projects directory: `mkdir projects` then `cd projects`
- If you now do `pwd` you should be in `/Users/username/projects`
- You can locate this anywhere convenient for you, but avoid any directories that are on your icloud

3. **Do a git clone:**

Enter this in the command prompt in the Projects folder:

`git clone https://github.com/ed-donner/llm_engineering.git`

This creates a new directory `llm_engineering` within your projects folder and downloads the code for the class.  
Do `cd llm_engineering` to go into it. This `llm_engineering` directory is known as the "project root directory".

4. **Cursor** Install Cursor if needed and open the project:

Visit https://cursor.com

Click Download for Mac OS. Or Linux. Then run the installer. Accept and pick defaults for everything..

Then go to Start menu, enter cursor. Cursor will come up, and you might need to answer questions. Then you should see the 'new window' screen where you can click "Open Project". If not, go to File menu >> New Window. Then click "Open Project".

Find your llm_engineering directory within your projects directory. Double click on llm_engineering so you're looking at the contents of llm_engineering. Then click Open.

Cursor should then open up llm_engineering. You know you're in good shape if you see LLM_ENGINEERING in block caps on the top left.

___

## STEP 2: Installing the fabulous **uv** then doing a `uv sync`

For this course, we're using uv, the blazingly fast package manager. It's really taken off in the Data Science world -- and for good reason.

It's fast and reliable. You're going to love it!

First, within Cursor, select View >> Terminal, to see a Terminal window within Cursor. Type `pwd` to check you're in the project root directory.

Now type `uv --version` to see if uv is installed. If you get a version number, then terrific! But if you get an error, then follow the instructions here to install uv - I recommend using the Standalone Installer approach at the very top, but you can use any approach. Run commands in the Cursor installer. If one approach doesn't work for you, then try another.

https://docs.astral.sh/uv/getting-started/installation/

Once you've installed uv, you need to open a new terminal window in Cursor (the plus sign or Ctrl+shift+backtick) for `uv --version` to work. Please check!

Any problems with uv installation or using uv, please see [Q11 on my FAQ page](https://edwarddonner.com/faq/#11) for a full briefing.

### Now that it's installed:

Run `uv self update` to make sure you're on the latest version of uv.

And now simply run this:  
`uv sync`  
uv should install everything blazingly fast. Any problems, please see [Q11 on my FAQ page](https://edwarddonner.com/faq/#11).

You now have a full spec environment!!

Using uv is simple and fast:  
1. Instead of `pip install xxx` you do `uv add xxx`  
2. You never need to activate an environment - uv does it for you.  
3. Instead of `python xxx` you do `uv run xxx`

___

## STEP 3 - OPTIONAL - Set up OpenAI Account

Alternative: see Guide 9 in the guides folder for free alternatives!

Go to https://platform.openai.com

- Click Sign Up to create an account if you don't have one. You might need to click some buttons to create an Organization first - just put in sensible defaults. See Guide 4 in the Guides folder if you're unsure about the differences between ChatGPT and the OpenAI API.
- Click on the Settings icon on the top right, and then Billing on the left sidebar navigation.
- Ensure Auto-Recharge is off. As needed, "Add to Credit Balance" and pick the $5 up-front payment amount, be sure that you add a proper payment method
- Still in Settings, select API keys in the left sidebar (near the top)
- Press "Create new secret key" - select "Owned by you", give it any name you want, for the project select "Default project", leave Permissions at All
- Press "Create secret key" and you should see your new key. Press Copy to copy it into your clipboard.

___

## STEP 4 - needed for any model like OpenAI or Gemini, but not needed if you only use Ollama - create (and SAVE) your .env file

**Be dilligent with this section!** - any mistakes with your key will be very hard to track down!! I get a huge volume of questions from students who make a mistake with one of these steps... Above all, remember to save the file after you change it.

1. Create your `.env` file

- Go back to Cursor
- In the File Explorer on the left, right click in the blank space at the bottom of all your files, select "New File" and call your file `.env`
- I can't stress this enough: the file needs to be called PRECISELY `.env` - those four characters, no more and no less. Not ".env.txt" and not "john.env" and not "openai.env" and not anything else! And it needs to be within the project root.

If you're wondering why I rant about this: I get many, many frustrated people contacting me who (despite all my appeals) have named the file something else and think it's OK. It's not OK! It needs to be called `.env` in the llm_engineering directory 😂

2. Populate your `.env` file and then Save it:

Select the file on the left. You should see an empty blank file on the right. And type this into the contents of the file in the right:

`OPENAI_API_KEY=`

And then press paste! You should now see something like this:

`OPENAI_API_KEY=sk-proj-lots-and-lots-of-digits`

But obviously with your actual key there, not the words "sk-proj-lots-and-lots-of-digits"..

Now be sure to SAVE the file! File >> Save or Ctrl+S (PC) or Command+S (Mac). Many people forget to Save. You need to Save the file!

You should see a Stop sign by the .env file - don't be concerned.. this is a good thing! See Q7 [here](https://edwarddonner.com/faq) if you want to understand why.

__

## STEP 5 - Install Cursor Extensions, Open Day 1, Set the Kernel and GO!

(If you are prompted in Cursor to install recommended extensions, just say yes! That is a nice shortcut for this step.)

- Go to view menu and select Extensions.  
- Search for "python" to bring up the Python extensions. Select the Python extension made by "ms-python" or by "anysphere" and install it if not already installed.  
- Search for "jupyter" and select the extension made by "ms-toolsai" and install it if not already installed.

Now go to View >> Explorer. Open the week1 folder, and click on `day1.ipynb`.

- See where it says "Select Kernel" near the top right? Click that.. then pick "Python Environments"
- Pick the top option with a star that should say something like `.venv (Python 3.12.x) .venv/bin/python Recommended`
- If this doesn't come up, please go to the troubleshooting lab in the Setup folder.

# CONGRATULATIONS!! You made it! The rest of the course is easy 😂

**One final note:**

Early on in the course (on Day 2), I give a demo of a very cool, popular product called Claude Code. It's an AI coding tool, similar to Cursor that we use on the course. I'm only showing this as an example of Agentic AI in action; it's not a tool that's covered explicitly on this course, particularly as we're in Cursor. But if you want to use Claude Code yourself, the Quick Start guide from Anthropic is [here](https://docs.claude.com/en/docs/claude-code/quickstart).