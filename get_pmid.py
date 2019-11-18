'''
This is the get_pmid module.

This module collects all the PMIDs from 1990-present. 
In total 21,201,991 PMIDs.
Updated on 2019-10-18.
'''

from fd import *

import json
import requests


def form_url(retstart, retmax=100000):
    return f'https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&\
term=(%221990/01/01%22[Date%20-%20Publication]%20:%20%223000%22[Date%20-%20Publication])\
&usehistory=y&retstart={retstart}&RetMax={retmax}&retmode=json'


if __name__ == "__main__":
    total_count = json.loads(requests.get(form_url(0, 1)).text)['esearchresult']['count']
    total_count = int(total_count)
    print(f"Total amound of PMIDs: {total_count}")
    
    # Get the PMIDs
    # Each time get #retmax PMIDs
    retmax = 100000
    pmid = []
    j = 0
    for i in range(total_count//retmax+1):
        try:
            pmid.extend(json.loads(requests.get(form_url(i*retmax)).text)['esearchresult']['idlist'])
            if j % 10 == 0:
                print("step:", j)
            j += 1
        except e:
            print(e)
            
    assert len(pmid) == total_count
    
    pmid = [int(i) for i in pmid]
    with open(f'{WD}/data/pmid_list.pkl', 'wb') as f:
        pickle.dump(pmid, f)
    print(f"Minimum PMID: {min(pmid)}")
