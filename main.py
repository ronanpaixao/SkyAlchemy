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
import base64
from io import BytesIO
from collections import OrderedDict
try:
    from queue import PriorityQueue  # PY3
except ImportError:
    from Queue import PriorityQueue  # PY2
import operator

#%% Setup PyQt's v2 APIs. Must be done before importing PyQt or PySide
import rthook

#%% Third-party imports
from qtpy import QtCore, QtGui, QtWidgets, uic

import six
from jinja2 import Environment, FileSystemLoader


#%% Application imports
import savegame
import skyrimdata
from skyrimdata import db

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
class SavegameThread(QtCore.QThread):
    """Savegame thread.

    Concentrates all intensive processing to avoid GUI freezes.
    """
    newJob = QtCore.Signal(str, int)
    jobStatus = QtCore.Signal(int)
    generalData = QtCore.Signal(str)
    inventoryItem = QtCore.Signal(int, int)
    def __init__(self, queue, *args, **kwargs):
        queue.put((1, 'load'))
        self.queue = queue
        self.running = True
        super(SavegameThread, self).__init__(*args, **kwargs)
        # Setup Jinja templating
        self.env = Environment(loader=FileSystemLoader(frozen('data')))
        self.inv_types = OrderedDict([
            ('ARMO', self.tr("Armor")),
            ('WEAP', self.tr("Weapons")),
            ('ALCH', self.tr("Potions")),
            ('INGR', self.tr("Ingredients")),
            ('SCRL', self.tr("Scrolls")),
            ('MISC', self.tr("Miscellaneous")),
            ('BOOK', self.tr("Books")),
            ('AMMO', self.tr("Ammunition")),
            ('SLGM', self.tr("Soul gems")),
            ('KEYM', self.tr("Keys")),
            ('Other', self.tr("Other")),
        ])

    def __del__(self):
        self.wait()

    def run(self):
        while True:
            job = self.queue.get()
            prio, job, data = job[0], job[1], job[2:]
            print("SavegameThread job:", job)
            if job == 'stop':
                break
            else:
                self.newJob.emit(job, 0)
            if job == 'load':
                skyrimdata.loadData()
                self.newJob.emit("", 0)
            elif job == 'savegame':
                filename = data[0]
                self.newJob.emit("savegame", os.stat(filename).st_size)
                sg = savegame.Savegame(filename, load_now=False)
                for status in sg.loadGame():
                    self.jobStatus.emit(status)
                sg.populate_ids()
                html = self.dict2html(sg.d)
                self.sg = sg
                self.generalData.emit(html.encode("ascii", "xmlcharrefreplace"))
                for count, formid in sg.player_ingrs():
                    self.inventoryItem.emit(count, formid)
                self.newJob.emit("", 0)

    def stop(self):
        self.running = False
        self.queue.put((0, 'stop'))

    def dict2html(self, dic):
        template_filename = 'general_'+QtCore.QLocale().name()+'.html'
        buf = BytesIO()
        dic['screenshotImage'].save(buf, format="BMP")
        template = self.env.get_template(template_filename)
        inventory = {v: [] for v in self.inv_types.values()}
        inventory_weight = {v: 0 for v in self.inv_types.values()}
        for inv_item in dic['inventory']:
            # TODO: fix torch (MISC ID 0x0001D4EC)
            if inv_item.item.type not in {'C', 'F'} and inv_item.itemcount>0:
                item_ref = inv_item.item.name
                type_ = self.inv_types.get(inv_item.item.name.type,
                                           self.inv_types['Other'])
                inventory[type_].append((item_ref.FullName,
                                         item_ref.Value,
                                         item_ref.Weight,
                                         inv_item.itemcount))
                inventory_weight[type_] += item_ref.Weight * inv_item.itemcount
        for item_list in inventory.values():
            item_list.sort()
        total_weight = sum(inventory_weight.values())
        html = template.render(d=dic, screenshotData=
                               base64.b64encode(buf.getvalue()),
                               inventory=inventory,
                               inventory_weight=inventory_weight,
                               total_weight=total_weight)
        return html


#%% QTableView model
class IngrTable(QtCore.QAbstractTableModel):
    def __init__(self, ingrs=[], parent=None):
        super(IngrTable, self).__init__(parent)
        self.ingrs = ingrs
        self.layoutChanged.emit()
        self.headers = [self.tr("Name"),
                        self.tr("#"),
                        self.tr("Value"),
                        self.tr("Weight"),
                        self.tr("FormID")]

    def rowCount(self, parent):
        return len(self.ingrs)

    def columnCount(self, parent):
        return len(self.headers)

    def addItem(self, formid, count):
        self.layoutAboutToBeChanged.emit()
        ingr = db['INGR'][formid]
        self.ingrs.append((formid, ingr.FullName, count, ingr.Value, ingr.Weight,
                           "{:08X}".format(formid)))
        self.layoutChanged.emit()

    def data(self, index, role):
        if not index.isValid():
            return None
        elif role != QtCore.Qt.DisplayRole:
            return None
        return self.ingrs[index.row()][index.column() + 1]

    def headerData(self, col, orientation, role):
        if orientation == QtCore.Qt.Horizontal and role == QtCore.Qt.DisplayRole:
            return self.headers[col]
        if orientation == QtCore.Qt.Vertical and role == QtCore.Qt.DisplayRole:
            return col + 1
        return None

    def sort(self, Ncol, order):
        """Sort table by given column number.
        """
        self.layoutAboutToBeChanged.emit()
