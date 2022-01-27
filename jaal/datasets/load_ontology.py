"""
Author: Mohit Mayank

Load and return the Game of Thrones dataset

Data details:
1. 
"""

# imports
import logging
import datetime
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
    """Loads the Pizza-example ontology wih classes, with classes, instances, object- and data-properties"""

    logfile = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_jaal.log"
    logging.basicConfig(filename=logfile, level=logging.INFO)

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
    ontor1.add_ops(ontor.load_json(os.path.join(this_dir, "example_ontology", "props.json"))["op"])
    ontor1.add_dps(ontor.load_json(os.path.join(this_dir, "example_ontology", "props.json"))["dp"])
    ontor1.add_axioms(ontor.load_csv(os.path.join(this_dir, "example_ontology", "class_axioms.csv")))
    ontor1.add_instances(ins)
    return ontor1

def get_tboxes(onto: OntoEditor, nodelist = []):
    """Extracts T-Boxes from ontology and returns them in a list.

    Parameters
    -----------
    onto: OntoEditor
        ontology of type OntoEditor from which classes are extracted
    nodelist: list
        list of all classes/ instances that were already extracted from the ontology"""

    # Generator of all classes in the ontology is created
    node_gen = onto.onto.classes()
    # All classes from the generator are written into a list with their name, importance, shape and T-Box label
    for cl in node_gen:
        nodelist.append([cl.name, 1, 'dot', 'T', ""])
    #return list of all extracted classes
    logging.info("successfully parsed T-Boxes from ontology specified")
    return nodelist

def get_isa_realtions(onto: OntoEditor, edgelist = []):
    """Extracts all 'is_a'-relations from ontology and returns them in a list.

    Parameters
    -----------
    onto: OntoEditor
        ontology of type OntoEditor from which relations are extracted
    edgelist: list
        list of all relations that were already extracted from the ontology"""

    # Generator of all classes in the ontology is created
    node_gen = onto.onto.classes()
    # For all classes from the generator the associated subclasses are written into a list
    for cl in node_gen:
        rellist = list(cl.subclasses())
        # All subclasses are written into a list with their name, associated superclasses' name,
        # id, weight, label and dashed-boolean
        for i, value in enumerate(rellist):
            identifier = rellist[i].name + ' is_a ' + cl.name
            edgelist.append([rellist[i].name, cl.name, identifier, 1, 'is_a', False])
    # return list of all extracted edges/ relations
    logging.info("successfully parsed IS_A-relations from ontology specified")
    return edgelist

def get_OPs(onto: OntoEditor, edgelist = []):
    """Extracts all object-properties from ontology and returns them in a list that is passed to the function.

    Parameters
    -----------
    onto: OntoEditor
        ontology of type OntoEditor from which relations are extracted
    edgelist: list
        list of all relations that were already extracted from the ontology"""

    # Generator of all object-properties in the ontology is created
    op_gen = onto.onto.object_properties()
    # Iteration over all object-properties from the generator
    for op in op_gen:
        # All range-elements (targets) are written into a list except the first element, with their
        # domain's name, name, identifier, weight, associated object-property's name and dashes-boolean
        for i, value in enumerate(op.range):
            if i != 0:
                identifier = op.domain[0].name + ' ' + op.name + ' ' + op.range[i].name
                edgelist.append([op.domain[0].name, op.range[i].name, identifier, 1, op.name, True])
    # return list of all extracted edges/ relations
    logging.info("successfully parsed Object-Properties from ontology specified")
    return edgelist

