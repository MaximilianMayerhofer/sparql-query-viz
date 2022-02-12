# import
from jaal import Jaal
import logging
logging.info("Jaal-example is executed")
Jaal(iri="onto-example-new.owl", path="./onto-example-new.owl", abox=False).plot(directed=True)