```python
import IPython
IPython.Application.instance().kernel.do_shutdown(True)
```
## It clears Vram and ram so for the new cell it can utilize full memory

# for secret key acces like api or hugging face token

## colab=
```python
hf_token = userdata.get('HF_TOKEN')
if hf_token and hf_token.startswith("hf_"):
  print("HF key looks good so far")
else:
  print("HF key is not set - please click the key in the left sidebar")
login(hf_token, add_to_git_credential=True)
```

## kaggle=
```python
from kaggle_secrets import UserSecretsClient
from huggingface_hub import login

user_secrets = UserSecretsClient()
hf_token = user_secrets.get_secret("HF_TOKEN")

if hf_token and hf_token.startswith("hf_"):
    print("HF key looks good so far")
    login(hf_token)
else:
    print("HF key is not set correctly")

```