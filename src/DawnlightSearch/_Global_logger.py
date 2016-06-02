from __future__ import absolute_import

import logging
import logging.handlers

logging.basicConfig(format='%(asctime)s - %(thread)d:%(funcName)s:%(lineno)s - %(name)s - %(message)s')
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
