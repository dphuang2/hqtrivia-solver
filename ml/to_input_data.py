from pprint import pprint
import json
import pdb

questions_processed = json.load(open('questions_processed.json'))

DELIMITER = '|'

with open('regression.data', 'w') as f:
    for k,v in questions_processed.iteritems():
        lines = v['raw_data']['lines']
        for i in range(len(lines)):
            if len(lines[i]) != 10:
                pprint(v)
                exit()
            f.write(DELIMITER.join([str(v['right_answer'][i])] + [str(val) for val in lines]) + '\n')

print 'Successfully converted processed questions to input data!'
