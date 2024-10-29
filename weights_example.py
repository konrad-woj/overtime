"""Example how to use timeline graph chart from overtime. It has been improved
here internally in order to support edge weights and node attributes for
plotting.

If you're getting ImportError: cannot import name 'Iterable' from 'collections',
you can either downgrade Python to 3.9 or go to the pyecharts library and change
`from collections import Iterable` to `from collections.abc import Iterable`.
Unfortunately overtime and pyecharts are not maintained well enough.
"""
import pandas as pd
import overtime as ot
import math
import getpass
from aiml_graph_utils.sparql_util import SparqlClient, SPARQL_ENVS


def size_scaler_func(x):
    return (math.log(x, 2) + 1) * 5


def edge_size_scaler_func(x):
    return x * 100


def print_edges_over_time(graph):
    for time in graph.edges.timespan():
        print('\nTime:', time)
        edges_t = graph.edges.get_active_edges(time)
        edges_t.print()


# GET DATA.
edgelist_file = 'data/sir_edgelist.csv'
nodes_file = 'data/sir_nodes.csv'
sparql = SparqlClient(endpoint_root=SPARQL_ENVS['dev3'], repo_name='pubmed_hs',
                      user='admin', password=getpass.getpass('Enter password for SparqlClient.'))

prefixes = """
PREFIX diff: <https://rdf.iqvia.com/ns/kol/diffusion#>
PREFIX id: <https://rdf.iqvia.com/ns/ndwx/ids/provider#>
PREFIX score: <https://rdf.iqvia.com/ns/kol/score#>
PREFIX wgs: <http://www.w3.org/2003/01/geo/wgs84_pos#>
"""

edges_query = """
select 
(REPLACE(STR(?node1_), STR(id:), "") as ?node1)
(REPLACE(STR(?node2_), STR(id:), "") as ?node2)
(STR(?time) as ?tstart)
(STR(?time) as ?tend)
(STR(?value_) as ?weight) 
where { 
    values ?node1_ {id:10190737}.
    << << ?node1_ diff:reaches ?node2_ >> diff:time ?time >> diff:probability ?value_ .
    filter(?node1_ != ?node2_)
}
order by ?node1_ ?node2_ ?time_
limit 100
"""
sparql.execute_and_write(prefixes + edges_query, edgelist_file,
                         file_format='csv', skip_header=False)

nodes_query = f"""
select distinct (?label_ as ?label) (STR(?long_) as ?long) (STR(?lat_) as ?lat)
where {{
    {{
        select ?node1
        where {{ 
            {{
                {edges_query}
            }}
        }}
    }}
    union 
    {{
        select ?node2
        where {{ 
            {{
                {edges_query}
            }}
        }}
    }}
    BIND(COALESCE(?node1, ?node2) as ?label_)
    BIND(IRI(concat(str(id:), ?label_)) as ?id) 
    ?id wgs:long ?long_ ;
        wgs:lat ?lat_ .
}} 
"""
sparql.execute_and_write(prefixes + nodes_query, nodes_file, file_format='csv',
                         skip_header=False)



# CREATE GRAPH.
# Edgelist is required but node file is optional.
g = ot.TemporalDiGraph('example', data=ot.CsvInput(edgelist_file))
df = pd.read_csv(nodes_file, dtype={'label': str, 'long': float, 'lat': float})
g.nodes.add_data(df)

# Let me see the edge labels.
print_edges_over_time(g)
# Print nodes.
for idx, label in enumerate(g.nodes.labels()):
    print(idx, g.nodes.aslist()[idx].data)

# TEMPORAL GRAPH PLOTS
# Render graph with circular layout to html file.
t1 = ot.echarts_Timeline(graph=g, h=2, path='examples/html/sir_circular_t.html',
                         title='SIR example', subtitle='circular layout',
                         layout='circular',
                         edge_size_scaler_func=edge_size_scaler_func)

# Render graph with forced layout to html file.
t2 = ot.echarts_Timeline(graph=g, h=2, repulsion=50, gravity=0.03,
                         path='examples/html/sir_force_t.html',
                         title='SIR example', subtitle='force layout',
                         layout='force',
                         edge_size_scaler_func=edge_size_scaler_func, )

# Render graph with location layout to html file.
t3 = ot.echarts_Timeline(graph=g, h=2, x='long', y='lat',
                         path='examples/html/sir_location_t.html',
                         title='SIR example', subtitle='location layout',
                         layout='none')

