"""
Author: Mohit Mayank

Layout code for the application
"""
# import
import logging
import os
import visdcc
import base64
import random
import pandas as pd
from dash import dcc, html
import dash_bootstrap_components as dbc
from ontor import OntoEditor
import dash_daq as daq

# constants
# default node and edge size
DEFAULT_NODE_SIZE = 7
DEFAULT_EDGE_SIZE = 1

# default node and edge color
DEFAULT_COLOR = '#97C2FC'

# Taken from https://stackoverflow.com/questions/470690/how-to-automatically-generate-n-distinct-colors
KELLY_COLORS_HEX = [
    "#FFB300", # Vivid Yellow
    "#A6BDD7", # Very Light Blue
    "#803E75", # Strong Purple
    "#FF6800", # Vivid Orange
    "#C10020", # Vivid Red
    "#CEA262", # Grayish Yellow
    "#817066", # Medium Gray

    # The following don't work well for people with defective color vision
    "#007D34", # Vivid Green
    "#F6768E", # Strong Purplish Pink
    "#00538A", # Strong Blue
    "#FF7A5C", # Strong Yellowish Pink
    "#53377A", # Strong Violet
    "#FF8E00", # Vivid Orange Yellow
    "#B32851", # Strong Purplish Red
    "#F4C800", # Vivid Greenish Yellow
    "#7F180D", # Strong Reddish Brown
    "#93AA00", # Vivid Yellowish Green
    "#593315", # Deep Yellowish Brown
    "#F13A13", # Vivid Reddish Orange
    "#232C16", # Dark Olive Green
    ]

DEFAULT_OPTIONS = {
    'height': '800px',
    'width': '100%',
    'interaction':{'hover': True},
}

def get_options(directed: bool, opts_args: dict= None, physics: bool = True):
    """ defines the default options for the visdcc-graph and adds the optional arguments if not None

    :param directed: indicates whether the graph has directed edges
     :type directed: bool
     :param opts_args: optional arguments for the graph visualization
     :type opts_args: dict
     :param physics: indicates whether simulation physics are on or off
     :type physics: bool
     :return: options for the visdcc-graph visualization
     :rtype: dict
     """
    opts = DEFAULT_OPTIONS.copy()
    if not physics:
        opts['physics'] = {'enabled': False}
    else:
        pass
    #    opts['physics'] = {'stabilization':{'enabled': False}, 'timestep': 1, 'maxVelocity': 25, 'minVelocity': 0.1,
    #                       'barnesHut': {'theta': 1,'gravitationalConstant': -100000, 'centralGravity': 0.1,
    #                                     'springLength': 200, 'springConstant': 0.01, 'damping': 0.09,
    #                                     'avoidOverlap': 0.0 }}
    opts['edges'] = {'arrows': {'to': directed}, 'font': {'size': 0}}
    #opts['edges'] = { 'arrows': { 'to': directed }, 'chosen': {'edge': False, 'label': True}}
    #opts['edges'] = { 'arrows': { 'to': directed }, 'font': {'size': 0},'chosen': {'edge': False, 'label': 'function(values, id, selected, hovering) {values.size = 14;}'}}
    if opts_args is not None:
        opts.update(opts_args)
    return opts

def get_distinct_colors(n: int, for_nodes = True):
    """ return distinct colors, with two options to get different color schemes (for edges and nodes)

    :param n: number of distinct colors required
     :type n: int
     :param for_nodes: indicates whether nodes or edges will be colored
     :type for_nodes: bool
     :return: list of colors
     :rtype: list[str]
    """
    if for_nodes:
        return KELLY_COLORS_HEX[:n]
    else:
        return KELLY_COLORS_HEX[2:(n+2)]

