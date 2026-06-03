import pdb
from pricer.ci import Pricer
from unittest.mock import patch, MagicMock
import torch
import pytest
from transformers import BitsAndBytesConfig

BASE_MODEL = "meta-llama/Meta-Llama-3.1-8B"
PROJECT_NAME = "pricer"
HF_USER = "ed-donner" # your HF name here! Or use mine if you just want to reproduce my results.
RUN_NAME = "2024-09-13_13.04.39"
PROJECT_RUN_NAME = f"{PROJECT_NAME}-{RUN_NAME}"
REVISION = "e8d637df551603dc86cd7a1598a8f44af4d7ae36"
FINETUNED_MODEL = f"{HF_USER}/{PROJECT_RUN_NAME}"
MODEL_DIR = "hf-cache/"
BASE_DIR = MODEL_DIR + BASE_MODEL
FINETUNED_DIR = MODEL_DIR + FINETUNED_MODEL

@pytest.fixture
def pricer():
    return Pricer()

def test_wake_up():
    pricer = Pricer()
    assert pricer.wake_up() == "ok"


@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
@patch('transformers.AutoModelForCausalLM')
def test_setup(MockAutoModel, MockPeftModel, MockAutoTokenizer, pricer):
    # Setup mocks
    mock_tokenizer = MockAutoTokenizer.from_pretrained.return_value
    mock_model = MockAutoModel.from_pretrained.return_value
    mock_peft_model = MockPeftModel.from_pretrained.return_value
    
    # Call the setup method
    pricer.setup()
    
    # Assertions to ensure the setup method works correctly
    MockAutoTokenizer.from_pretrained.assert_called_once_with(BASE_DIR)
    assert pricer.tokenizer == mock_tokenizer
    assert pricer.tokenizer.pad_token == pricer.tokenizer.eos_token
    assert pricer.tokenizer.padding_side == "right"
    
    quant_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=torch.bfloat16,
            bnb_4bit_quant_type="nf4"
        )
    
    MockAutoModel.from_pretrained.assert_called_once_with(
        BASE_DIR, 
        quantization_config=quant_config, 
        device_map="auto"
        )
    assert pricer.base_model == mock_model
    
    MockPeftModel.from_pretrained.assert_called_once_with(mock_model, FINETUNED_DIR, revision=REVISION)
    assert pricer.fine_tuned_model == mock_peft_model


@patch('transformers.AutoTokenizer')
@patch('peft.PeftModel')
def test_price(MockPeftModel, MockAutoTokenizer, pricer):
 # Setup mocks
    mock_tokenizer = MockAutoTokenizer.return_value
    mock_tokenizer.encode.return_value = torch.tensor([[1, 2, 3]])
    mock_tokenizer.decode.return_value = "Price is $123.45"
    
    mock_model = MockPeftModel.return_value
    mock_model.generate.return_value = torch.tensor([[1, 2, 3, 4, 5]])
    
    # Assign mocks to the pricer instance
    pricer.tokenizer = mock_tokenizer
    pricer.fine_tuned_model = mock_model
    
    # Call the method
    description = "Test description"
    result = pricer.price(description)
    
    # Assert the result
    assert result == 123.45
