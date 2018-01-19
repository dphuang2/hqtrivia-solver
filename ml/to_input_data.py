import json

questions_processed = json.load(open('questions_processed.json'))

DELIMITER = '|'

with open('regression.data', 'w') as f:
    for k,v in questions_processed.iteritems():
        for line in v['lines']:
            if len(line) != 7:
                print line
                exit()
            f.write(DELIMITER.join([str(v) for v in line]) + '\n')

print 'Successfully converted processed questions to input data!'
