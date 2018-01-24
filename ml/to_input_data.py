from pprint import pprint
import json
import pdb

questions_processed = json.load(open('questions_processed.json'))

DELIMITER = '|'

with open('regression.data', 'w') as f:
    for k,v in questions_processed.iteritems():
        for line in v['lines']:
            if len(line) != 10:
                pprint(v)
                exit()
            f.write(DELIMITER.join([str(val) for val in line]) + '\n')

print 'Successfully converted processed questions to input data!'
