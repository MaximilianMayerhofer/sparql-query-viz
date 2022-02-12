# import
import ontor
from jaal import Jaal
from ontor import OntoEditor
import logging
logging.info("Jaal-example is executed")
Jaal(onto = ontor.OntoEditor("onto-example-new.owl","./onto-example-new.owl"), abox=False).plot(directed=True)