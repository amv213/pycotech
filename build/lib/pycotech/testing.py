from pycotech.utils import *
from pycotech import plw_player
import configparser
from pathlib import Path
import logging


logging.basicConfig()
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")
logging.getLogger('pycotech.utils').setLevel("DEBUG")

#print(read_txt('NOV_2020.txt'))
df = read_plw('NOV 2020.PLW')
print(df)

stream = to_pico_stream(df)
print(stream)

df = from_pico_stream(stream)
print(df)

#print(map_channels('NOV 2020.PLW'))

#print(to_pico_stream(read_txt('NOV_2020.txt')))
#print(to_pico_stream(read_plw('NOV 2020.PLW')))