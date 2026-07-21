from openai import OpenAI
from models import ExperimentResult

client = OpenAI()

def run_experiment(experiment):
    messages = [
        {"role": "system", "content": experiment.system_prompt},
        {"role": "user", "content": experiment.user_input}
    ]
    
    try:
        response = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages
        )
    
        output_text = response.choices[0].message.content
        

        return ExperimentResult(
            experiment_name=experiment.name,
            task_type=experiment.task_type,
            response=output_text, 
            success=True, 
            error=None
        )
    
    except Exception as error:
        return ExperimentResult(
            experiment_name=experiment.name,
            task_type=experiment.task_type,
            response=None, 
            success=False, 
            error=str(error)
        )