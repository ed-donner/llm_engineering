# Importing the RAG Implementation

The folder names `community-contributions` and `clinton-d` contain hyphens, so they cannot be used in a normal dotted Python import.

For a file directly inside `week5`, such as `week5/app.py`:

```python
import sys
from pathlib import Path

contribution_dir = Path(__file__).resolve().parent / "community-contributions" / "clinton-d"
sys.path.insert(0, str(contribution_dir))

from answer import answer_question, fetch_context
```

For a file inside `week5/evaluation`, such as `week5/evaluation/eval.py`:

```python
import sys
from pathlib import Path

contribution_dir = (
    Path(__file__).resolve().parents[1] / "community-contributions" / "clinton-d"
)
sys.path.insert(0, str(contribution_dir))

from answer import answer_question, fetch_context
```

Run `ingest.py` before using `answer.py`. Both files use the database at `clinton-d/preprocessed_db`.
