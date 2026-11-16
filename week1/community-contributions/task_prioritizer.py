# imports

import os
from dotenv import load_dotenv
from openai import OpenAI

# initialize OpenAI client
load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")

openai = OpenAI(api_key=api_key)


# ------------------------------------------------------------
# STEP 1: COLLECT TASKS FROM THE USER
# ------------------------------------------------------------

def get_tasks():

    print("\n========== TASK PRIORITIZER ==========")
    print("Enter your tasks in the following format:")
    print("Task : Priority")
    print("Type # when finished.\n")

    tasks = []
    priorities = []

    while True:

        line = input("> ").strip()

        # Stop entering tasks
        if line == "#":
            break

        # Ignore empty lines
        if not line:
            continue

        # Check input format
        if ":" not in line:
            print("Invalid format. Use: Task : Priority")
            continue

        # Split at the last colon
        task, priority = line.rsplit(":", 1)

        task = task.strip()
        priority = priority.strip()

        if not task or not priority:
            print("Both task and priority are required.")
            continue

        # Validate priority
        if priority.lower() not in ["critical", "high", "medium", "low"]:
            print("Priority must be Critical, High, Medium or Low.")
            continue

        tasks.append(task)
        priorities.append(f"{task}: {priority}")

    return tasks, priorities

# ------------------------------------------------------------
# STEP 2: Create the messages for the OpenAI API
# ------------------------------------------------------------

def messages_for(tasks, priorities):


    system_prompt = """ 
    You are an intelligent task prioritization assistant.

    Your objective is to transform an unstructured list of tasks into a practical, actionable and prioritized action plan.

    Your responsibilities:

    Analyze the tasks and their associated priorities.
    Identify critical and time-sensitive tasks.
    Identify quick wins (tasks requiring less than 5 minutes).
    Break down large or complex tasks into manageable subtasks.
    Estimate realistic completion times.
    Preserve the original intent of every task.
    Identify dependencies between tasks where relevant.

    Be pragmatic. Avoid unnecessary task decomposition and overly optimistic time estimates.

    If information is insufficient, explicitly indicate when an estimate or priority is uncertain.

    Respond in Markdown. Never wrap the Markdown response in a code block.
    """
    user_prompt = """
   Please prioritize the following tasks:

    {tasks}

    Priorities:

    {priorities}

    Additional instructions:

    Apply the following prioritization order:

    - Critical or time-sensitive tasks.
    - Quick wins (tasks requiring less than 5 minutes).
    - Remaining tasks, ordered by their assigned priority (highest first).
    - Break large tasks into manageable subtasks where appropriate.
    - Estimate the duration of each task and subtask.
    - Preserve the original intent of every task.
    - Identify dependencies and respect their execution order.

    Expected output:

    - Return a practical, prioritized action plan in Markdown.

    - Finish with a brief summary of the number of tasks and estimated total execution time.
    """
    tasks_text = "\n".join(f"- {task}" for task in tasks)
    priorities_text = "\n".join(f"- {priority}" for priority in priorities)

    return [
        {"role": "system", "content": system_prompt},
        {
            "role": "user",
            "content": user_prompt.format(
                tasks=tasks_text,
                priorities=priorities_text
            )
        }
    ]

# ------------------------------------------------------------
# STEP 3: SEND REQUEST TO OPENAI
# ------------------------------------------------------------


def prioritize(tasks, priorities):

    response = openai.chat.completions.create(
        model="gpt-4.1-mini",
        messages=messages_for(tasks, priorities)
    )

    return response.choices[0].message.content

    print(prioritize(tasks, priorities))

# ------------------------------------------------------------
# STEP 4: MAIN APPLICATION
# ------------------------------------------------------------


def main():

   # Collect tasks
    tasks, priorities = get_tasks()

    # Check whether tasks were entered
    if not tasks:
        print("\nNo tasks entered. Exiting.")
        return

    print(f"\nProcessing {len(tasks)} tasks...")

    try:
        # Prioritize tasks using OpenAI
        result = prioritize(tasks, priorities)

        # Display result
        print("\n========== PRIORITIZED TASKS ==========\n")
        print(result)

    except Exception as error:
        print(f"\nAn error occurred: {error}")


# ------------------------------------------------------------
# STEP 5: EXECUTE APPLICATION
# ------------------------------------------------------------

if __name__ == "__main__":
    main()