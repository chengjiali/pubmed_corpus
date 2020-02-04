'''
This is the parse_dependency module.

This module parses the PubMed abstract after NER
and returns shortest dependency path 
between all entities greedily.
'''

import os
import re
import spacy
import networkx as nx
import mpi4py.MPI as MPI

corpus = '/scratch/cheng.jial/pubmed/pmid'
output_path = '/scratch/cheng.jial/foodome/data/graph_table'

chemical_pattern = re.compile('CHEMICAL[A-Z]*\S[0-9]*')
disease_pattern = re.compile('DISEASE[A-Z]*\S[0-9]*')

# total = 20075213

nlp = spacy.load("en_core_web_lg")

def find_all_bio(s, pat):
    '''Find all the BioConcept IDs in the string'''
    return pat.findall(s)

def is_chemical(s):
    return re.match(chemical_pattern, s)

def is_disease(s):
    return re.match(disease_pattern, s)

def get_dep(start, end, graph):
    '''Find shortest dependency path start-end in graph.'''
    
    graph  = nx.Graph(edges)
    path   = nx.shortest_path(graph, source=start, target=end)
    
    return path[1:-1]

def format_output(line, dp):
    return f'{line}\t{dp[0].text}\t{dp[-1].text}\t{dp}'

def parse_file(pmid):
    '''Parse an abstract. Read the lines and call parse_line'''
    
    with open(f'{corpus}/{pmid}') as f:
        lines = f.readlines()
    result = [parse_line(l) for l in lines]
    result = sum(result, [])

    # If we get dependency path(s), write to disk
    if result:
        with open(f'{output_path}/{pmid}', 'w') as f:
            for i in result:
                f.write(f'{pmid}\t{i}')     # Add the pmid
                f.write('\n')
                
def parse_line(line):
    '''Parse a single sentence. NER + DP'''
    
    line = line.strip('\n')

    # If a line contains no chemical or disease, no need to parse
    if (len(set(find_all_bio(line, chemical_pattern))) == 0 or 
        len(set(find_all_bio(line, disease_pattern))) == 0):
        return []

    # Dependency parsing with SpaCy
    doc = nlp(line)
    result = []
    edges = []
    chemicals = []
    diseases = []

    # Create nx graph, token as node, dep path as edge
    graph = nx.Graph()
    for token in doc:
        graph.add_node(token)
        for child in token.children:
            graph.add_edge(token, child)

        # NER. Find the chemical, disease
        if is_chemical(token.text):
            chemicals.append(token)
        if is_disease(token.text):
            diseases.append(token)

    # Find shortest dependency path with networkX
    for c in chemicals:
        for d in diseases:
            try:
                dps = nx.all_shortest_paths(graph, source=c, target=d)
                result.extend([format_output(line, dp) for dp in dps])
            except nx.NetworkXNoPath:
                print("NOPATH!!", line, c, d)                
                
    return result
        
        
comm = MPI.COMM_WORLD
rank = comm.Get_rank()
size = comm.Get_size()

if __name__ == "__main__":
    
    pmid_list = os.listdir(corpus)
    total = len(pmid_list)
    
    # Split the PMIDs across the processes
    # The last process takes the remainder
    s = rank * total//size
    e = s + total//size
    local_pmid = pmid_list[s:e]
    if rank == size - 1:
        local_pmid = pmid_list[s:]
    
    _ = [parse_file(pmid) for pmid in local_pmid]
    

"""
class Node():
    '''Hashable node for networkX. Format (token, token_index)'''
    
    def __init__(self, token, index):
        self.token = token
        self.index = index
    
    def __str__(self):
        return f'{self.token}!!{self.index}'
    
    def __eq__(self, other):
        return (self.token == other.token) and (self.index == other.index)
    
    def __hash__(self):
        return hash(str(self))
"""