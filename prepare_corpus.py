'''
This is the prepare_corpus module.

This module parses the downloaded PubTator file 
and replaces chemical/disease/gene with their IDs.
'''

import re

MIN_PMID = 1279087
pubtator_data = '/scratch/cheng.jial/nlp_corpus/pubmed_pubtator/bioconcepts2pubtatorcentral.offset'
output_path = '/scratch/cheng.jial/nlp_corpus/pubmed_pubtator/pmid'

def sentence_split(text):
    '''Source: https://stackoverflow.com/questions/4576077/python-split-text-on-sentences'''
    
    digits = "([0-9])"
    alphabets= "([A-Za-z])"
    prefixes = "(Mr|St|Mrs|Ms|Dr)[.]"
    suffixes = "(Inc|Ltd|Jr|Sr|Co)"
    starters = "(Mr|Mrs|Ms|Dr|He\s|She\s|It\s|They\s|Their\s|Our\s|We\s|But\s|However\s|That\s|This\s|Wherever)"
    acronyms = "([A-Z][.][A-Z][.](?:[A-Z][.])?)"
    websites = "[.](com|net|org|io|gov)"

    text = " " + text + "  "
    text = text.replace("\n"," ")
    text = re.sub(digits + "[.]" + digits,"\\1<prd>\\2",text)
    text = re.sub(prefixes,"\\1<prd>",text)
    text = re.sub(websites,"<prd>\\1",text)
    if "Ph.D" in text: text = text.replace("Ph.D.","Ph<prd>D<prd>")
    text = re.sub("\s" + alphabets + "[.] "," \\1<prd> ",text)
    text = re.sub(acronyms+" "+starters,"\\1<stop> \\2",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>\\3<prd>",text)
    text = re.sub(alphabets + "[.]" + alphabets + "[.]","\\1<prd>\\2<prd>",text)
    text = re.sub(" "+suffixes+"[.] "+starters," \\1<stop> \\2",text)
    text = re.sub(" "+suffixes+"[.]"," \\1<prd>",text)
    text = re.sub(" " + alphabets + "[.]"," \\1<prd>",text)
    if "”" in text: text = text.replace(".”","”.")
    if "\"" in text: text = text.replace(".\"","\".")
    if "!" in text: text = text.replace("!\"","\"!")
    if "?" in text: text = text.replace("?\"","\"?")
    text = text.replace(".",".<stop>")
    text = text.replace("?","?<stop>")
    text = text.replace("!","!<stop>")
    text = text.replace("<prd>",".")
    sentences = text.split("<stop>")
    sentences = sentences[:-1]
    sentences = [s.strip() for s in sentences]
    return sentences

def replace_with_correct_index(pmid, abstract, replace_dict, size=3):
    '''PubTator's index of bioconcepts is so noisy. 
       Check the range of window size for correct index.
       
       Input:
       replace_dict: dict of strings to be replaced, 
                     key:   start index; 
                     value: [end index, raw string, ID]'''

    keys = list(replace_dict.keys())
    keys.sort()
    end_prev = 0
    new_abstract = ''
    for k in keys:
        
        # Get the PubTator indeces
        start = k
        end   = replace_dict[k][0]
        
        # Get the strings
        raw   = replace_dict[k][1]
        new   = replace_dict[k][2]
        
        # If the PubTator indeces are correct, don't change
        if abstract[start:end] == raw:
            start_corr = start
            end_corr   = end
        
        # If the indeces are wrong, search raw string in a range of window size
        else:
            extended_range = abstract[start-size:end+size+1]
            
            # If the extended search string is too short, no need to search
            # Normally this won't happen
            if len(extended_range) < (end - start):
                continue 
            else:
                if raw in extended_range:
                    idx = extended_range.index(raw)
                else:
                    print("ERROR", pmid)
                    print("ERROR", raw)
                    continue
                
                # Update the indeces
                start_corr = start - size + idx
                end_corr   = start_corr + end - start
        
        # This is the actual repalcement
        new_abstract = new_abstract + abstract[end_prev:start_corr] + replace_dict[k][2]
        end_prev = end_corr
    
    new_abstract = new_abstract + abstract[end_prev:]
    return new_abstract

def parse_block(lines):
    '''Parse a block of data from one PMID.
    
    Block format:
    PMID|t|title
    PMID|a|abstract
    PMID \t index1 \t index2 \t raw text \t type \t ID
    ...
    
    Then replace raw string into ID.
    Format:
    CHEMICALMESHD[1-9]*, DISEASEMESHD[1-9]*, GENE[1-9]*
    To avoid any possible tokenization in any code.
    '''
    
    # Parse meta data
    line1 = lines[0].split('|t|'); line2    = lines[1].split('|a|')
    pmid  = line1[0];              pmid2    = line2[0]
    title = line1[1].strip('\n');  abstract = line2[1].strip('\n')
    assert pmid == pmid2
    if int(pmid) > MIN_PMID:
        
        # If the content is too short, no need to parse
        if len(title) < 2 or len(abstract) < 2:
            print("Skip:", pmid)
            
        else:

            # Parse the IDs, save to a dictionary
            len_t = len(title)
            title_replace = {}
            abs_replace   = {}
            for l in lines[2:]:
                data = l.split('\t')
                in_title = data[4] in ('Chemical', 'Disease', 'Gene') and \
                           int(data[2]) < len(title)
                in_abs   = data[4] in ('Chemical', 'Disease', 'Gene') and \
                           len(title) <= int(data[2]) < len(title+abstract)

                # There are many capital letters recognized as chemical elements
                # whereas they are just part of codes, e.g. type of disease
                # Don't change those.
                if (data[4] == 'Chemical') and (len(data[3])==1):
                    continue
                
                # Replace IDs in Title
                if in_title:
                    new_name = data[5].strip('\n').replace(':', '')        # Format the ID
                    title_replace[int(data[1])] = [int(data[2]), 
                                                   data[3], 
                                                   (data[4][0]+new_name).upper()]
                # Replace IDs in Abstract
                if in_abs:
                    new_name = data[5].strip('\n').replace(':', '')        # Format the ID
                    abs_replace[int(data[1])-len_t] = [int(data[2])-len_t, 
                                                       data[3], 
                                                       (data[4][0]+new_name).upper()]

            # Replace text with IDs
            new_title    = replace_with_correct_index(pmid, title, title_replace)
            new_abstract = replace_with_correct_index(pmid, abstract, abs_replace)

            # Write the abstract to disk
            if new_title or new_abstract:
                with open(f'{output_path}/{pmid}', 'w') as f:
                    if new_title: 
                        f.write(new_title)
                        f.write('\n')
                    if new_abstract:
                        lines = sentence_split(new_abstract)
                        for l in lines:
                            f.write(l)
                            f.write('\n')    
                print("Done:", pmid)
            else:
                print("Skip:", pmid) 
    else:
        print("Skip:", pmid)
    
if __name__ == "__main__":
    block = []
    with open(pubtator_data, 'r') as f:
        for line in f:
            if line == '\n':
                parse_block(block)
                block = []
            else:
                block.append(line)