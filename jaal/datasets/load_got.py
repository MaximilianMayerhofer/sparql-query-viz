"""
Author: Mohit Mayank

Load and return the Game of Thrones dataset

Data details:
1. 
"""

# imports
import os
import pandas as pd
import ontor as ontor
from ontor import OntoEditor
import owlready2

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
    edge_df = pd.read_csv(os.path.join(this_dir, "got", "got_edge_df.csv"))
    node_df = pd.read_csv(os.path.join(this_dir, "got", "got_node_df.csv"))
    #return
    return edge_df, node_df

def load_ontology():
    this_dir, _ = os.path.split(__file__)
    iri = "http://example.org/onto-got.owl"
    fname = "./onto-got.owl"
    ontor1 = OntoEditor(iri, fname)
    classes = [["company", None, None, None, None, None, None], \
               ["pizza_company", "company", None, None, None, None, False], \
               ["margherita_company", "pizza_company", None, None, None, None, False], \
               ["quattro_stagioni", "pizza", None, None, None, None, False]]
    ins = [["Her_pizza", "quattro_stagioni", None, None, None], \
           ["Jane", "human", "likes", "Her_pizza", None], \
           ["Faulty_pizza", None, None, None, None], \
           ["Her_pizza", "quattro_stagioni", "weight_in_grams", "430.0", "float"], \
           ["Her_pizza", "quattro_stagioni", "diameter_in_cm", "32", "integer"], \
           ["Her_pizza", "quattro_stagioni", "description", "jane's pizza", "string"]]
    ontor1.add_axioms(classes)
    ontor1.add_ops(ontor.load_json(os.path.join(this_dir, "got", "props.json"))["op"])
    ontor1.add_dps(ontor.load_json(os.path.join(this_dir, "got", "props.json"))["dp"])
    ontor1.add_axioms(ontor.load_csv(os.path.join(this_dir, "got", "class_axioms.csv")))
    ontor1.add_instances(ins)
    return ontor1

def get_df_from_ontology(onto: OntoEditor, aBox: bool = False):
    nodelist = []
    node_gen = onto.onto.classes()
    for cl in node_gen:
        nodelist.append([cl.name, 1, 'dot', 'T']) # 'T' indicates that this is a tBox

    edgelist = []
    node_gen = onto.onto.classes() #mit list keyword kann mehrfach verwendet werden
    for cl in node_gen:
        rellist = list(cl.subclasses())
        for i, value in enumerate(rellist):
            edgelist.append([rellist[i].name,cl.name,'is_a', 1, 'is_a', False])

    op_gen = onto.onto.object_properties()
    for op in op_gen:
        op_name = op.name
        op_dom = op.domain
        op_ran = op.range
        for i, value in enumerate(op_ran):
            if i != 0:
                edgelist.append([op_dom[0].name, op_ran[i].name, op_name, 1, op_name, True])

    dp_gen = onto.onto.data_properties()
    for dp in dp_gen:
        dp_name = dp.name
        dp_dom = dp.domain
        dp_dom_unique = []
        for dom in dp_dom:
            if not dom in dp_dom_unique:
               dp_dom_unique.append(dom)
        dp_ran = dp.range
        try:
            flag_nodes = False
            flag_edges = False
            dp_type = str(dp_ran).split("'")[1]
            for edge_column in edgelist:
                for i, value in enumerate(dp_dom_unique):
                    if edge_column[0] == dp_dom_unique[i].name and edge_column[1] == dp_type and (len(dp_dom_unique) == 1 or not i == 0):
                        flag_edges = True
                        edge_column[2] = edge_column[2] + ', ' + dp_name
                        edge_column[4] = edge_column[4] + ', ' + dp_name
                        edge_column[3] = edge_column[3] + 0.1
            if not flag_edges:
                for i, value in enumerate(dp_dom_unique):
                    if len(dp_dom_unique) == 1 or not i == 0:
                        edgelist.append([dp_dom_unique[i].name, dp_type, dp_name, 1, dp_name, True])

            for node in nodelist:
                if node[0] == dp_type:
                    flag_nodes = True
            if not flag_nodes:
                nodelist.append([dp_type, 1, 'triangle', 'T'])

        except IndexError:
            print(dp_name, "was skipped.")

    if aBox:
        get_inst_rel(nodelist, edgelist, onto)

    node_df = pd.DataFrame(nodelist)
    node_df.columns = ['id', 'importance', 'shape', 'T/A']

    edge_df = pd.DataFrame(edgelist)
    edge_df.columns = ['from', 'to', 'id', 'weight', 'label', 'dashes']

    get_node_weights(node_df, edge_df)



    return edge_df, node_df

def get_node_weights(node_df, edge_df):
    is_there_a_weight_col = False
    for node_col in node_df.columns:
        if node_col == 'importance':
            is_there_a_weight_col = True

    if is_there_a_weight_col:
        i = 0
        for node in node_df['id']:
            count = 0
            for index, edge in edge_df.iterrows():
                if node == edge['to'] and edge['id'] == 'is_a':
                    count = count + 1
            if count != 0:
                node_df.loc[i,'importance'] = count
            i = i + 1

    return node_df



def get_inst_rel(nodelist, edgelist, onto: OntoEditor):
    node_gen = onto.onto.classes()
    for node in node_gen:
        ins_list = onto.onto.search(type = node)
        for ins in ins_list:
            flag_nodes = False
            flag_edge = False

            for prop in ins.get_properties():
                for value in prop[ins]:
                    prop_value = value

            superclass = ins.is_a
            for cl in nodelist:
                if cl[0] == ins.name:
                    flag_nodes = True
            if flag_nodes == False:
                nodelist.append([ins.name, 1, 'box', 'A'])
            for rel in edgelist:
                if ins.name == rel[0] and superclass[0].name == rel[1]:
                    flag_edge = True
            if flag_edge == False:
                edgelist.append([ins.name, superclass[0].name, 'is_a', 1, 'is_a', False])