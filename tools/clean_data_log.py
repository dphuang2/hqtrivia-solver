import pdb
import json

# Read file
with open('../data/log', 'r') as f:
    content = f.read()

# Filter content and write
with open('../data/log', 'w') as f:
    for line in content.split('\n'):
        try:
            data = json.loads(line)
        except ValueError:
            continue
        try:
            if data["type"] == "question" or data["type"] == "questionSummary":
                f.write(line + '\n')
        except KeyError:
            continue

