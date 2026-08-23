from argparse import ArgumentParser
import os
from dotenv import load_dotenv
from openai import OpenAI
import anthropic
from utils import add_doc_string, Model, get_system_message
from pathlib import Path


def main():

    # get run time arguments
    parser = ArgumentParser(
        prog='Generate Doc String for an existing functions',
        description='Run Doc String for a given file and model',
    )
    parser.add_argument(
        '-fp',
        '--file_path',
        help='Enter the file path to the script that will be updated with doc strings',
        default=None
    )
    parser.add_argument(
        '-llm',
        '--llm_model',
        help='Choose the LLM model that will create the doc strings',
        default='claude'
    )

    # get run time arguments
    args = parser.parse_args()
    file_path = Path(args.file_path)
    llm_model = args.llm_model

    # check for file path
    assert file_path.exists(), f"File Path {str(file_path.as_posix())} doesn't exist. Please try again."

    # check for value llm values
    assert llm_model in ['gpt', 'claude'], (f"Invalid model chosen '{llm_model}'. "
                                            f"Please choose a valid model ('gpt' or 'claude')")

    # load keys and environment variables
    load_dotenv()
    os.environ['OPENAI_API_KEY'] = os.getenv('OPENAI_API_KEY', 'your-key-if-not-using-env')
    os.environ['ANTHROPIC_API_KEY'] = os.getenv('ANTHROPIC_API_KEY', 'your-key-if-not-using-env')
    os.environ['HF_TOKEN'] = os.getenv('HF_INF_TOKEN', 'your-key-if-not-using-env')

    # get system messages
    system_message = get_system_message()

    # get model info
    model_info = {
        'gpt': {
            'client': OpenAI(),
            'model': Model.OPENAI_MODEL.value,
        },
        'claude': {
            'client': anthropic.Anthropic(),
            'model': Model.CLAUDE_MODEL.value
        }
    }

    # add standard argumens
    model_info[llm_model].update(
        {
            'file_path': file_path,
            'system_message': system_message
        }
    )

    # convert python code to c++ code using open ai
    print(f"\nSTARTED | Doc Strings Using {llm_model.upper()} for file {str(file_path)}\n\n")
    add_doc_string(**model_info[llm_model])
    print(f"\nFINISHED | Doc Strings Using {llm_model.upper()} for file {str(file_path)}\n\n")


if __name__ == '__main__':

    main()






