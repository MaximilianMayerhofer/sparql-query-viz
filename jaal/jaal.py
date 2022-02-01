"""
Author: Mohit Mayank

Main class for Jaal network visualization dashboard
"""
# import
import logging
import owlready2.rply
from ontor import OntoEditor
import dash
import visdcc
import pandas as pd
from dash import dcc
from dash import html
import dash_bootstrap_components as dbc
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State
from .datasets.parse_dataframe import parse_dataframe
from .datasets.load_ontology import *
from .layout import get_app_layout, get_distinct_colors, create_color_legend, get_categorical_features, get_numerical_features, DEFAULT_COLOR, DEFAULT_NODE_SIZE, DEFAULT_EDGE_SIZE

def _callback_search_graph(graph_data, search_text):
    """Only show the nodes which match the search text
    """
    nodes = graph_data['nodes']
    edges = graph_data['edges']
    for node in nodes:
        if search_text not in node['label'].lower():
            node['hidden'] = True
        else:
            node['hidden'] = False
    for edge in edges:
        if search_text in edge['label'].lower():
            for node in nodes:
                if edge['from'].lower() == node['label'].lower():
                    node['hidden'] = False
                elif edge['to'].lower() == node['label'].lower():
                    node['hidden'] = False
    graph_data['nodes'] = nodes
    graph_data['edges'] = edges
    return graph_data

def get_color_popover_legend_children(node_value_color_mapping={}, edge_value_color_mapping={}):
    """Get the popover legends for node and edge based on the color setting
    """
    # var
    popover_legend_children = []

    # common function
    def create_legends_for(title="Node", legends={}):
        # add title
        _popover_legend_children = [dbc.PopoverHeader(f"{title} legends")]
        # add values if present
        if len(legends) > 0:
            for key, value in legends.items():
                partition = key.partition(',\n ')
                if partition[2] == '':
                    _popover_legend_children.append(
                        # dbc.PopoverBody(f"Key: {key}, Value: {value}")
                        create_color_legend(key, value)
                        )
                else:
                    _popover_legend_children.append(
                        # dbc.PopoverBody(f"Key: {key}, Value: {value}")
                        create_color_legend(partition[0], value)
                    )
                    _popover_legend_children.append(
                        # dbc.PopoverBody(f"Key: {key}, Value: {value}")
                        create_color_legend(partition[2], value)
                    )
        else: # otherwise add filler
            _popover_legend_children.append(dbc.PopoverBody(f"no {title.lower()} colored!"))
        #
        return _popover_legend_children

    # add node color legends
    popover_legend_children.extend(create_legends_for("Node", node_value_color_mapping))
    # add edge color legends
    popover_legend_children.extend(create_legends_for("Edge", edge_value_color_mapping))
    #
    return popover_legend_children

def get_nodes_to_be_shown(res_list: list, data: dict, number_of_edges_to_be_shown_around_result: int = 1):
    filtered_node_data = []
    #n = 1
    for node in data['nodes']:
        for result in res_list:
            if node['id'] == result.name:
                filtered_node_data.append(node)
    node_selection = filtered_node_data.copy()
    #while n <= number_of_edges_to_be_shown_around_result:
    #globals()['%s_center_node_list' % n] = res_list
    for result in res_list:
        for edge in data['edges']:
            if edge['from'] == result.name:
                for node in data['nodes']:
                    if node['id'] == edge['to']:
                        filtered_node_data.append(node)
                        #globals()['%s_center_node_list' % str(n+1)].append(node['id'])

    return filtered_node_data, node_selection

