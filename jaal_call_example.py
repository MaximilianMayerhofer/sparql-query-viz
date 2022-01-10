# import
from jaal import Jaal
from jaal.datasets.load_got import *

# load the data
onto1 = load_ontology()
edge_df,node_df = get_df_from_ontology(onto1, True)

# init Jaal and run server (with opts
Jaal(edge_df, onto1, node_df).plot(directed=True)