def create_card(card_id: str, value, description: str):
    # todo not used (may be removed)
    """ creates card for high level stats

    :param card_id: id of the card
     :type card_id: str
     :param value: the children of the card
     :param description: long text detail of the setting
     :type description: str
     :return: dbc-element of the card
     :rtype: dbc.Card
    """
    return dbc.Card(
        dbc.CardBody(
            [
                html.H4(id=card_id, children=value, className='card-title'),
                html.P(children=description),
            ]))

def create_color_legend(text: str, color: str):
    """ creates individual row for the color legend

    :param text: text to appear in a row of the legend
     :type text: str
     :param color: color-code which will be the background color of the row
     :type color: str
     :return: html-element of the rwo of the legend
     :rtype: html.Div
    """
    return html.Div(text, style={'padding-left': '10px', 'width': '200px', 'background-color': color})

def create_info_text(text: str):
    """ creates the info text as html-element

    :param text: text to be shown in info popover
     :type text: str
     :return: html-element of info text in popover
     :rtype: html.Div
    """
    return create_row([
        html.Div(text, style={'padding-left': '10px'}),
    ])

def fetch_flex_row_style():
    return {'display': 'flex', 'flex-direction': 'row', 'justify-content': 'center', 'align-items': 'center'}

def create_row(children, style=None):
    if style is None:
        style = fetch_flex_row_style()
    return dbc.Row(children,
                   style=style,
                   className="column flex-display")

# forms for layout
search_form = dbc.FormGroup([
    dbc.Input(type="search", id="search_graph", placeholder="Search node or edge in graph..."),
    dbc.FormText(
         "Show the node or edge you are looking for",
         color="secondary",
    )
])

selected_edge_form = dbc.FormGroup([
    dbc.FormText(
        id = 'edge-selection',
        color="secondary",
    ),
])

a_box_dp_form = dbc.FormGroup([
    dbc.FormText(
        id = 'node-selection',
        color="secondary",
    ),
])

