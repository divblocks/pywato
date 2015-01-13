# -*- coding: utf-8 -*-
import sys
import re
from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from crawlbase import *
import json
import random
import os.path
from sqlalchemy import *
from sqlalchemy.ext.declarative import *

logging.basicConfig(format = u'%(levelname)-8s [%(asctime)s] %(message)s', level = logging.DEBUG, filename = u'goog.log')

Base = declarative_base()

class TestCrawler(Crawler):
    def __init__(self, app, engine):
        Crawler.__init__(self,app, engine)
        self.webSiteRoot = "http://google.com"

    def start(self):
        self.browser.openPage(self.webSiteRoot)


logging.info("Starting to open google.com")

engine = create_engine('sqlite:///base.db')
Base.metadata.create_all(engine)

app = QApplication(sys.argv)

crawler = TestCrawler(app, engine)
crawler.start()

sys.exit()
