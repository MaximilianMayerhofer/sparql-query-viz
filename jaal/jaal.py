"""
Author: Mohit Mayank

Main class for Jaal network visualization dashboard
"""
# import
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
from .layout import get_app_layout, get_distinct_colors, create_color_legend, get_categorical_features, get_numerical_features, DEFAULT_COLOR, DEFAULT_NODE_SIZE, DEFAULT_EDGE_SIZE


# class
class Jaal:
    """The main visualization class
    """
    def __init__(self, edge_df, onto: OntoEditor, node_df=None):
        """
        Parameters
        -------------
        edge_df: pandas dataframe
            The network edge data stored in format of pandas dataframe

        node_df: pandas dataframe (optional)
            The network node data stored in format of pandas dataframe
        """
        print("Parsing the data...", end="")
        self.data, self.scaling_vars = parse_dataframe(edge_df, node_df)
        self.filtered_data = self.data.copy()
        self.node_value_color_mapping = {}
        self.edge_value_color_mapping = {}
        self.sparql_query = ''
        self.sparql_query_history = ''
        self.counter_query_history = 0
        self.onto = onto
        print("Done")

    def _callback_search_graph(self, graph_data, search_text):
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

    def _callback_filter_nodes_output(self, graph_data, filter_nodes_text):
        try:
            res_list = list(self.onto.onto_world.sparql(filter_nodes_text))
            flat_res_list = [x for l in res_list for x in l]
            result = ""
            try:
                for res in flat_res_list:
                    result = result + str(res.name) + "\n"
            except:
                for res in flat_res_list:
                    result = result + str(res) + "\n"
        except:
            result = "Not a valid SPARQL query."
        return result

    def _callback_filter_nodes(self, graph_data, filter_nodes_text):
        """Filter the nodes based on the Python query syntax
        """
        self.filtered_data = self.data.copy()
        #node_df = pd.DataFrame(self.filtered_data['nodes'])
        #try:
        #    node_list = node_df.query(filter_nodes_text)['id'].tolist()
        #    nodes = []
        #    for node in self.filtered_data['nodes']:
        #        if node['id'] in node_list:
        #            nodes.append(node)
        #    self.filtered_data['nodes'] = nodes
        #    graph_data = self.filtered_data
        #except:
        #    graph_data = self.data
        #    print("wrong node filter query!!")

        try:
            res_list = list(self.onto.onto_world.sparql(self.sparql_query))
            flat_res_list = [x for l in res_list for x in l]
            res = []
            res_is_int = True
            for result in flat_res_list:
                if type(result) is not int:
                    res_is_int = False
                    
            if res_is_int:
                print("SPARQL-query result:", flat_res_list)
                graph_data = self.data
            else:
                for node in self.filtered_data['nodes']:
                    for result in flat_res_list:
                        if node['id'] == result.name:
                            res.append(node)
                self.filtered_data['nodes'] = res
                graph_data = self.filtered_data
            self.counter_query_history = self.counter_query_history + 1
            self.sparql_query_history = self.sparql_query_history + str(self.counter_query_history) + ": " + self.sparql_query + '\n'
            self.sparql_query = ""
        except:
            graph_data = self.data
            print("Not a valid SPARQL query.")
        return graph_data

    def _callback_sparql_query_history(self, number_of_shown_queries):
        sparql_query_history = self.sparql_query_history
        if self.counter_query_history > number_of_shown_queries:
            separator = str(self.counter_query_history - (number_of_shown_queries - 1)) + ": "
            partition = sparql_query_history.partition(separator)
            shown_sparql_query_history = partition[1] + partition[2]
        else:
            shown_sparql_query_history = sparql_query_history
        return shown_sparql_query_history

    def _callback_filter_edges(self, graph_data, filter_edges_text):
        """Filter the edges based on the Python query syntax
        """
        self.filtered_data = self.data.copy()
        edges_df = pd.DataFrame(self.filtered_data['edges'])
        try:
            edges_list = edges_df.query(filter_edges_text)['id'].tolist()
            edges = []
            for edge in self.filtered_data['edges']:
                if edge['id'] in edges_list:
                    edges.append(edge)
            self.filtered_data['edges'] = edges
            graph_data = self.filtered_data
        except:
            graph_data = self.data
            print("wrong edge filter query!!")
        return graph_data

    def _callback_color_nodes(self, graph_data, color_nodes_value):
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_nodes_value == 'None':
            # revert to default color
            for node in self.data['nodes']:
                node['color'] = DEFAULT_COLOR
        else:
            print("inside color node", color_nodes_value)
            unique_values = pd.DataFrame(self.data['nodes'])[color_nodes_value].unique()
            colors = get_distinct_colors(len(unique_values))
            value_color_mapping = {x:y for x, y in zip(unique_values, colors)}
            for node in self.data['nodes']:
                node['color'] = value_color_mapping[node[color_nodes_value]]
        # filter the data currently shown
        filtered_nodes = [x['id'] for x in self.filtered_data['nodes']]
        self.filtered_data['nodes'] = [x for x in self.data['nodes'] if x['id'] in filtered_nodes]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping
    
    def _callback_size_nodes(self, graph_data, size_nodes_value):

        # color option is None, revert back all changes
        if size_nodes_value == 'None':
            # revert to default color
            for node in self.data['nodes']:
                node['size'] = DEFAULT_NODE_SIZE
        else:
            print("Modifying node size using ", size_nodes_value)
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

    def _callback_color_edges(self, graph_data, color_edges_value):
        value_color_mapping = {}
        # color option is None, revert back all changes
        if color_edges_value == 'None':
            # revert to default color
            for edge in self.data['edges']:
                edge['color']['color'] = DEFAULT_COLOR
        else:
            print("inside color edge", color_edges_value)
            unique_values = pd.DataFrame(self.data['edges'])[color_edges_value].unique()
            colors = get_distinct_colors(len(unique_values))
            value_color_mapping = {x:y for x, y in zip(unique_values, colors)}
            for edge in self.data['edges']:
                edge['color']['color'] = value_color_mapping[edge[color_edges_value]]
        # filter the data currently shown
        filtered_edges = [x['id'] for x in self.filtered_data['edges']]
        self.filtered_data['edges'] = [x for x in self.data['edges'] if x['id'] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data, value_color_mapping

    def _callback_size_edges(self, graph_data, size_edges_value):
        # color option is None, revert back all changes
        if size_edges_value == 'None':
            # revert to default size
            for edge in self.data['edges']:
                edge['width'] = DEFAULT_EDGE_SIZE
        else:
            print("Modifying edge size using ", size_edges_value)
            # fetch the scaling value
            minn = self.scaling_vars['edge'][size_edges_value]['min']
            maxx = self.scaling_vars['edge'][size_edges_value]['max']
            # define the scaling function
            #scale_val = lambda x: 20*(x-minn)/(maxx-minn)
            # set the size after scaling
            for edge in self.data['edges']:
                # edge['width'] = scale_val(edge[size_edges_value])
                edge['width'] = edge[size_edges_value]
        # filter the data currently shown
        filtered_edges = [x['id'] for x in self.filtered_data['edges']]
        self.filtered_data['edges'] = [x for x in self.data['edges'] if x['id'] in filtered_edges]
        graph_data = self.filtered_data
        return graph_data

    def get_color_popover_legend_children(self, node_value_color_mapping={}, edge_value_color_mapping={}):
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
                    _popover_legend_children.append(
                        # dbc.PopoverBody(f"Key: {key}, Value: {value}")
                        create_color_legend(key, value)
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

    def forced_callback_excecution_at_beginning(self):
        """This function executes the callback functions for node and edge Coloring and Sizing at start of the app,
        without andy userinput. This is to ensure a default coloring and sizing of nodes and edges."""

        # Get list of categorical features from nodes
        cat_node_features = get_categorical_features(pd.DataFrame(self.data['nodes']), 20, ['shape', 'label', 'id'])
        # Define label and value for each categorical feature
        options = [{'label': opt, 'value': opt} for opt in cat_node_features]
        # If options has mor then one categorical feature, the callback function for nodes-coloring is executed once,
        # to set the first option as default value
        if len(options) > 1: self.data, self.node_value_color_mapping = self._callback_color_nodes(self.data,
                                                                                                   options[1].get(
                                                                                                       'value'))
        # Get list of categorical features from edges
        cat_edge_features = get_categorical_features(
            pd.DataFrame(self.data['edges']).drop(columns=['color', 'to']), 20,
            ['color', 'from', 'to', 'id'])
        # Define label and value for each categorical feature
        options = [{'label': opt, 'value': opt} for opt in cat_edge_features]
        # If options has mor then one categorical feature, the callback function for edge-coloring is executed once,
        # to set the first option as default value
        if len(options) > 1: self.data, self.edge_value_color_mapping = self._callback_color_edges(self.data,
                                                                                                   options[1].get(
                                                                                                       'value'))
        # Get list of numerical features from nodes
        num_node_features = get_numerical_features(pd.DataFrame(self.data['nodes']))
        # Define label and value for each numerical feature
        options = [{'label': opt, 'value': opt} for opt in num_node_features]
        # If options has mor then one numerical feature, the callback function for nodes-sizing is executed once,
        # to set the first option as default value
        if len(options) > 1: self.data = self._callback_size_nodes(self.data, options[1].get('value'))
        # Get list of numerical features from edges
        num_edge_features = get_numerical_features(pd.DataFrame(self.data['edges']))
        # Define label and value for each numerical feature
        options = [{'label': opt, 'value': opt} for opt in num_edge_features]
        # If options has mor then one numerical feature, the callback function for edge-sizing is executed once,
        # to set the first option as default value
        if len(options) > 1: self.data = self._callback_size_edges(self.data, options[1].get('value'))

    def create(self, directed=False, vis_opts=None, abox: bool = False):
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
        app = dash.Dash(external_stylesheets=[dbc.themes.BOOTSTRAP])

        # define layout
        app.layout = get_app_layout(self.data, self.onto, color_legends=self.get_color_popover_legend_children(), directed=directed, vis_opts=vis_opts, abox = abox)
        
        # get color_mapping and size_mapping once at the start
        self.forced_callback_excecution_at_beginning()

        # create callbacks to toggle legend popover
        @app.callback(
            Output("color-legend-popup", "is_open"),
            [Input("color-legend-toggle", "n_clicks")],
            [State("color-legend-popup", "is_open")],
        )
        def toggle_popover(n, is_open):
            if n:
                return not is_open
            return is_open

        # create callbacks to toggle hide/show sections - FILTER section
        @app.callback(
            Output("filter-show-toggle", "is_open"),
            [Input("filter-show-toggle-button", "n_clicks")],
            [State("filter-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
                return not is_open
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
                if input_id == "result-show-toggle-button":
                    return not is_open
                if input_id == "evaluate_query_button":
                    return True
            return is_open

        @app.callback(
            Output("history-show-toggle", "is_open"),
            [Input("history-show-toggle-button", "n_clicks")],
            [State("history-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n_show, is_open):
            if n_show:
                return not is_open
            return is_open
        
        @app.callback(
            Output("select-sparql", "children"),
            [Input("prefix-sparql-button", "n_clicks")],
            [Input("select-sparql-button", "n_clicks")],
            [Input("add_to_query_button", "n_clicks")],
            [Input("count-sparql-button", "n_clicks")],
            [Input("delete_query_button", "n_clicks")],
            [Input("as-sparql-button", "n_clicks")],
            [Input("filter-sparql-button", "n_clicks")],
            [State("filter_nodes", "value")],
        )
        def insert_select_sparql_keyword(n_prefix, n_select, n_add, n_count, n_delete, n_as, n_filter, value):
            ctx = dash.callback_context
            if self.sparql_query is None:
                self.sparql_query = ""

            if not ctx.triggered:
                return self.sparql_query
            else:
                # find the id of the option which was triggered
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # perform operation depending on which sparql button was triggered
                if input_id == "select-sparql-button":
                    if n_select:
                        self.sparql_query = self.sparql_query + "\n SELECT "
                elif input_id == "count-sparql-button":
                    if n_count:
                        self.sparql_query = self.sparql_query + "COUNT "
                elif input_id == "prefix-sparql-button":
                    if n_prefix:
                        self.sparql_query = self.sparql_query + "PREFIX : <" + self.onto.iri + "#>"
                elif input_id == "as-sparql-button":
                    if n_as:
                        self.sparql_query = self.sparql_query + "AS "
                elif input_id == "filter-sparql-button":
                    if n_filter:
                        self.sparql_query = self.sparql_query + "FILTER "
                elif input_id == "add_to_query_button":
                    if n_add and value is not None:
                        self.sparql_query = self.sparql_query + value
                elif input_id == "delete_query_button":
                    if n_delete:
                        self.sparql_query = ""

            return self.sparql_query
        
        # create callbacks to toggle hide/show sections - COLOR section
        @app.callback(
            Output("color-show-toggle", "is_open"),
            [Input("color-show-toggle-button", "n_clicks")],
            [State("color-show-toggle", "is_open")],
        )
        def toggle_filter_collapse(n, is_open):
            if n:
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
                return not is_open
            return is_open

        @app.callback(
            Output('edge-selection', 'children'),
            [Input('graph', 'selection')])

        def show_selected_edge(x):
            s = ''
            if len(x['edges']) > 0:
                s = [s] + [html.Div(i) for i in x['edges']]
            return s

        @app.callback(
            Output('node-selection', 'children'),
            [Input('graph', 'selection')])
        def show_dp_from_selected_node(x):
            s = ''
            if len(x['nodes']) > 0:
                s = [s] + [html.Div(i) for i in x['nodes']]
            return s

        # create the main callbacks
        @app.callback(
            [Output('graph', 'data'), Output('color-legend-popup', 'children'), 
             Output('textarea-result-output', 'children'), 
             Output('sparql_query_history', 'children')],
            [Input('search_graph', 'value'),
            Input('filter_nodes', 'value'),
            Input('color_nodes', 'value'),
            Input('color_edges', 'value'),
            Input('size_nodes', 'value'),
            Input('size_edges', 'value'),
            Input('evaluate_query_button', 'n_clicks'),
            Input('clear-query-history-button', 'n_clicks'),
            Input('query-history-length-slider','value')],
            [State('graph', 'data')]
        )
        def setting_pane_callback(search_text, filter_nodes_text,  
                    color_nodes_value, color_edges_value, size_nodes_value, size_edges_value, n_evaluate, n_clear, query_history_length, graph_data):
            # fetch the id of option which triggered
            ctx = dash.callback_context
            flat_res_list_children = []
            sparql_query_history_children = []
            # if its the first call
            if not ctx.triggered:
                print("No trigger")
                return [self.data, self.get_color_popover_legend_children(), flat_res_list_children, sparql_query_history_children]
            else:
                # find the id of the option which was triggered
                input_id = ctx.triggered[0]['prop_id'].split('.')[0]
                # perform operation in case of search graph option
                if input_id == "search_graph":
                    graph_data = self._callback_search_graph(graph_data, search_text)
                # In case filter nodes was triggered
                elif (input_id == 'evaluate_query_button' and n_evaluate) or input_id == 'query-history-length-slider':
                    graph_data = self._callback_filter_nodes(graph_data, filter_nodes_text)
                    flat_res_list_children = self._callback_filter_nodes_output(graph_data, filter_nodes_text)
                    sparql_query_history_children = self._callback_sparql_query_history(query_history_length)
                if input_id == "clear-query-history-button" and n_clear:
                    self.counter_query_history= 0
                    self.sparql_query_history = ""
                    sparql_query_history_children = self._callback_sparql_query_history(query_history_length)
                # In case filter edges was triggered
                #elif input_id == 'filter_edges':
                #    graph_data = self._callback_filter_edges(graph_data, filter_edges_text)
                # If color node text is provided
                if input_id == 'color_nodes':
                    graph_data, self.node_value_color_mapping = self._callback_color_nodes(graph_data, color_nodes_value)
                # If color edge text is provided
                if input_id == 'color_edges':
                    graph_data, self.edge_value_color_mapping = self._callback_color_edges(graph_data, color_edges_value)
                # If size node text is provided
                if input_id == 'size_nodes':
                    graph_data = self._callback_size_nodes(graph_data, size_nodes_value)
                # If size edge text is provided
                if input_id == 'size_edges':
                    graph_data = self._callback_size_edges(graph_data, size_edges_value)
            # create the color legend children
            color_popover_legend_children = self.get_color_popover_legend_children(self.node_value_color_mapping, self.edge_value_color_mapping)
            # finally return the modified data
            return [graph_data, color_popover_legend_children, flat_res_list_children, sparql_query_history_children]
        # return server
        return app

    def plot(self, debug=False, host="127.0.0.1", port="8050", directed=False, vis_opts=None, abox: bool = False):
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
        app = self.create(directed=directed, vis_opts=vis_opts, abox= abox)
        # run the server
        app.run_server(debug=debug, host=host, port=port)