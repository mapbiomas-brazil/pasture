from loguru import logger

logger.debug("That's it, beautiful and simple logging!")
logger.add("client.log",format="{time} [{level}] {name}:{module}:[{file}:{line}] {message} | {exception} ", rotation="500 MB",level='WARNING') 

