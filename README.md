# Setup and Installation

Create a new virtualenv and source it
```
virtualenv .venv && source .venv/bin/activate
```

then install the packages
```
pip install -r requirements.txt
```

Then install the spaCy language model for english
```
python -m spacy download en_vectors_web_lg
```
