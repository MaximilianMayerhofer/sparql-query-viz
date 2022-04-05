# import
from sparql_query_viz import SQV

port = 8050
while True:
    try:
        SQV().plot(port=port, vis_opts="small")
    except:
        port += 1
