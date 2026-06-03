from openai import OpenAI
from dotenv import load_dotenv
import os
import pypdf

class ResumeBasedJobRecommendation:
    def __init__(self, path: str):
        self.resume_path = path

    # method to read the content from the resume and use it for the user prompt
    def read_resume(self):
        """method to read the content from the resume and use it for the user prompt.

        Returns:
            content (str): returns the content of the resume.
        """        
        try:
            pdfreader = pypdf.PdfReader(self.resume_path)
            data = ""
            for page_number in range(pdfreader.get_num_pages()):
                page = pdfreader.pages[page_number]
                data += page.extract_text()
        except FileNotFoundError as e:
            print(f"Issue with the resume file path: {str(e)}")
            return
        except Exception as e:
            print(f"Couldn't able to parse the pdf : {str(e)}")
            return
        return data
    
    #
    def message_prompt(self, data: str, job_sites: list, location: str):
        """method suggests the appropriate job roles and provides the search link from job sites based on users input of resume data, job boards and location.

        Args:
            data (str): resume content for user prompt
            job_sites (list): job searching sites for user prompt
            location (str): location of job search

        Returns:
            content (str): Provides summary of resume with suggested job roles and links using gpt 4.o model.
        """        
        self.message = [
            {"role": "system", 
             "content": "You are an assistant that analysizes the resume data and summarize it. \
              Based on the summarization, you suggest the appropriate job roles \
              and provide the appropriate job search links for each suggested roles from the job sites based on filtering by the \
              location provided. "
            },
            {
                "role": "user",
                "content": f"Below is my resume content, kindly look for the appropriate job openings in \
                {job_sites} for location {location}:\n{data}"
            }]
        self.response = openai.chat.completions.create(model='gpt-4o-mini', messages=self.message)
        return self.response.choices[0].message.content


if __name__ == '__main__':
    # load the api key from .env and check if it is valid.
    load_dotenv()

    api_key = os.getenv('OPENAI_API_KEY')

    if api_key is None:
        print("No api key was found.")
        exit()
    elif not api_key.startswith('sk-proj-'):
        print("api key is present but it is not matching with the openai api key pattern starting with sk-proj-. Please check it.")
        exit()
    elif api_key.strip() != api_key:
        print("api key is good but it seems it has the spaces at starting or the end. Please check and remove it.")
        exit()
    else:
        print("api key is found and it looks good.")

    openai = OpenAI()

    #Provide the valid resume path
    file_path = input("Kindly enter the resume path:\n")
    if not file_path:
        print("Resume path is not provided. Kindly provide the valid path.")
        exit()
    
    obj = ResumeBasedJobRecommendation(file_path)
    data = obj.read_resume()

    if not data:
        pass
    else:
        #provide the input for the job sites to search and valid job location
        job_sites = input("Enter the job sites with space between each other: ")
        if not job_sites:
            print("Didn't provided the job sites to search for. Going with Linkedin, Indeed, Glassdoor and Naukri as defaults.")
            job_sites = ['LinkedIn', 'Indeed', 'Naukri', 'Glassdoor']
        else:
            job_sites = job_sites.split(' ')
        location = input("Enter the job location:")
        if not location:
            print("No location has been provided. Default will consider as United States.")
            location = 'United States'
        
        response = obj.message_prompt(data, job_sites, location)
        print(response)
