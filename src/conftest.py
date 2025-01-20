import logging

# make faker stop spamming DEBUG logs
logging.getLogger("faker").setLevel(logging.ERROR)