filter_node_form = dbc.FormGroup([
    # dbc.Label("Filter nodes", html_for="filter_nodes"),
    create_row([
        dbc.Button("Add", id="add_to_query_button", outline=True, color="secondary",size="sm"),
        daq.BooleanSwitch(id='add_node_edge_to_query_button', on=False, color="#FFB300",
                          label="Select Edge/Node", labelPosition="top"),
    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
    dbc.Textarea(id="filter_nodes", placeholder="Enter SPARQL-query here..."),
    create_row([
        dcc.Dropdown(
            id='sparql-keywords-dropdown',
            options=[
                {'label': 'Prefix', 'value': 'PREFIX'},
                {'label': 'Select', 'value': 'SELECT'},
                {'label': 'Insert', 'value': 'INSERT'},
                {'label': 'Delete', 'value': 'DELETE'},
                {'label': 'Union', 'value': 'UNION'},
                {'label': 'Count as', 'value': 'COUNT ( ?[...] ) AS'},
                {'label': 'Filter', 'value': 'FILTER'},
                {'label': 'Filter Exists', 'value': 'FILTER EXISTS'},
                {'label': 'Filter not Exists', 'value': 'FILTER NOT EXISTS'},
                {'label': 'Bind', 'value': 'BIND'},
                {'label': 'Values', 'value': 'VALUES'},
                {'label': 'Where', 'value': 'WHERE'}
            ],
            placeholder="Keywords",
            style={'width': '102px'},
        ),
        dcc.Dropdown(
            id='sparql-variables-dropdown',
            options=[
                {'label': 'X', 'value': '?x'},
                {'label': 'Y', 'value': '?y'},
                {'label': 'Z', 'value': '?z'}
            ],
            placeholder="Variables",
            style={'width': '97px'},
        ),
        dcc.Dropdown(
            id='sparql-syntax-dropdown',
            options=[
                {'label': '{', 'value': '{'},
                {'label': '}', 'value': '}'},
                {'label': '(', 'value': '('},
                {'label': ')', 'value': ')'},
                {'label': '.', 'value': '.'},
                {'label': 'rdf', 'value': 'rdf:'},
                {'label': 'rdfs', 'value': 'rdfs:'},
                {'label': 'owl', 'value': 'owl:'},
                {'label': 'owlready', 'value': 'owlready:'},
                {'label': 'xsd', 'value': 'xsd:'},
                {'label': 'obo', 'value': 'obo:'},
                {'label': 'subClassOf', 'value': 'rdfs:subClassOf*'},
                {'label': 'label', 'value': 'rdfs:label'}
            ],
            placeholder="Symbols",
            style={'width': '81px'},
        )
    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
    html.Hr(className="my-2"),
    html.H6("SPARQL Query to evaluate:"),
    html.Div(id='select-sparql', style={'whiteSpace': 'pre-line'}),
    html.Hr(className="my-2"),
    create_row([
        dbc.Button("Delete", id="delete_query_button", outline=True, color="secondary",size="sm"),
        dbc.Button("Clear", id="clear_query_button", outline=True, color="secondary",size="sm"),
        dbc.Button("Evaluate Query", id="evaluate_query_button", outline=True, color="secondary",size="sm"),
    ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
    dbc.FormText(
        html.P([
            "Filter graph data by using ",
            html.A("SPARQL Query syntax",
            href="https://www.w3.org/TR/sparql11-query/#grammar"),
        ]),
        color="secondary",
    ),
])

sparql_template_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
                id='sparql_template_dropdown',
                options=[
                    {'label': 'Get Number of owl-Classes', 'value': 'template_1.sparql'},
                    {'label': 'Find Instance with selected OP', 'value': 'template_2.sparql'},
                    {'label': 'Find Instance with selected OP', 'value': 'template_3.sparql'},
                ],
                placeholder="Templates",
                style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
        color="secondary",
    ),
])

sparql_library_form = dbc.FormGroup([
    dbc.FormText(
        create_row([
            dcc.Dropdown(
            id='sparql_library_dropdown',
            options=[
                {'label': 'Anzahl angetriebene Rolle Check', 'value': 'anzahl_angetriebene_rolle_check.sparql'},
                {'label': 'Projektinfo Check', 'value': 'projektinfo_check.sparql'},
                {'label': 'Rollen angetrieben Check', 'value': 'rollen_angetrieben_check.sparql'},
                {'label': 'Rollen antriebskenner Check', 'value': 'rollen_antriebskenner_check.sparql'},
                {'label': 'Rollen per Anlage Check', 'value': 'rollen_per_anlage_check.sparql'},
                {'label': 'Rollen per Segment Check', 'value': 'rollen_per_segment_check.sparql'},
                {'label': 'Rollen Winkel Check', 'value': 'rollen_winkel_check.sparql'},
                {'label': 'Rollenanzahl Pressuresystem Check', 'value': 'rollenanzahl_pressuresystem_check.sparql'},
                {'label': 'Rollenanzahl Zone Check', 'value': 'rollenanzahl_zone_check.sparql'},
                {'label': 'Rollennummer antriebsleistung check', 'value': 'rollennummer_antriebsleistung_check.sparql'},
                {'label': 'Segmentnummer Pressure Rolle Check', 'value': 'segmentnummer_pressure_rolle_check.sparql'},
                {'label': 'Segmentzahl Check', 'value': 'segmentzahl_check.sparql'},
                {'label': 'Summer Distribution Check', 'value': 'summe_distribution_check.sparql'},
            ],
            placeholder="Consistency Checks",
            style={'width': '100%'}),
        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
        'justify-content': 'space-between'}),
        color="secondary",
    ),
])

def get_select_form_layout(form_id: str, options: list, label: str, description: str):
    """ creates a select (dropdown) form with provides details

    :param form_id: id of the form
     :type form_id: str
     :param options: options to show in dropdown
     :type options: list
     :param label: label of the select dropdown bar
     :type label: list
     :param description: long text detail of the setting
     :type description: str
     :return: dbc-element of the form
     :rtype: dbc.FormGroup
    """
    if len(options)>1:
        return  dbc.FormGroup([
                    dbc.InputGroup([
                        dbc.InputGroupAddon(label, addon_type="append"),
                        dbc.RadioItems(id=form_id,
                            options=options, value=options[1].get('value')
                        ),]),
                    dbc.FormText(description, color="secondary",)
                ,])
    return dbc.FormGroup([
                    dbc.InputGroup([
                        dbc.InputGroupAddon(label, addon_type="append"),
                        dbc.RadioItems(id=form_id,
                            options=options
                        ),]),
                    dbc.FormText(description, color="secondary",)
                ,])

def get_categorical_features(df_: pd.DataFrame, unique_limit: int=20, blacklist_features: list[str]=None):
    """ identify categorical features for edge or node data and return their names
    NOTE: Additional logics: (1) cardinality should be within `unique_limit`, (2) remove blacklist_features

    :param df_: DataFrame from which the features are extracted
     :type df_: pd.DataFrame
     :param unique_limit: maximum of unique features
     :type unique_limit: int
     :param blacklist_features: list of features that will be excluded
     :type blacklist_features: list[str]
     :return: list of categorical features
     :rtype: list[str]
    """
    # identify the rel cols + None
    if blacklist_features is None:
        blacklist_features = ['shape', 'label', 'id']
    cat_features = ['None'] + df_.columns[(df_.dtypes == 'object') & (df_.apply(pd.Series.nunique) <= unique_limit)].tolist()
    # remove irrelevant cols
    try:
        for col in blacklist_features:
            cat_features.remove(col)
    except ValueError:
        pass
    # return
    return cat_features

def get_numerical_features(df_: pd.DataFrame):
    """ identify numerical features for edge or node data and return their names

    :param df_: DataFrame from which the features are extracted
     :type df_: pd.DataFrame
     :return: list of numerical features
     :rtype: list[str]
    """
    # supported numerical cols
    numerics = ['int16', 'int32', 'int64', 'float16', 'float32', 'float64']
    # identify numerical features
    numeric_features = ['None'] + df_.select_dtypes(include=numerics).columns.tolist()
    # remove blacklist cols (for nodes)
    try:
        numeric_features.remove('size')
    except ValueError:
        pass
    try:
        numeric_features.remove('width')
    except ValueError:
        pass
    # return
    return numeric_features

def get_app_layout(graph_data: dict, onto: OntoEditor, color_legends: list=None,
                   directed: bool=False, vis_opts: dict=None, abox: bool = False):
    """ create and return the layout of the app

    :param graph_data: network data in format of visdcc
     :type graph_data: dict
     :param onto: ontology
     :type onto: OntoEditor
     :param color_legends: list of legend elements
     :type color_legends: list
     :param directed: indicates whether the graph is directed
     :type directed: bool
     :param vis_opts: additional visualization options to pass to the visdcc-Network options
     :type vis_opts: dict
     :param abox: indicates whether A-Boxes are visualized
     :type abox: bool
     :return: html-element of the layout
     :rtype: html.Div
    """
    # Step 1-2: find categorical features of nodes and edges
    if color_legends is None:
        color_legends = []
    cat_node_features = get_categorical_features(pd.DataFrame(graph_data['nodes']).drop(columns=['color']), 20, ['shape', 'label', 'id', 'title', 'color'])
    cat_edge_features = get_categorical_features(pd.DataFrame(graph_data['edges']).drop(columns=['color', 'from', 'to', 'id','arrows']), 20, ['color', 'from', 'to', 'id'])
    # Step 3-4: Get numerical features of nodes and edges
    num_node_features = get_numerical_features(pd.DataFrame(graph_data['nodes']))
    num_edge_features = get_numerical_features(pd.DataFrame(graph_data['edges']))
    # Step 5: create and return the layout
    layout_with_abox = html.Div([
            create_row(html.H2(children="SPARQL Query Viz")),  # Title
            create_row(html.H3(children=onto.onto.name)), # Subtitle
            create_row([
                dbc.Col([
                    # setting panel
                    dbc.Form([
                        # ---- search section ----
                        create_row([
                            html.H6("Search"),
                            dbc.Button("Un-/Freeze", id="freeze-physics", outline=True,
                                       color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        html.Hr(className="my-2"),
                        search_form,

                        # ---- edge selection section ----
                        create_row([
                            html.H6("Selected Edge"),
                            dbc.Button("Hide/Show", id="edge-selection-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            selected_edge_form,
                            html.Hr(className="my-2"),
                        ], id="edge-selection-show-toggle", is_open=False),

                        # ---- abox data-properties section ----
                        create_row([
                            html.H6("A-Box Data-Properties"),
                            dbc.Button("Hide/Show", id="abox-dp-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            a_box_dp_form,
                            html.Hr(className="my-2"),
                        ], id="abox-dp-show-toggle", is_open=False),

                        # ---- SPARQL Template section ----
                        create_row([
                            html.H6("SPARQL Templates"),
                            dbc.Button("Hide/Show", id="template-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            sparql_template_form,
                            html.Hr(className="my-2"),
                        ], id="template-show-toggle", is_open=False),
                        
                        # ---- SPARQL Library section ----
                        create_row([
                            html.H6("SPARQL Library"),
                            dbc.Button("Hide/Show", id="library-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            sparql_library_form,
                            html.Hr(className="my-2"),
                        ], id="library-show-toggle", is_open=False),

                        # ---- SPARQL Query section ----
                        create_row([
                            html.H6("SPARQL Query"),
                            dbc.Button("Hide/Show", id="filter-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                            dbc.Button("Info", id="info-sparql-query-button", outline=True, color="info", size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Popover(
                            html.Div("To write an SPARQL query, type in a valid query in the text "
                                                      "field and click 'Add'. Or use the provided keywords to build "
                                                      "up the query. To see the result click 'Evaluate query'. "
                                                      "To erase the entered text click 'Delete'."),
                            id="info-sparql-popup", is_open=False,
                            target="info-sparql-query-button",style={'padding-left': '10px', 'width': '230px'}
                        ),
                        dbc.Collapse([
                            html.Hr(className="my-2"),
                            filter_node_form,
                        ], id="filter-show-toggle", is_open=False),

                        # ---- SPARQL Result section ----
                        create_row([
                            html.H6("SPARQL Result"),
                            dbc.Button("Hide/Show", id="result-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            dcc.Slider(
                                id='result-level-slider',
                                min=0,
                                max=4,
                                step=1,
                                value=1,
                                marks={
                                    0: '0',
                                    1: '1',
                                    2: '2',
                                    3: '3',
                                    4: '4'
                                },
                            ),
                            html.Div(id='textarea-result-output', style={'whiteSpace': 'pre-line'}),
                            html.Hr(className="my-2"),
                        ], id="result-show-toggle", is_open=False),

                        # ---- SPARQL History section ----
                        create_row([
                            html.H6("SPARQL History"),
                            dbc.Button("Hide/Show", id="history-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            dcc.Slider(
                                id='query-history-length-slider',
                                min=1,
                                max=5,
                                step=1,
                                value=3,
                                marks={
                                    1: '1',
                                    2: '2',
                                    3: '3',
                                    4: '4',
                                    5: '5'
                                },
                            ),
                            html.Div(id='sparql_query_history', style={'whiteSpace': 'pre-line'}),
                            html.Hr(className="my-2"),
                            dbc.Button("Clear", id="clear-query-history-button", outline=True, color="secondary",
                                       size="sm"),
                        ], id="history-show-toggle", is_open=False),

                        # ---- color section ----
                        create_row([
                            html.H6("Color"),  # heading
                            html.Div([
                                dbc.Button("Hide/Show", id="color-show-toggle-button", outline=True, color="secondary",
                                           size="sm"),  # legend
                                dbc.Button("Legends", id="color-legend-toggle", outline=True, color="secondary", size="sm"),
                                # legend
                            ]),
                            # add the legends popup
                            dbc.Popover(
                                children=color_legends,
                                id="color-legend-popup", is_open=False,
                                target="color-legend-toggle"
                            ),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            html.Hr(className="my-2"),
                            get_select_form_layout(
                                form_id='color_nodes',
                                options=[{'label': opt, 'value': opt} for opt in cat_node_features],
                                label='Color nodes by',
                                description='Select the categorical node property to color nodes by'
                            ),
                            get_select_form_layout(
                                form_id='color_edges',
                                options=[{'label': opt, 'value': opt} for opt in cat_edge_features],
                                label='Color edges by',
                                description='Select the categorical edge property to color edges by'
                            ),
                        ], id="color-show-toggle", is_open=False),

                        # ---- size section ----
                        create_row([
                            html.H6("Size"),  # heading
                            dbc.Button("Hide/Show", id="size-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            html.Hr(className="my-2"),
                            get_select_form_layout(
                                form_id='size_nodes',
                                options=[{'label': opt, 'value': opt} for opt in num_node_features],
                                label='Size nodes by',
                                description='Select the numerical node property to size nodes by'
                            ),
                            get_select_form_layout(
                                form_id='size_edges',
                                options=[{'label': opt, 'value': opt} for opt in num_edge_features],
                                label='Size edges by',
                                description='Select the numerical edge property to size edges by'
                            ),
                        ], id="size-show-toggle", is_open=False),

                    ], className="card", style={'padding': '5px', 'background': '#e5e5e5'}),
                ], width=3, style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}, align="start"),
                # graph
                dbc.Col(
                    visdcc.Network(
                        id='graph',
                        data=graph_data,
                        selection={'nodes': [], 'edges': []},
                        options=get_options(directed, vis_opts)),
                    width=9, align="start")])
        ])
    if abox:
        logging.info("returning app-layout with section for A-Box Data-Properties")
        return layout_with_abox
    logging.info("returning standard app-layout")
    return html.Div([
            create_row(html.H2(children="SPARQL Query Viz")),  # Title
            create_row(html.H3(children=onto.onto.name)), # Subtitle
            create_row([
                dbc.Col([
                    # setting panel
                    dbc.Form([
                        # ---- search section ----
                        create_row([
                            html.H6("Search"),
                            dbc.Button("Un-/Freeze", id="freeze-physics", outline=True,
                                       color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        html.Hr(className="my-2"),
                        search_form,

                        # ---- edge selection section ----
                        create_row([
                            html.H6("Selected Edge"),
                            dbc.Button("Hide/Show", id="edge-selection-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            selected_edge_form,
                            html.Hr(className="my-2"),
                        ], id="edge-selection-show-toggle", is_open=False),

                        # ---- SPARQL Template section ----
                        create_row([
                            html.H6("SPARQL Templates"),
                            dbc.Button("Hide/Show", id="template-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            sparql_template_form,
                            html.Hr(className="my-2"),
                        ], id="template-show-toggle", is_open=False),

                        # ---- SPARQL Query section ----
                        create_row([
                            html.H6("SPARQL Query"),
                            dbc.Button("Hide/Show", id="filter-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                            dbc.Button("Info", id="info-sparql-query-button", outline=True, color="info", size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Popover(
                            html.Div("To write an SPARQL query, type in a valid query in the text "
                                                      "field and click 'Add'. Or use the provided keywords to build "
                                                      "up the query. To see the result click 'Evaluate query'. "
                                                      "To erase the entered text click 'Delete'."),
                            id="info-sparql-popup", is_open=False,
                            target="info-sparql-query-button",style={'padding-left': '10px', 'width': '230px'}
                        ),
                        dbc.Collapse([
                            html.Hr(className="my-2"),
                            filter_node_form,
                        ], id="filter-show-toggle", is_open=False),

                        # ---- SPARQL Result section ----
                        create_row([
                            html.H6("SPARQL Result"),
                            dbc.Button("Hide/Show", id="result-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            dcc.Slider(
                                id='result-level-slider',
                                min=0,
                                max=4,
                                step=1,
                                value=1,
                                marks={
                                    0: '0',
                                    1: '1',
                                    2: '2',
                                    3: '3',
                                    4: '4'
                                },
                            ),
                            html.Div(id='textarea-result-output', style={'whiteSpace': 'pre-line'}),
                            html.Hr(className="my-2"),
                        ], id="result-show-toggle", is_open=False),

                        # ---- SPARQL History section ----
                        create_row([
                            html.H6("SPARQL History"),
                            dbc.Button("Hide/Show", id="history-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            dcc.Slider(
                                id='query-history-length-slider',
                                min=1,
                                max=5,
                                step=1,
                                value=3,
                                marks={
                                    1: '1',
                                    2: '2',
                                    3: '3',
                                    4: '4',
                                    5: '5'
                                },
                            ),
                            html.Div(id='sparql_query_history', style={'whiteSpace': 'pre-line'}),
                            html.Hr(className="my-2"),
                            dbc.Button("Clear", id="clear-query-history-button", outline=True, color="secondary",
                                       size="sm"),
                        ], id="history-show-toggle", is_open=False),

                        # ---- color section ----
                        create_row([
                            html.H6("Color"),  # heading
                            html.Div([
                                dbc.Button("Hide/Show", id="color-show-toggle-button", outline=True, color="secondary",
                                           size="sm"),  # legend
                                dbc.Button("Legends", id="color-legend-toggle", outline=True, color="secondary", size="sm"),
                                # legend
                            ]),
                            # add the legends popup
                            dbc.Popover(
                                children=color_legends,
                                id="color-legend-popup", is_open=False,
                                target="color-legend-toggle"
                            ),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            html.Hr(className="my-2"),
                            get_select_form_layout(
                                form_id='color_nodes',
                                options=[{'label': opt, 'value': opt} for opt in cat_node_features],
                                label='Color nodes by',
                                description='Select the categorical node property to color nodes by'
                            ),
                            get_select_form_layout(
                                form_id='color_edges',
                                options=[{'label': opt, 'value': opt} for opt in cat_edge_features],
                                label='Color edges by',
                                description='Select the categorical edge property to color edges by'
                            ),
                        ], id="color-show-toggle", is_open=False),

                        # ---- size section ----
                        create_row([
                            html.H6("Size"),  # heading
                            dbc.Button("Hide/Show", id="size-show-toggle-button", outline=True, color="secondary",
                                       size="sm"),
                        ], {**fetch_flex_row_style(), 'margin-left': 0, 'margin-right': 0,
                            'justify-content': 'space-between'}),
                        dbc.Collapse([
                            html.Hr(className="my-2"),
                            get_select_form_layout(
                                form_id='size_nodes',
                                options=[{'label': opt, 'value': opt} for opt in num_node_features],
                                label='Size nodes by',
                                description='Select the numerical node property to size nodes by'
                            ),
                            get_select_form_layout(
                                form_id='size_edges',
                                options=[{'label': opt, 'value': opt} for opt in num_edge_features],
                                label='Size edges by',
                                description='Select the numerical edge property to size edges by'
                            ),
                        ], id="size-show-toggle", is_open=False),

                    ], className="card", style={'padding': '5px', 'background': '#e5e5e5'}),
                ], width=3, style={'display': 'flex', 'justify-content': 'center', 'align-items': 'center'}, align="start"),
                # graph
                dbc.Col(
                    visdcc.Network(
                        id='graph',
                        data=graph_data,
                        selection={'nodes': [], 'edges': []},
                        options=get_options(directed, vis_opts)),
                    width=9, align="start")])
        ])