class Jaal:
    """The main visualization class
    """
    def __init__(self, onto: OntoEditor = ontor.OntoEditor("http://example.org/onto-ex.owl", "./onto-ex.owl"), abox: bool = True):
        """
        Parameters
        -------------
        edge_df: pandas dataframe
            The network edge data stored in format of pandas dataframe

        node_df: pandas dataframe (optional)
            The network node data stored in format of pandas dataframe
        """
        self.filename = onto.path.split(sep="/")[-1]
        self.logger = logging.getLogger(self.filename.split(".")[0])
        self.abox = abox
        self.edge_df, self.node_df = get_df_from_ontology(onto, self.abox)
        self.logger.info("begin parsing data from dataframes to visdcc-dataformat...")
        self.data, self.scaling_vars = parse_dataframe(self.edge_df, self.node_df)
        self.logger.info("...successfully parsed data from dataframes to visdcc-dataformat")
        self.filtered_data = self.data.copy()
        self.node_value_color_mapping = {}
        self.edge_value_color_mapping = {}
        self.sparql_query = ''
        self.sparql_query_last_input = ['']
        self.sparql_query_history = ''
        self.counter_query_history = 0
        self.sparql_query_result = ''
        self.nodes_selected_for_template = 0
        self.selected_node_for_template = ''
        self.edges_selected_for_template = 0
        self.selected_edge_for_template = ''
        self.onto = onto

    def edit_edge_appearance(self, directed = True):
        for edge in self.data['edges']:
            if edge['label'] == 'is_a':
                arrow_type = {'arrows': {'to': {'enabled': directed, 'type': 'circle'}}}
            else:
                arrow_type = {'arrows': {'to': {'enabled': directed, 'type': 'arrow'}}}
            edge.update(arrow_type)

    def clear_selection_for_template_query(self):
        self.nodes_selected_for_template = 0
        self.selected_node_for_template = ''
        self.edges_selected_for_template = 0
        self.selected_edge_for_template = ''

    def complete_sparql_query_with_selection(self, selection: dict):
        if len(selection['nodes']) > 0:
            for node in self.data['nodes']:
                if [node['id']] == selection['nodes']:
                    self.sparql_query_last_input.append(' :' + node['id'])
                    if (" PREFIX : <" + self.onto.iri + "#>" + "SELECT ?x WHERE { ?x" in self.sparql_query) \
                            and self.nodes_selected_for_template == 0:
                        self.sparql_query = self.sparql_query.replace(':[node]', self.sparql_query_last_input[-1])
                        self.nodes_selected_for_template = self.nodes_selected_for_template + 1
                        self.selected_node_for_template = self.sparql_query_last_input[-1]
                    else:
                        self.sparql_query = self.sparql_query + self.sparql_query_last_input[-1]
                    self.logger.info("%s added to sparql query", self.sparql_query_last_input[-1])
        elif len(selection['edges']) > 0:
            for edge in self.data['edges']:
                if [edge['id']] == selection['edges']:
                    self.sparql_query_last_input.append(' :' + edge['label'])
                    if (" PREFIX : <" + self.onto.iri + "#>" + "SELECT ?x WHERE { ?x" in self.sparql_query) \
                            and self.edges_selected_for_template == 0:
                        self.sparql_query = self.sparql_query.replace(':[edge]', self.sparql_query_last_input[-1])
                        self.edges_selected_for_template = self.edges_selected_for_template + 1
                        self.selected_edge_for_template = self.sparql_query_last_input[-1]
                    else:
                        self.sparql_query = self.sparql_query + self.sparql_query_last_input[-1]
                    self.logger.info("%s added to sparql query", self.sparql_query_last_input[-1])

    def add_to_query_history(self):
        self.counter_query_history = self.counter_query_history + 1
        self.sparql_query_history = self.sparql_query_history + str(
            self.counter_query_history) + ": " + self.sparql_query + '\n'

    def _callback_filter_nodes(self, graph_data):
        """Filter the nodes based on the Python query syntax
        """
        self.filtered_data = self.data.copy()
        selection = {'nodes': [], 'edges': []}
        try:
            res_list = list(self.onto.onto_world.sparql(self.sparql_query))
            flat_res_list = [x for l in res_list for x in l]
            result = ""
            if not flat_res_list:
                graph_data = self.data
                result = "No results for this SPARQL query."
                self.sparql_query_result = result
                self.logger.info("result for passed sparql query is empty")
                return graph_data, result, selection
            res_is_no_data_object = False
            for flat_res in flat_res_list:
                try:
                    result = result + str(flat_res.name) + "\n"
                    self.logger.info("result is a valid node/edge of graph")
                except AttributeError:
                    graph_data = self.data
                    result = result + str(flat_res) + "\n"
                    self.logger.info("result is not an object (A-/ T-Box) in graph (different data-type)")
                    res_is_no_data_object = True
            self.sparql_query_result = result
            if not res_is_no_data_object:
                self.filtered_data['nodes'], selection['nodes'] = get_nodes_to_be_shown(flat_res_list,self.filtered_data)
                graph_data = self.filtered_data
            self.add_to_query_history()
            self.logger.info("valid sparql query successfully evaluated")
        except owlready2.rply.ParsingError:
            graph_data = self.data
            result = "No SPARQL query entered"
            self.sparql_query_result = result
            self.logger.warning("sparql query passed from user is empty")
        except owlready2.rply.LexingError:
            graph_data = self.data
            result = "Not a valid SPARQL query."
            self.sparql_query_result = result
            self.logger.warning("sparql query passed from user is not valid")
        except ValueError:
            graph_data = self.data
            result = "Not a valid SPARQL query."
            self.sparql_query_result = result
            self.logger.warning("sparql query passed from user is not valid")
        return graph_data, result, selection

    def _callback_sparql_query_history(self, number_of_shown_queries):
        sparql_query_history = self.sparql_query_history
        if self.counter_query_history > number_of_shown_queries:
            separator = str(self.counter_query_history - (number_of_shown_queries - 1)) + ": "
            partition = sparql_query_history.partition(separator)
            shown_sparql_query_history = partition[1] + partition[2]
        else:
            shown_sparql_query_history = sparql_query_history
        return shown_sparql_query_history

    def _callback_color_nodes(self, color_nodes_value):
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_nodes_value == 'None':
            # revert to default color
            for node in self.data['nodes']:
                node['color'] = DEFAULT_COLOR
        else:
            unique_values = pd.DataFrame(self.data['nodes'])[color_nodes_value].unique()
            colors = get_distinct_colors(len(unique_values), for_nodes=True)
            value_color_mapping = {x:y for x, y in zip(unique_values, colors)}
            for node in self.data['nodes']:
                node['color'] = value_color_mapping[node[color_nodes_value]]
        # filter the data currently shown
        filtered_nodes = [x['id'] for x in self.filtered_data['nodes']]
        self.filtered_data['nodes'] = [x for x in self.data['nodes'] if x['id'] in filtered_nodes]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping
    
    def _callback_size_nodes(self, size_nodes_value):

        # color option is None, revert back all changes
        if size_nodes_value == 'None':
            # revert to default size
            for node in self.data['nodes']:
                node['size'] = DEFAULT_NODE_SIZE
        else:
            # fetch the scaling value
            minn = self.scaling_vars['node'][size_nodes_value]['min']
            maxx = self.scaling_vars['node'][size_nodes_value]['max']
            # define the scaling function
            scale_val = lambda x: 20*(x-minn)/(maxx-minn)
            # set size after scaling
            for node in self.data['nodes']:
                node['size'] = node['size'] + scale_val(node[size_nodes_value])
        # filter the data currently shown
        filtered_nodes = [x['id'] for x in self.filtered_data['nodes']]
        self.filtered_data['nodes'] = [x for x in self.data['nodes'] if x['id'] in filtered_nodes]
        graph_data = self.filtered_data
        return graph_data

    def _callback_color_edges(self, color_edges_value):
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_edges_value == 'None':
            # revert to default color
            for edge in self.data['edges']:
                edge['color']['color'] = DEFAULT_COLOR
        else:
            unique_values = pd.DataFrame(self.data['edges'])[color_edges_value].unique()
            colors = get_distinct_colors(len(unique_values), for_nodes=False)
            value_color_mapping = {x:y for x, y in zip(unique_values, colors)}
            for edge in self.data['edges']:
                edge['color']['color'] = value_color_mapping[edge[color_edges_value]]
        # filter the data currently shown
        filtered_edges = [x['id'] for x in self.filtered_data['edges']]
        self.filtered_data['edges'] = [x for x in self.data['edges'] if x['id'] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping

    def _callback_size_edges(self, size_edges_value):
        minn = 0
        maxx = 100
        # fetch the scaling value
        if size_edges_value != 'None':
            minn = self.scaling_vars['edge'][size_edges_value]['min']
            maxx = self.scaling_vars['edge'][size_edges_value]['max']
        # if color option is None or minn and maxx is the same, revert back all changes
        if size_edges_value == 'None' or minn == maxx:
            # revert to default size
            for edge in self.data['edges']:
                edge['width'] = DEFAULT_EDGE_SIZE
        else:
            # define the scaling function
            scale_val = lambda x: 5*(x-minn)/(maxx-minn)
            # set the size after scaling
            for edge in self.data['edges']:
                if edge[size_edges_value] == minn:
                    edge['width'] = DEFAULT_EDGE_SIZE
                else:
                    edge['width'] = scale_val(edge[size_edges_value])
                # edge['width'] = edge[size_edges_value]
        # filter the data currently shown
        filtered_edges = [x['id'] for x in self.filtered_data['edges']]
        self.filtered_data['edges'] = [x for x in self.data['edges'] if x['id'] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data

    def forced_callback_execution_at_beginning(self, directed=True):
        """This function executes the callback functions for node and edge Coloring and Sizing at start of the app,
        without andy userinput. This is to ensure a default coloring and sizing of nodes and edges."""

        # Give all is_a edges a circle as arrowhead
        self.edit_edge_appearance(directed=directed)
        # Get list of categorical features from nodes
        cat_node_features = get_categorical_features(pd.DataFrame(self.data['nodes']), 20, ['shape', 'label', 'id', 'title', 'color'])
        # Define label and value for each categorical feature
        options = [{'label': opt, 'value': opt} for opt in cat_node_features]
        # If options has more then one categorical feature, the callback function for nodes-coloring is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data, self.node_value_color_mapping = self._callback_color_nodes(options[1].get('value'))
            self.logger.info("Nodes were initially colored")
        # Get list of categorical features from edges
        cat_edge_features = get_categorical_features(pd.DataFrame(self.data['edges']).drop(
            columns=['color', 'from', 'to', 'id','arrows']), 20,['color', 'from', 'to', 'id'])
        # Define label and value for each categorical feature
        options = [{'label': opt, 'value': opt} for opt in cat_edge_features]
        # If options has mor then one categorical feature, the callback function for edge-coloring is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data, self.edge_value_color_mapping = self._callback_color_edges(options[1].get('value'))
            self.logger.info("Edges were initially colored")
        # Get list of numerical features from nodes
        num_node_features = get_numerical_features(pd.DataFrame(self.data['nodes']))
        # Define label and value for each numerical feature
        options = [{'label': opt, 'value': opt} for opt in num_node_features]
        # If options has mor then one numerical feature, the callback function for nodes-sizing is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data = self._callback_size_nodes(options[1].get('value'))
            self.logger.info("Nodes were initially sized")
        # Get list of numerical features from edges
        num_edge_features = get_numerical_features(pd.DataFrame(self.data['edges']))
        # Define label and value for each numerical feature
        options = [{'label': opt, 'value': opt} for opt in num_edge_features]
        # If options has mor then one numerical feature, the callback function for edge-sizing is executed once,
        # to set the first option as default value
        if len(options) > 1:
            self.data = self._callback_size_edges(options[1].get('value'))
            self.logger.info("Edges were initially sized")

    def create(self, directed=False, vis_opts=None):
        """Create the Jaal app and return it

        Parameter
        ----------
            directed: boolean
                process the graph as directed graph?

            vis_opts: dict
                the visual options to be passed to the dash server (default: None)

        Returns
        -------
            app: dash.Dash
                the Jaal app
        """
        # create the app
        #app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP], title = 'SPARQL Query Viz')
        app = dash.Dash(__name__,external_stylesheets=[dbc.themes.BOOTSTRAP], title = 'SPARQL Query Viz')

        # get color_mapping and size_mapping once at the start
        self.forced_callback_execution_at_beginning(directed=directed)

        # define layout
        app.layout = get_app_layout(self.data, self.onto, color_legends=get_color_popover_legend_children(), directed=directed, vis_opts=vis_opts, abox = self.abox)

        # create callbacks to toggle legend popover
        @app.callback(
            Output("color-legend-popup", "is_open"),
            [Input("color-legend-toggle", "n_clicks")],
            [State("color-legend-popup", "is_open")],
        )
        def toggle_popover(n, is_open):
            if n:
                if is_open:
                    self.logger.info("legend popup was hidden, triggered by user")
                else:
                    self.logger.info("legend popup was shown, triggered by user")
                return not is_open
            return is_open

        @app.callback(
            Output("info-sparql-popup", "is_open"),
            [Input("info-sparql-query-button", "n_clicks")],
            [State("info-sparql-popup", "is_open")],
        )
        def toggle_popover(n, is_open):
            if n:
                if is_open:
                    self.logger.info("sparql info popup was hidden, triggered by user")
                else:
                    self.logger.info("sparql info popup was shown, triggered by user")
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - FILTER section
        @app.callback(
            Output("filter-show-toggle", "is_open"),
            [Input("filter-show-toggle-button", "n_clicks"),
             Input('sparql_template_1', 'n_clicks'),
             Input('sparql_template_2', 'n_clicks')],
            [State("filter-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, n_template1, n_template2, is_open):
            ctx = dash.callback_context
            if not ctx.triggered:
                return is_open
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == "filter-show-toggle-button" and n_show:
                    if is_open:
                        self.logger.info("sparql query section was hidden, triggered by user")
                    else:
                        self.logger.info("sparql query section was shown, triggered by user")
                    return not is_open
                if input_id == "sparql_template_1" or input_id == "sparql_template_2":
                    self.logger.info("sparql query section was shown, because template button was triggered")
                    return True
            return is_open

        @app.callback(
            Output("result-show-toggle", "is_open"),
            [Input("result-show-toggle-button", "n_clicks"),
             Input('evaluate_query_button', 'n_clicks')],
            [State("result-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, n_evaluate, is_open):
            ctx = dash.callback_context
            if not ctx.triggered:
                return is_open
            else:
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                if input_id == "result-show-toggle-button" and n_show:
                    if is_open:
                        self.logger.info("sparql result section was hidden, triggered by user")
                    else:
                        self.logger.info("sparql result section was shown, triggered by user")
                    return not is_open
                if input_id == "evaluate_query_button" and n_evaluate:
                    self.logger.info("sparql result section was shown, because evaluation button was triggered")
                    return True
            return is_open

        @app.callback(
            Output("history-show-toggle", "is_open"),
            [Input("history-show-toggle-button", "n_clicks")],
            [State("history-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, is_open):
            if n_show:
                if is_open:
                    self.logger.info("sparql history section was hidden, triggered by user")
                else:
                    self.logger.info("sparql history section was shown, triggered by user")
                return not is_open
            return is_open
        
        @app.callback(
            Output("select-sparql", "children"),
            [Input("sparql-keywords-dropdown","value"),
             Input("sparql-variables-dropdown", "value"),
             Input("sparql-syntax-dropdown", "value"),
             Input("add_to_query_button", "n_clicks"),
             Input("clear_query_button", "n_clicks"),
             Input("delete_query_button", "n_clicks"),
             Input("add_node_edge_to_query_button", "on"),
             Input('graph', 'selection'),
             Input('sparql_template_1','n_clicks'),
             Input('sparql_template_2','n_clicks')],
            [State("filter_nodes", "value")],
        )
        def edit_sparql_query(kw_value, var_value, syn_value, n_add,
                              n_clear, n_delete, on_select, selection, n_template1, n_template2, value):
            ctx = dash.callback_context
            if self.sparql_query is None:
                self.sparql_query = ""

            if not ctx.triggered:
                self.logger.info("no trigger by user")
                return self.sparql_query
            else:
                # find the id of the option which was triggered
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # perform operation depending on which sparql button was triggered
                if input_id == "sparql-keywords-dropdown":
                    if kw_value is not None:
                        if kw_value == "PREFIX":
                            self.sparql_query_last_input.append(" PREFIX : <" + self.onto.iri + "#>")
                        elif kw_value == "SELECT":
                            self.sparql_query_last_input.append(" SELECT")
                        else:
                            self.sparql_query_last_input.append(" " + kw_value)
                        self.sparql_query = self.sparql_query + self.sparql_query_last_input[-1]
                        self.logger.info("%s - keyword added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "sparql-variables-dropdown":
                    if var_value is not None:
                        self.sparql_query_last_input.append(" " + var_value)
                        if 'COUNT ( ?[...] ) AS' in self.sparql_query:
                            self.sparql_query = self.sparql_query.replace(' ?[...]', self.sparql_query_last_input[-1])
                        else:
                            self.sparql_query = self.sparql_query + self.sparql_query_last_input[-1]
                        self.logger.info("%s - variable added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "sparql-syntax-dropdown":
                    if syn_value is not None:
                        self.sparql_query_last_input.append(" " + syn_value)
                        self.sparql_query = self.sparql_query + self.sparql_query_last_input[-1]
                        self.logger.info("%s - syntax added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "add_to_query_button":
                    if n_add and value is not None:
                        self.sparql_query_last_input.append(' ' + value)
                        self.sparql_query = self.sparql_query + self.sparql_query_last_input[-1]
                        self.logger.info("user-text-input %s added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "clear_query_button":
                    if n_clear:
                        self.sparql_query_last_input = ['']
                        self.sparql_query = ''
                        self.logger.info("sparql query cleared by user")
                        self.clear_selection_for_template_query()
                elif input_id == "delete_query_button":
                    if n_delete:
                        self.sparql_query = self.sparql_query.replace(self.sparql_query_last_input[-1], '')
                        self.sparql_query_last_input.remove(self.sparql_query_last_input[-1])
                        self.logger.info('last input from user deleted from sparql query, triggered by user')
                elif input_id == "sparql_template_1" and n_template1:
                    self.sparql_query_last_input.append("SELECT (COUNT(?x) AS ?nb) \n{ ?x a owl:Class . }")
                    self.sparql_query = self.sparql_query_last_input[-1]
                    self.clear_selection_for_template_query()
                    self.logger.info("template: %s added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "sparql_template_2" and n_template2:
                    self.sparql_query_last_input.append(" PREFIX : <" + self.onto.iri + "#>" + "SELECT ?x WHERE { ?x :[edge] :[node] .}")
                    self.sparql_query = self.sparql_query_last_input[-1]
                    self.clear_selection_for_template_query()
                    self.logger.info("template: %s added to sparql query", self.sparql_query_last_input[-1])
                elif input_id == "graph" and selection != {'nodes': [], 'edges': []} and on_select:
                    self.complete_sparql_query_with_selection(selection)
            return self.sparql_query
        
        # create callbacks to toggle hide/show sections - COLOR section
        @app.callback(
            Output("color-show-toggle", "is_open"),
            [Input("color-show-toggle-button", "n_clicks")],
            [State("color-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info("color section was hidden, triggered by user")
                else:
                    self.logger.info("color section was shown, triggered by user")
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - COLOR section
        @app.callback(
            Output("size-show-toggle", "is_open"),
            [Input("size-show-toggle-button", "n_clicks")],
            [State("size-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info("size section was hidden, triggered by user")
                else:
                    self.logger.info("size section was shown, triggered by user")
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - Template section
        @app.callback(
            Output("template-show-toggle", "is_open"),
            [Input("template-show-toggle-button", "n_clicks")],
            [State("template-show-toggle", "is_open")],
        )
        def toggle_template_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info("template section was hidden, triggered by user")
                else:
                    self.logger.info("template section was shown, triggered by user")
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - A-Box-DP section
        @app.callback(
            Output("abox-dp-show-toggle", "is_open"),
            [Input("abox-dp-show-toggle-button", "n_clicks")],
            [State("abox-dp-show-toggle", "is_open")],
        )
        def toggle_template_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info("A-Box Data Property section was hidden, triggered by user")
                else:
                    self.logger.info("A-Box Data Property section was shown, triggered by user")
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - Edge Selection section
        @app.callback(
            Output("edge-selection-show-toggle", "is_open"),
            [Input("edge-selection-show-toggle-button", "n_clicks")],
            [State("edge-selection-show-toggle", "is_open")],
        )
        def toggle_template_collapse(n, is_open):
            if n:
                if is_open:
                    self.logger.info("edge selection section was hidden, triggered by user")
                else:
                    self.logger.info("edge selection section was shown, triggered by user")
                return not is_open
            return is_open

        @app.callback(
            [Output('node-selection', 'children'),
             Output('edge-selection', 'children')],
            [Input('graph', 'selection')])
        def show_dp_from_selected_node(x):
            s_node = ''
            s_edge = ''
            if len(x['nodes']) > 0:
                for node in self.data['nodes']:
                    if [node['id']] == x['nodes']:
                        if node['T/A'] == 'T':
                            return s_node, s_edge
                        s_node = [html.Div(x['nodes'] + [': '])]
                        if node['title'] == '':
                            return s_node + [html.Div(['No Data-Properties for this A-Box'])], s_edge
                        separator = ',\n '
                        partition = node['title'].partition(separator)
                        if separator in node['title']:
                            s_node = s_node + [html.Div([partition[0]])]
                            while separator in partition[2]:
                                partition = partition[2].partition(separator)
                                s_node = s_node + [html.Div([partition[0]])]
                            s_node = s_node + [html.Div([partition[2]])]
                        else:
                            s_node = s_node + [html.Div([node['title']])]
            elif len(x['edges']) > 0:
                for edge in self.data['edges']:
                    if [edge['id']] == x['edges']:
                        separator = ',\n '
                        partition_id = edge['id'].partition(separator)
                        partition_label = edge['label'].partition(separator)
                        if (separator in edge['id']) and (separator in edge['label']):
                            s_edge = [html.Div([partition_label[0]] + [': '])]
                            s_edge = s_edge + [html.Div([partition_id[0]])]
                            while (separator in partition_id[2]) and (separator in partition_label[2]):
                                partition_id = partition_id[2].partition(separator)
                                partition_label = partition_label[2].partition(separator)
                                s_edge = s_edge + [html.Div([partition_label[0]] + [': '])]
                                s_edge = s_edge + [html.Div([partition_id[0]])]
                            s_edge = s_edge + [html.Div([partition_label[2]] + [': '])]
                            s_edge = s_edge + [html.Div([partition_id[2]])]
                        else:
                            s_edge = [html.Div([edge['label']] + [': '])]
                            s_edge = s_edge + [html.Div([edge['id']])]
            return s_node, s_edge

        # create the main callbacks
        @app.callback(
            [Output('graph', 'data'),
             Output('color-legend-popup', 'children'),
             Output('textarea-result-output', 'children'), 
             Output('sparql_query_history', 'children'),
             Output('graph', 'selection')],
            [Input('search_graph', 'value'),
             Input('color_nodes', 'value'),
             Input('color_edges', 'value'),
             Input('size_nodes', 'value'),
             Input('size_edges', 'value'),
             Input('evaluate_query_button', 'n_clicks'),
             Input('clear-query-history-button', 'n_clicks'),
             Input('query-history-length-slider','value'),
             Input("color-legend-toggle", "n_clicks")],
            [State('graph', 'data')]
        )
        def setting_pane_callback(search_text, color_nodes_value, color_edges_value,
                                  size_nodes_value, size_edges_value, n_evaluate, n_clear, query_history_length,
                                  n_legend, graph_data):
            # fetch the id of option which triggered
            ctx = dash.callback_context
            flat_res_list_children = self.sparql_query_result
            sparql_query_history_children = []
            selection = {'nodes': [], 'edges': []}
            # if its the first call
            if not ctx.triggered:
                self.logger.info("no trigger by user")
                return [self.data, get_color_popover_legend_children(),
                        flat_res_list_children, sparql_query_history_children, selection]
            else:
                # find the id of the option which was triggered
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # perform operation in case of search graph option
                if input_id == "search_graph":
                    graph_data = _callback_search_graph(graph_data, search_text)
                    self.logger.info("shown graph data filtered, triggered by user")
                # In case filter nodes was triggered
                elif input_id == 'evaluate_query_button' and n_evaluate:
                    graph_data, flat_res_list_children, selection = self._callback_filter_nodes(graph_data)
                if input_id == "clear-query-history-button" and n_clear:
                    self.counter_query_history= 0
                    self.sparql_query_history = ""
                    self.logger.info("query history was cleared, triggered by user")
                # If color node text is provided
                if input_id == 'color_nodes':
                    graph_data, self.node_value_color_mapping = self._callback_color_nodes(color_nodes_value)
                    self.logger.info("Nodes were recolored, triggered by user")
                # If color edge text is provided
                if input_id == 'color_edges':
                    graph_data, self.edge_value_color_mapping = self._callback_color_edges(color_edges_value)
                    self.logger.info("Edges were recolored, triggered by user")
                # If size node text is provided
                if input_id == 'size_nodes':
                    graph_data = self._callback_size_nodes(size_nodes_value)
                    self.logger.info("Nodes were resized, triggered by user")
                # If size edge text is provided
                if input_id == 'size_edges':
                    graph_data = self._callback_size_edges(size_edges_value)
                    self.logger.info("Edges were resized, triggered by user")
            # create the color legend children
            color_popover_legend_children = get_color_popover_legend_children(
                self.node_value_color_mapping, self.edge_value_color_mapping)
            self.logger.info("color legend was updated, triggered by user")
            # update the sparql query history
            sparql_query_history_children = self._callback_sparql_query_history(query_history_length)
            self.logger.info("query history is shown with a length of %i", query_history_length)
            # finally return the modified data
            return [graph_data, color_popover_legend_children, flat_res_list_children,
                    sparql_query_history_children, selection]
        # return server
        return app

    def plot(self, debug=False, host="127.0.0.1", port=8050, directed=False, vis_opts=None):
        """Plot the Jaal by first creating the app and then hosting it on default server

        Parameter
        ----------
            debug (boolean)
                run the debug instance of Dash?

            host: string
                ip address on which to run the dash server (default: 127.0.0.1)

            port: string
                port on which to expose the dash server (default: 8050)

            directed (boolean):
                whether the graph is directed or not (default: False)

            vis_opts: dict
                the visual options to be passed to the dash server (default: None)
        """
        # call the create_graph function
        app = self.create(directed=directed, vis_opts=vis_opts)
        # run the server
        app.run_server(debug=debug, host=host, port=port)