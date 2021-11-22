"""
Author: Mohit Mayank

Load and return the Game of Thrones dataset

Data details:
1. 
"""

# imports
import os
import pandas as pd
from jaal import ontor
from jaal.ontor import OntoEditor

# data load and return function
def load_got(filter_conections_threshold=10):
    """Load the first book of the Got Dataset

    Parameters
    -----------
    filter_conections_threshold: int
        keep the connections in GoT dataset with weights greater than this threshold 
    """
    # resolve path
    this_dir, _ = os.path.split(__file__)
    # load the edge and node data
    edge_df = pd.read_csv(os.path.join(this_dir, "got", "class_edges.csv"))
    # edge_df = pd.read_csv(os.path.join(this_dir, "got", "got_edge_df.csv"))
    node_df = pd.read_csv(os.path.join(this_dir, "got", "class_axioms.csv"))
    # node_df = pd.read_csv(os.path.join(this_dir, "got", "got_node_df.csv"))
    # return
    return edge_df, node_df

def load_ontology():
    this_dir, _ = os.path.split(__file__)
    iri = "http://example.org/onto-got.owl"
    fname = "./onto-got.owl"
    ontor1 = ontor.OntoEditor(iri, fname)
    ontor1.add_axioms(ontor.load_csv(os.path.join(this_dir, "got", "class_axioms.csv")))
    return ontor1

def get_df_from_ontology(onto: OntoEditor):
    nodelist = list(onto.get_elems())
    node_df = pd.DataFrame(nodelist)
    return node_df
