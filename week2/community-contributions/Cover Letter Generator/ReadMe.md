Coverly is a simple web-application to generate cover letters for job applications based on Gradio UI. 
This serves as a simple exercise to demonstrate the skills learned until week2 of the LLM Engineering course.

What it does?
You can paste the link to the job posting and upload your resume via the Gradio UI. 
Once you hit "Generate Cover Letter" it will write a custom cover letter based on your inputs and making it available as a downloadable pdf.

How to run it?
It is written as a python script. You need to use your python environment to run it. Make sure you have installed the required libraries before hand.
Then Gradio launches a web-application in the browser and also provides a shareable link that lasts for a week.

Why is it not written as a Jupyter Notebook?
While running from a Jupyter Notebook would have been ideal to try things out and also make adaptations to fit to your needs, there seems to be a lot
of issues related to event looping owing to the interplay between Windows + Jupyter + Playwright. Running the application using a Python script means
you're running a normal Python process, which works perfectly fine with Playwright sync method calls, keeping the code simple.

