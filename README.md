<img src="jaal/assest/logo_sqv.png" alt="sqv logo"/>


*Your interactive ontology visualizing and SPARQL query formulation tool*

[[_TOC_]]

## What is *SPARQL Query Viz*

*SPARQL Query Viz* is a python based interactive ontology visualizing tool, that supports you to compose SPARQL queries interactively. 

The straightforward visualization can be adjusted to your needs by coloring and sizing of the graph elements. You can also turn of the visualization of *ABoxes* if the visualized ontology is cluttering the display. 

*SPARQL Query Viz* provides an interactive query formulation and composition panel, that enables you to write queries, by making use of templates and other useful features. You can evaluate the queries and see the visualized result in the context of the ontology.

## Requirements

*SPARQL Query Viz* requires the following python packages, 
1. Dash
    - dash_core_components
    - dash_html_components 
2. dash_bootstrap_components
3. visdcc
4. ontor
5. owlready2

## Installation

1. Clone the repo from [GitLab](https://gitlab.lrz.de/maximilianmayerhofer/SPARQL-Query-Viz)
2. Set up a virtual enivornment, by using `python -m venv myenv` and activate the env:
    - (Windows) `.\\myvenv\\Scripts\\activate.bat`
    - (Linux & MacOS) `source myvenv/bin/activate`

## Getting started

To visualize the included *Pizza-ontology*, the file `SPARQLQueryViz_run_pizza_example.py` has to be excecuted.
Alternativly the following two lines of code also do the job:

```python
from jaal import Jaal
jl = Jaal(iri = "http://example.org/onto-ex.owl", path = "./jaal/datasets/ontologies/pizza", abox = True)
jl.plot(host = "127.0.0.1", port = 8050, directed = True, vis_opts = "small")
```

1. The main visualization class `Jaal` is imported. 
2. `Jaal` is initialised by passing the following optional arguments to the constructor:
    - `iri`: The *Internationalized Resource Identifier* of the ontology
    - `path`: The path to the ontology file
    - `abox`: The option to turn on or off the visualization of the *ABoxes* in the ontology
3. The `plot` method of `Jaal` is called with the following optional arguments_
    - `host`: The host of the `Dash`-app
    - `port`: The port of the `Dash`-app
    - `directed`: The option to visualize the edges with arrowheads
    - `vis_opts`: The option to pass additional visualization options to the `visdcc`-graph

Note, that all of the arguments are optional. The default values for these aruments are the same as passed to the functions in the example above. Except for the argument `vis_opts` in the `plot` method: The default value here is `vis_opts = None `. Passing the keyword `"small"` adjusts the visualization options for small ontologies.

After running the plot, the console will prompt the default localhost address (`127.0.0.1:8050`) where Jaal is running. Access it to see the following dashboard:

<img src="jaal/assest/dashboard.png" alt="dashboard"/>

## 👉 Features

At present, the dashboard consist of following sections,
1. **Setting panel:** here we can play with the graph data, it further contain following sections:
    - **Search:** can be used to find a node in graph
    - **Filter:** supports pandas query language and can be used to filter the graph data based on nodes or edge features.
    - **Color:** can be used to color nodes or edges based on their categorical features. Note, currently only features with at max 20 cardinality are supported. 
    - **Size:** can be used to size nodes or edges based on their numerical features.
2. **Graph:** the network graph in all its glory :)

## 👉 Examples

### 1. Searching
<img src="jaal/assest/jaal_search.gif" alt="dashboard"/>

### 2. Filtering
<img src="jaal/assest/jaal_filter.gif" alt="dashboard"/>

### 3. Coloring
<img src="jaal/assest/jaal_color.gif" alt="dashboard"/>

### 4. Size
<img src="jaal/assest/jaal_size.gif" alt="dashboard"/>

## 👉 Extra settings

### Display edge label

To display labels over edges, we need to add a `label` attribute (column) in the `edge_df`. Also, it has to be in `string` format. 
For example, using the GoT dataset, by adding the following line before the `Jaal` call, we can display the edge labels.

```python
# add edge labels
edge_df.loc[:, 'label'] = edge_df.loc[:, 'weight'].astype(str)
```

### Directed edges

By default, `Jaal` plot undirected edges. This setting can be changed by,

```python
Jaal(edge_df, node_df).plot(directed=True)
```

### Using vis.js settings

We can tweak any of the `vis.js` related network visualization settings. An example is,

```python
# init Jaal and run server
Jaal(edge_df, node_df).plot(vis_opts={'height': '600px', # change height
                                      'interaction':{'hover': True}, # turn on-off the hover 
                                      'physics':{'stabilization':{'iterations': 100}}}) # define the convergence iteration of network

```

For a complete list of settings, visit [vis.js website](https://visjs.github.io/vis-network/docs/network/).

### Using gunicorn

We can host Jaal on production level HTTP server using `gunicorn` by first creating the app file (`jaal_app.py`),

```python
# import
from jaal import Jaal
from jaal.datasets import load_got
# load the data
edge_df, node_df = load_got()
# create the app and server
app = Jaal(edge_df, node_df).create()
server = app.server
```

then from the command line, start the server by,

```
gunicorn jaal_app:server
```

Note, `Jaal.create()` takes `directed` and `vis_opts` as arguments. (same as `Jaal.plot()` except the `host` and `port` arguments)

## 👉 Common Problems

### Port related issue

If you are facing port related issue, please try the following way to run Jaal. It will try different ports, until an empty one is found.

```python
port=8050
while True:
    try:
        Jaal(edge_df, node_df).plot(port=port)
    except:
        port+=1
```

## 👉 Issue tracker

Please report any bug or feature idea using Jaal issue tracker: https://github.com/imohitmayank/jaal/issues

## 👉 Collaboration

Any type of collaboration is appreciated. It could be  testing, development, documentation and other tasks that is useful to the project. Feel free to connect with me regarding this.

## Contact

You can connect with me on [LinkedIn](www.linkedin.com/in/maximilian-mayerhofer-41804917b)

## License

*SPARQL-Query-Viz* is licensed under the terms of the MIT License (see the file
LICENSE).
