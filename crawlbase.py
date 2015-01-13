import types
from PySide.QtCore import *
from PySide.QtWebKit import *
import PySide
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import logging

def infomsg(logMessage):
    print(logMessage)
    logging.info(logMessage)

def debugmsg(logMessage):
    logging.debug(logMessage)

def only_numerics(seq):
    return filter(type(seq).isdigit, seq)

class Browser(QObject):
    def __init__(self):
        QObject.__init__(self)
        self.jqpath = 'jquery.js'
        self.page = QWebPage()
        self.page.settings().setAttribute(PySide.QtWebKit.QWebSettings.WebAttribute.AutoLoadImages, False)
        self.page.settings().setAttribute(PySide.QtWebKit.QWebSettings.JavaEnabled, False)
        self.page.settings().setAttribute(PySide.QtWebKit.QWebSettings.PluginsEnabled, False)

    def log(self, str):
        infomsg('Log message' + str)

    def wait(self, time):
        loop = QEventLoop()
        self.timer = QTimer()
        QObject.connect(self.timer, SIGNAL("timeout()"), loop, SLOT("quit()"))
        self.timer.start(time)
        loop.exec_()
        loop = None
        self.timer = None

    def jQueryInject(self):
        debugmsg("Injecting jquery")
        isInjectedAlready = self.evaluateCode('return jQuery.isReady;')
        if isInjectedAlready is True:
            return True
        self.evaluateFileScript(self.jqpath)
        def waitFunc():
            res = self.evaluateCode('return jQuery.isReady;')
            return res
        return self.waitFor(waitFunc, 1000, 2000, 100)

    def openPage(self, address):
        debugmsg('Waiting for load ' + address)
        self.timer = QTimer()
        loop = QEventLoop()
        QObject.connect(self.page, SIGNAL("loadFinished(bool)"),loop, SLOT("quit()"))
        QObject.connect(self.timer, SIGNAL("timeout()"), loop, SLOT("quit()"))
        self.timer.start(15000)
        self.page.mainFrame().load(address)
        loop.exec_()
        loop = None
        debugmsg('Waiting for load page ' + address + ' finished')
        if self.jQueryInject() == False:
            infomsg('Cannot inject jquery!!')
            return None
        return self.page.mainFrame().title

    def downloadImage(self, address):
        return 0

    def evaluateFileScript(self, scriptPath):
        debugmsg('Evaluating script file ' + scriptPath)
        scriptFile = QFile(scriptPath)
        scriptFile.open(QIODevice.ReadOnly)
        code = str(scriptFile.readAll())
        if len(code) == 0:
            infomsg('Readen script length is 0')
            return None
        result = self.page.mainFrame().evaluateJavaScript(code)
        return str(result)

    def objToString(self, obj):
        if isinstance(obj, bool):
            if obj is True:
                return "true"
            else:
                return "false"
        return str(obj)

    def waitFor(self, testCond, startInterval, waitPause, maxAttempts):
        self.wait(startInterval)
        attempts = 0
        while attempts < maxAttempts:
            if type(testCond) == types.FunctionType:
                condFuncRes = testCond()
                if type(condFuncRes) == str:
                    condition = eval(condFuncRes)
                else:
                    condition = condFuncRes
            if type(testCond) == str:
                condition = eval(testCond)
            if type(testCond) == bool:
                condition = testCond

            if condition is True:
                return True
            self.wait(waitPause)
            attempts += 1
        if attempts == maxAttempts:
            infomsg("Attempt limit exceeded")
            return False
        return True


    def evaluateCode(self, code):
        code = '(function () {' + code + '})();'
        debugmsg('Evaluating code ' + code)
        result = self.page.mainFrame().evaluateJavaScript(code)
        return result

    def saveCurrentHtmlToFile(self, fileName):
        debugmsg('Saving to file ' + fileName)
        html = self.page.mainFrame().toHtml()
        outputFile = QFile(fileName)
        outputFile.open(QFile.WriteOnly)
        outputFile.writeData(html, len(html))
        outputFile.close()

    def generateFormWithActionCode(self, field):
        str = '$("form[action='
        str += chr(39)
        str += field
        str += chr(39)
        str += ']")'
        return str

    def generateInputCode(self, field):
        str = '$("input[name='
        str += chr(39)
        str += field
        str += chr(39)
        str += ']")'
        return str

    def generateFormCode(self, field):
        str = '$("form[name='
        str += chr(39)
        str += field
        str += chr(39)
        str += ']")'
        return str

class Crawler(QObject):
    def __init__(self, app, engine):
        QObject.__init__(self)
        self.engine = engine
        self.app = app
        self.browser = Browser()
        self.linksList = list()
        Session = sessionmaker(bind=self.engine)
        self.session = Session()

    def makeInitialLogin(self,
                          userNameSetterCode,
                          passwordSetterCode,
                          submitCode):
        self.browser.evaluateCode(userNameSetterCode)
        self.browser.evaluateCode(passwordSetterCode)
        self.browser.evaluateCode(submitCode)
        self.browser.wait(2000)
        self.browser.jQueryInject()

    def makeStandardLogin(self,
                          userNameSetterCode,
                          passwordSetterCode,
                          submitCode,
                          evalSuccessCode):
        self.makeInitialLogin(userNameSetterCode, passwordSetterCode, submitCode)

        def waitFunc():
            txt = self.browser.evaluateCode(evalSuccessCode)
            if txt is None:
                return False
            return txt
        return self.browser.waitFor(waitFunc, 5000, 1000, 100)

