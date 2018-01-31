from pprint import pprint
import json
import pdb

questions_processed = json.load(open('questions_processed.json'))
# questions_processed = {k:v for k,v in questions_processed.iteritems() if len(v['raw_data']['lines'][0]) != 11}
# with open('questions_processed.json', 'w') as f:
    # json.dump(questions_processed, f, indent=4, separators=(',', ': '))

DELIMITER = '|'

with open('regression.data', 'w') as f:
    for k,v in questions_processed.iteritems():
        lines = v['raw_data']['lines']
        for i in range(len(lines)):
            if len(lines[i]) != 15:
                pprint(v)
                exit()
            f.write(DELIMITER.join([str(v['right_answer'][i])] + [str(val) for val in lines[i]]) + '\n')

print 'Successfully converted processed questions to input data!'