def get_DPs(onto: OntoEditor, nodelist = [], edgelist = []):
    """Extracts all data-properties from ontology and returns them in a list that is passed to the function.

    Parameters
    -----------
    onto: OntoEditor
        ontology of type OntoEditor from which relations are extracted
    nodelist: list
        list of all classes/ instances that were already extracted from the ontology
    edgelist: list
        list of all relations that were already extracted from the ontology"""
    counter_skipped = 0
    counter_parsed = 0
    # Generator of all data-properties in the ontology is created
    dp_gen = onto.onto.data_properties()
    # Iteration over all data-properties from the generator
    for dp in dp_gen:
        # A list of unique domains of the associated data-property is created
        dp_dom_unique = []
        for dom in dp.domain:
            if not dom in dp_dom_unique:
                dp_dom_unique.append(dom)
        try:
            # Booleans to indicate, whether node/ edge is already in nodelist/ edgelist are instantiated
            node_in_nodelist = False
            edge_in_edgelist = False
            # The datatype of the associated data-property is written into a string-variable
            dp_type = str(dp.range).split("'")[1]
            # Iteration over all relations in edgelist
            for edge in edgelist:
                # Iteration over all unique domains of the associated data-property
                for i, value in enumerate(dp_dom_unique):
                    # If there is already a relation between two corresponding domains and data-types,
                    # and it is not the first domain of the associated data-property (unless there is only one),
                    # the new data-property is added to the existing edge with their id and the data-property's name.
                    # Also the weight of the edge is increased by one and the boolean to indicate the edge already
                    # exists is set to True
                    if edge[0] == dp_dom_unique[i].name and edge[1] == dp_type and (
                            len(dp_dom_unique) == 1 or not i == 0):
                        edge_in_edgelist = True
                        identifier = dp_dom_unique[i].name + ' ' + dp.name + ' ' + dp_type
                        edge[2] = edge[2] + ',\n ' + identifier
                        edge[4] = edge[4] + ',\n ' + dp.name
                        edge[3] = edge[3] + 1
            # If there is not already a relation between two corresponding domains and data-types,
            # and it is not the first domain of the associated data-property (unless there is only one), the new
            # data-property is written to a list with their domain's name, data-type, id, weight, data-property's name
            # and dashes-boolean
            if not edge_in_edgelist:
                for i, value in enumerate(dp_dom_unique):
                    if len(dp_dom_unique) == 1 or not i == 0:
                        identifier = dp_dom_unique[i].name + ' ' + dp.name + ' ' + dp_type
                        edgelist.append([dp_dom_unique[i].name, dp_type, identifier, 1, dp.name, True])
            # If the data-type of the associated data-property is already in the nodelist, the boolean to indicate
            # the node already exists is set to True
            node_in_nodelist = is_already_in_list(dp_type, nodelist)
            # If node_in_list is False, the data-type of the associated data-property will be added to the nodelist
            # with their identifier, weight, shape and T-Box label
            if not node_in_nodelist:
                nodelist.append([dp_type, 1, 'triangle', 'T', ""])
            counter_parsed = counter_parsed + 1
        # If an IndexError is thrown, an warning will be logged, that the one data-property was skipped
        except IndexError:
            counter_skipped = counter_skipped + 1
    logging.info("successfully parsed %i Data-Properties from ontology specified", counter_parsed)
    logging.warning("while parsing, %i Data-Properties were skipped", counter_skipped)
    # return list of all extracted nodes/ data-types and list of all extracted edges/ relations
    return nodelist, edgelist

def calculate_node_importance(node_df, edge_df):
    """Weights the nodes in nodelist acoording to the number of incoming edges

    Parameters
    -----------
    node_df: pandas.DataFrame
        DataFrame parsed from nodelist
    edge_df: pandas.DataFrame
        DataFrame parsed from edgelist"""

    # Boolean to indicate there is an weight/ importance column in node_df is created
    importance_col = False
    # If there is a column in node_df called importance, importance_col will be set to True
    for col in node_df.columns:
        if col == 'importance':
            importance_col = True
    # If importance_col is True ...
    if importance_col:
        # Iteration over nodes in node_df
        for node_index, node in node_df.iterrows():
            # For every new node-ID the counter is set to zero
            counter = 0
            # Iteration over all edges in edge_df
            for edge_index, edge in edge_df.iterrows():
                # If the ID/ name of a node is equal to the edge to-column and it is an is_a relation,
                # the counter is increased by one
                if node['id'] == edge['to'] and edge['label'] == 'is_a':
                    counter = counter + 1
            # If the counter of a node is higher than zero, the new importance value is assigned
            if counter != 0:
                node_df.loc[node_index,'importance'] = counter
    # return node_df with new importance values
    logging.info("successfully calculated weights for A-/T-Boxes")
    return node_df

