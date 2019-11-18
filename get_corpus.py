'''
This is the get_corpus module.

This module parses the downloaded PubTator file 
and replaces chemical/disease/gene with their IDs.
'''

from fd import *

MIN_PMID = 1279087

def parse_block(lines):
    
    '''Parse a block of data from one PMID.
    
    
    
    Block format:
    PMID|t|title
    PMID|a|abstract
    PMID \t index1 \t index2 \t raw text \t type \t ID
    ...
    '''
    
    # Parse meta data
    line1 = lines[0].split('|t|'); line2    = lines[1].split('|a|')
    title = line1[1].strip('\n');  abstract = line2[1].strip('\n')
    pmid  = line1[0];              pmid2    = line2[0]
    assert pmid == pmid2
    if int(pmid) > MIN_PMID:
        if len(title) < 2 or len(abstract) < 2:
            print("Skip:", pmid)
        else:
            if title[-1] == ' ':
                abstract = title.strip() + '.' + abstract
            elif title[-1] == '.':
                abstract = title + abstract
            else:
                abstract = title[:-1] + '.' + abstract

            # Parse the IDs, save to a dictionary
            to_be_replaced = {}
            for l in lines[2:]:
                data = l.split('\t')
                flag = (data[4] in ('Chemical', 'Disease', 'Gene')) and (int(data[2]) < len(abstract))

                # There are many capital letters recognized as chemical elements
                # whereas they are just part of codes, e.g. type of disease
                # Don't change those.
                if (data[4] == 'Chemical') and (len(data[3])==1):
                    continue
                if flag:
                    to_be_replaced[int(data[1])] = [int(data[2]), data[4].upper()+':'+data[5].strip('\n').upper()]

            # Replace text with IDs
            keys = list(to_be_replaced.keys())
            keys.sort()
            start = 0
            new_abstract = ''
            for k in keys:
                end = k
                new_abstract = new_abstract + abstract[start:end] + to_be_replaced[k][1]
                start = to_be_replaced[k][0]
            new_abstract = new_abstract + abstract[start:]

            # Write the abstract to disk
            with open(f'/scratch/cheng.jial/pubmed/pmid/{pmid}', 'w') as f:
                f.write(new_abstract)
            print("Done:", pmid)
    else:
        print("Skip:", pmid)
    
if __name__ == "__main__":
    block = []
    with open(f'/scratch/cheng.jial/pubmed/bioconcepts2pubtatorcentral.offset', 'r') as f:
        for line in f:
            if line == '\n':
                parse_block(block)
                block = []
            else:
                block.append(line)