#        self.emit(SIGNAL("layoutAboutToBeChanged()"))
        self.ingrs = sorted(self.ingrs, key=operator.itemgetter(Ncol + 1))
        if order == QtCore.Qt.DescendingOrder:
            self.ingrs.reverse()
        self.layoutChanged.emit()
#        self.emit(SIGNAL("layoutChanged()"))

    def clear(self):
        self.layoutAboutToBeChanged.emit()
        self.ingrs = []
        self.layoutChanged.emit()


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
        logger = logging.getLogger()
        logging.basicConfig(level=logging.DEBUG,
                            format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
        logger.name = "<app_name>"
        self.logger = logger
        # Threading setup
        self.queue = PriorityQueue()
        self.thread = SavegameThread(self.queue, self)
#        self.thread.finished.connect(self.on_thread_finished)
        self.thread.newJob.connect(self.on_thread_newJob)
        self.thread.jobStatus.connect(self.on_thread_jobStatus)
        self.thread.generalData.connect(self.on_thread_generalData)
        self.thread.inventoryItem.connect(self.on_thread_inventoryItem)
        self.thread.start()
        savegames = savegame.getSaveGames()
        # Sort by last modified time first
        savegames = sorted(savegames,
                           key=lambda f: osp.getmtime(f),
                           reverse=True)
        if len(savegames):
            self.comboSavegames.addItem(self.tr("Select savegame"))
#            self.comboSavegames.setCurrentIndex(0)
        for f in savegames:
            self.comboSavegames.addItem(osp.basename(f), f)
#            self.open_savegame(savegames[0])
        # Setup Jinja templating
        self.env = Environment(loader=FileSystemLoader(frozen('data')))


    def initUI(self):
        ui_file = frozen(osp.join('data', 'wndmain.ui'))
        uic.loadUi(ui_file, self)
        # Load window geometry and state
        self.restoreGeometry(self.settings.value("geometry", ""))
        self.restoreState(self.settings.value("windowState", ""))
        # Status bar
        statusBar = self.statusBar()
        self.progressBar = QtWidgets.QProgressBar(statusBar)
        statusBar.addPermanentWidget(self.progressBar, 0)
        self.progressCancel = QtWidgets.QPushButton(statusBar)
        self.progressCancel.setText(self.tr("Cancel"))
        self.progressCancel.setEnabled(False)
        statusBar.addPermanentWidget(self.progressCancel, 0)
        self.tableIngrModel = IngrTable([], self.tableIngr)
        self.tableIngr.setModel(self.tableIngrModel)
        self.tableIngr.selectionModel().selectionChanged.connect(
            self.on_tableIngr_selectionChanged)
        self.show()

    ### Function overrides:
    def closeEvent(self, e):
        # Write window geometry and state to config file
        self.settings.setValue("geometry", self.saveGeometry())
        self.settings.setValue("windowState", self.saveState())
        e.accept()

    ### Qt slots
    @QtCore.Slot()
    def on_thread_finished(self):
        QtWidgets.QMessageBox.information(self,
                                          self.tr("Information"),
                                          self.tr("Thread finished."))

    @QtCore.Slot(int)
    def on_comboSavegames_currentIndexChanged(self, index):
        filename = self.comboSavegames.itemData(index)
        if filename is not None:
            self.open_savegame(filename)

    ### Core functionality
    def open_savegame(self, filename):
        self.queue.put((2, 'savegame', filename))

    @QtCore.Slot(str, int)
    def on_thread_newJob(self, job, maximum):
        if job == 'load':
            self.statusBar().showMessage(self.tr("Loading data..."))
            self.progressBar.setMaximum(0)
            self.progressBar.setMinimum(0)
            self.progressCancel.setEnabled(False)
        elif job == '':
            self.progressBar.setMaximum(1)
            self.progressCancel.setEnabled(False)
            self.statusBar().clearMessage()
        elif job == 'savegame':
            self.tableIngr.model().clear()
            self.statusBar().showMessage(self.tr("Loading savegame..."))
            self.progressBar.setMaximum(maximum)

    @QtCore.Slot(int)
    def on_thread_jobStatus(self, status):
        self.progressBar.setValue(status)

    @QtCore.Slot(str)
    def on_thread_generalData(self, html):
        self.textGeneral.setHtml(html)

    @QtCore.Slot(int, int)
    def on_thread_inventoryItem(self, count, formid):
        self.tableIngr.model().addItem(formid, count)

    @QtCore.Slot(QtCore.QItemSelection, QtCore.QItemSelection)
    def on_tableIngr_selectionChanged(self, selected, deselected):
        formid = self.tableIngrModel.ingrs[selected.indexes()[0].row()][0]
        ingr = skyrimdata.db['INGR'][formid]
        template_filename = 'ingr_'+QtCore.QLocale().name()+'.html'
        template = self.env.get_template(template_filename)
        val_weight = ingr.Value/ingr.Weight
        count = self.tableIngrModel.ingrs[selected.indexes()[0].row()][2]
        weight_count = ingr.Weight * count
        html = template.render(ingr=ingr, val_weight=val_weight, count=count,
                               weight_count=weight_count)
        self.textIngr.setHtml(html)


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
    if translator.load(frozen(osp.join("data", "main_{}.qm".format(lang)))):
        QtWidgets.qApp.installTranslator(translator)
    QtCore.QLocale().setDefault(QtCore.QLocale(lang))
    ### Create main window and run
    wnd = WndMain()
    if existing:
        self = wnd  # Makes it easier to debug with Spyder's F9 inside a class
    else:
        sys.exit(app.exec_())