def get_aboxes(onto: OntoEditor, nodelist, edgelist):
    """Extracts all instances/ A-Boxes from ontology and returns them in a list that is passed to the function.

    Parameters
    -----------
    onto: OntoEditor
        ontology of type OntoEditor from which relations are extracted
    nodelist: list
        list of all classes/ instances that were already extracted from the ontology
    edgelist: list
        list of all relations that were already extracted from the ontology"""

    # Generator of all classes in the ontology is created
    node_gen = onto.onto.classes()
    # Iteration over all classes/ nodes in the generator
    for node in node_gen:
        # Iteration over all instances of of the associated class
        for ins in onto.onto.search(type = node):
            # Boolean to indicate, whether edge is already in edgelist is instantiated
            edge_in_edgelist = False
            # Get superclass of instance
            superclass = ins.is_a
            # write property in node or edge list depending on OP or DP
            prop_value = ''
            for prop in ins.get_properties():
                for value in prop[ins]:
                    if type(value) == float or type(value) == int or type(value) == str:
                        if prop_value == '' and not (prop.name + ' = ' + str(value)) in prop_value:
                            prop_value = prop.name + ' = ' + str(value)
                        elif not (prop.name + ' = ' + str(value)) in prop_value:
                            prop_value = prop_value + ',\n ' + prop.name + ' = ' + str(value)
                    else:
                        identifier = ins.name + ' ' + prop.name + ' ' + value.name
                        for rel in edgelist:
                            if rel[2] == identifier:
                                edge_in_edgelist = True
                        if not edge_in_edgelist:
                            edgelist.append([ins.name, value.name, identifier, 1, prop.name, False])
                        edge_in_edgelist = False
            # If there is a class in nodelist that has the same name as the instance node_in_list is set to True
            node_in_nodelist = is_already_in_list(ins.name, nodelist)
            # If node_in_nodelist is False the instance is written in a list with its ID, weight, shape and A-Box label
            if not node_in_nodelist:
                nodelist.append([ins.name, 1, 'box', 'A', prop_value])
            # Iteration over all relations/ edges in edgelist
            for rel in edgelist:
                # If there is already an edge between the instance and its superclass, edge_in_edgelist is set to True.
                # The new relation is added to the existing edge with its ID and label and the weight
                # is increased by one.
                if ins.name == rel[0] and superclass[0].name == rel[1]:
                    edge_in_edgelist = True
                    identifier = ins.name + ' is_a ' + superclass[0].name
                    # The new relation is added to the existing edge with its ID and label and the weight
                    # is increased by one, if there is not already an relationship with the same ID
                    if not identifier == rel[2]:
                        rel[2] = rel[2] + ',\n ' + identifier
                        rel[4] = rel[4] + ',\n ' + 'is_a'
                        rel[3] = rel[3] + 1
            # If edge_in_edgelist is False, the new instance is written into a list
            # with its name, its superclasses' name, identifier, weight, label and dashes-boolean
            if not edge_in_edgelist:
                identifier = ins.name + ' is_a ' + superclass[0].name
                edgelist.append([ins.name, superclass[0].name, identifier, 1, 'is_a', False])
    logging.info('successfully parsed A-Boxes from ontology specified')
    # return list of all extracted instances and list of all extracted edges/ relations
    return nodelist, edgelist

def is_already_in_list(nodename, nodelist):
    """Checks if a node with a given name, is already in the given list"""
    # Iterate over all classes in nodelist
    for cl in nodelist:
        # If there is a class in nodelist that has the name nodename, True is returned
        if cl[0] == nodename:
            return True
    return False

def get_df_from_ontology(onto: OntoEditor, abox: bool = False):
    """Parses the information given by the ontology into a panda.DataFrame. Parsed data includes:
    T-Boxes, is-a relations, object-properties, data-properties and A-Boxes (if abox is True).

    Parameters
    -----------
    onto: OntoEditor
       ontology of type OntoEditor from which the information is extracted
    abox: bool
        Boolean to indicate wheter A-Boxes should be included or not"""
    # Set basic Configuration for Logger (if its not already set)
    logfile = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_jaal.log"
    logging.basicConfig(filename=logfile, level=logging.INFO)
    logging.info("begin parsing data from specified ontology to dataframes...")
    # Get T-Boxes from ontology and write them into nodelist
    nodelist = get_tboxes(onto)
    # Get is-a relations from ontology and write them into edgelist
    edgelist = get_isa_realtions(onto)
    # Get object-properties from ontology and write them into edgelist
    edgelist = get_OPs(onto, edgelist)
    # Get data-properties from ontology and write them into edgelist
    nodelist, edgelist = get_DPs(onto, nodelist, edgelist)
    # If abox is True, get A-Boxes from ontology and write them into nodelist
    if abox:
        nodelist, edgelist = get_aboxes(onto, nodelist, edgelist)

    # Parse nodelist into panda.DataFrame, with column-names id, importance, shape and T/A
    node_df = pd.DataFrame(nodelist)
    node_df.columns = ['id', 'importance', 'shape', 'T/A', 'title']
    # Parse edgelist into panda.DataFrame, with column-names from, to, id, weight, label and dashes
    edge_df = pd.DataFrame(edgelist)
    edge_df.columns = ['from', 'to', 'id', 'weight', 'label', 'dashes']
    # Calculate the importance of nodes in nodelist and write the new importance value into node_df
    node_df = calculate_node_importance(node_df, edge_df)
    logging.info("...successfully parsed data from ontology specified to dataframes")
    return edge_df, node_df