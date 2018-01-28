# Setup and Installation

Create a new virtualenv and source it
```
virtualenv .ENV && source .ENV/bin/activate
```

then install the packages
```
pip install -r requirements.txt
```

Then install the spaCy language model for english
```
python -m spacy download en
```
