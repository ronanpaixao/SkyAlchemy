#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""
# Built-in imports
from __future__ import division, unicode_literals, print_function

import sys
import os
import os.path as osp
import subprocess
import ctypes
import logging
reload(logging)  # Needed inside Spyder IDE
import argparse

#%% Setup PyQt's v2 APIs. Must be done before importing PyQt or PySide
import rthook

#%% Third-party imports
from qtpy import QtCore, QtGui, QtWidgets, uic

import six

#%% Global functions
# PyInstaller utilities
def frozen(filename):
    """Returns the filename for a frozen file (program file which may be
    included inside the executable created by PyInstaller).
    """
    if getattr(sys, 'frozen', False):
        return osp.join(sys._MEIPASS, filename)
    else:
        return filename

# I usually need some sort of file/dir opening function
if sys.platform == 'darwin':
    def show_file(path):
        subprocess.Popen(['open', '--', path])
    def open_default_program(path):
        subprocess.Popen(['start', path])
elif sys.platform == 'linux2':
    def show_file(path):
        subprocess.Popen(['xdg-open', '--', path])
    def open_default_program(path):
        subprocess.Popen(['xdg-open', path])
elif sys.platform == 'win32':
    def show_file(path):
        subprocess.Popen(['explorer', '/select,', path])
    open_default_program = os.startfile

#%% Simple thread example (always useful to avoid locking the GUI)
class CallbackThread(QtCore.QThread):
    """Simple threading example.

    The thread executes a callback function. Use self if you want to store
    variables as the thread instance's attributes. It is also useful to use
    arguments as default values. This examples prints after 2 seconds:

    >>> def callback_fcn(self, t=2):
    ...     self.sleep(t)
    ...     print("Thread Finished")
    ...
    >>> thread = CallbackThread()
    >>> thread.callback = callback_fcn
    >>> thread.start()  # Finishes after 2 seconds
    """
    def __init__(self, *args, **kwargs):
        super(CallbackThread, self).__init__(*args, **kwargs)
        self.callback = lambda *args: None
        self.ret = None

    def __del__(self):
        self.wait()

    def run(self):
        self.ret = self.callback(self)

#%% Qt-enabled logging handler. Allows logging to GUI
class ConsoleWindowLogHandler(logging.Handler, QtCore.QObject):
    """Qt-enabled logging handler

    Allows logging to GUI by connecting the ``log`` signal to the receiving
    object's slot.
    """
    # Qt signals
    log = QtCore.pyqtSignal(str, name="log")

    def __init__(self, parent=None):
        super(ConsoleWindowLogHandler, self).__init__()
        QtCore.QObject.__init__(self, parent)

    def emit(self, logRecord):
        message = unicode(self.format(logRecord))
        self.log.emit(message)

#%% Main window class
class WndMain(QtWidgets.QMainWindow):
    ### Initialization
    def __init__(self, *args, **kwargs):
        super(WndMain, self).__init__(*args, **kwargs)
        # Setup settings storage
        self.settings = QtCore.QSettings("settings.ini",
                                         QtCore.QSettings.IniFormat)
        # Initialize UI (open main window)
        self.initUI()
        # Logging setup
        consoleHandler = ConsoleWindowLogHandler(self.txtLog)
        logger = logging.getLogger()
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        consoleHandler.setFormatter(logger.handlers[0].formatter)
        logger.name = "<app_name>"
        logger.addHandler(consoleHandler)
        consoleHandler.log.connect(self.on_consoleHandler_log)
        self.logger = logger
        # Threading example with new-style connections
#        self.thread = CallbackThread(self)
#        def callback_fcn(self, t=2):  # Use defaults to pass arguments
#            self.sleep(t)
#            logging.info("Thread finished.")  # Shouldn't translate log msgs
#        self.thread.callback = callback_fcn
#        self.thread.finished.connect(self.on_thread_finished)
#        self.thread.start()
        dll = ctypes.windll.shell32
        buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH + 1)
        try:
            if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
                savedir = osp.join(buf.value, "My Games", "Skyrim", "Saves")
                if not osp.exists(savedir) or not osp.isdir(savedir):
                    raise RuntimeError("Could not find savegame directory.")
                logging.debug("Savegame directory: %s", savedir)
            else:
                raise RuntimeError("Could not find savegame directory.")
        except:
            QtWidgets.QMessageBox.critical(self,
                                           self.tr("Error"),
                                           self.tr("Could not find savegame directory."))
        self.savedir = savedir
        savegames = [f for f in os.listdir(savedir) if f.endswith(".ess")]
        savegames = sorted(savegames,
                           key=lambda f: osp.getmtime(osp.join(savedir, f)),
                           reverse=True)
        for f in savegames:
            self.listSavegames.addItem(f)
        if len(savegames):
            self.open_savegame(savegames[0])


    def initUI(self):
        ui_file = frozen(osp.join('data', 'wndmain.ui'))
        uic.loadUi(ui_file, self)
        # Load window geometry and state
        self.restoreGeometry(self.settings.value("geometry", ""))
        self.restoreState(self.settings.value("windowState", ""))
        self.show()

    ### Function overrides:
    def closeEvent(self, e):
        # Write window geometry and state to config file
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        e.accept()

    ### Qt slots
    @QtCore.pyqtSlot()
    def on_thread_finished(self):
        QtWidgets.QMessageBox.information(self,
                                          self.tr("Information"),
                                          self.tr("Thread finished."))

    @QtCore.pyqtSlot(str)
    def on_consoleHandler_log(self, message):
        self.txtLog.appendPlainText(message)

    @QtCore.pyqtSlot()
    def on_listSavegames_itemDoubleClicked(item):
        open_savegame(item.text())

    ### Core functionality
    def open_savegame(self, filename):
        filename = osp.join(self.savedir, filename)



#%% Main execution
# Runs when executing script directly (not importing).
if __name__ == '__main__':
    ### Properly register window icon
    myappid = u'br.com.dapaixao.skyalchemy.1.0'
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    ### Grab existing QApplication
    # Only one QApplication is allowed per process. This allows running inside
    # Qt-based IDEs like Spyder.
    existing = QtWidgets.qApp.instance()
    if existing:
        app = existing
    else:
        app = QtWidgets.QApplication(sys.argv)
    ### Parsing command-line arguments/options
    parser = argparse.ArgumentParser()
    parser.add_argument("--lang", nargs="?",
                        help="Language to run (override system language)")
    try:
        args = parser.parse_args()
    except:
        parser.print_help()
        sys.exit(-1)
    lang = args.lang or QtCore.QLocale.system().name()
    ### Setup internationalization/localization (i18n/l10n)
    translator = QtCore.QTranslator()
    translator.load(frozen(osp.join("data", "main_{}.qm".format(lang))))
    QtWidgets.qApp.installTranslator(translator)
    ### Create main window and run
    wnd = WndMain()
    if existing:
        self = wnd  # Makes it easier to debug with Spyder's F9 inside a class
    else:
        sys.exit(app.exec_())
