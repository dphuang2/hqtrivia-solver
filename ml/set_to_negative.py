import json

questions_processed = json.load(open('questions_processed.json'))

for k,v in questions_processed.iteritems():
    if v['raw_data']['negative_question']:
        for line in v['lines']:
            for i in range(1, len(line)):
                line[i] = 1 - line[i]

print 'Successfully reversed values of all negative questions'

with open('questions_processed.json', 'w') as f:
    json.dump(questions_processed, f, indent=4, separators=(',', ': '))

print 'Successfully wrote new questions_processed.json'

