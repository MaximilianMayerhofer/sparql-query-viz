# import
from jaal import Jaal
import datetime
import logging
logfile = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S") + "_jaal.log"
logging.basicConfig(filename=logfile, level=logging.INFO)
logging.info("Jaal-example is executed")
Jaal().plot(directed=True)