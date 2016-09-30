# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""

from __future__ import unicode_literals

import struct
from collections import OrderedDict
from cStringIO import StringIO
import os
import os.path as osp
import ctypes
import ctypes.wintypes

#%% unpack and data
from skyrimtypes import unpack, RefID
import skyrimdata
skyrimdata.loadData()


#%%
class Savegame(object):
    """This class loads a The Elder Scrolls V: Skyrim savegame file and parses
    useful information.
    """
    def __init__(self, filename):
        #%%
        d = OrderedDict()  # Data storage
        f = open(filename, 'rb')  # TODO: replace
        f.seek(0)
        if True:
#        with open(filename, 'rb') as f:
            # File
            d['magic'] = f.read(13)
            if d['magic'] != 'TESV_SAVEGAME':
                raise AssertionError("Incorrect magic in file header")
            d['headerSize'] = unpack("uint32", f)
            # Header
            header = StringIO(f.read(d['headerSize']))
            d['version'] = unpack("uint32", header)
            if not 7 <= d['version'] <= 9:
                raise AssertionError("Only versions 7 to 9 are supported")
            d['saveNumber'] = unpack("uint32", header)
            d['playerName'] = unpack("wstring", header)
            d['playerLevel'] = unpack("uint32", header)
            d['playerLocation'] = unpack("wstring", header)
            d['gameDate'] = unpack("wstring", header)
            d['playerRaceEditorId'] = unpack("wstring", header)
            d['playerSex'] = {0: "male", 1: "female"}[unpack("uint16", header)]
            d['playerCurExp'] = unpack("float32", header)
            d['playerLvlUpExp'] = unpack("float32", header)
            d['filetime'] = unpack("filetime", header)
            d['shotWidth'] = unpack("uint32", header)
            d['shotHeight'] = unpack("uint32", header)
            # Back to file
            d['screenshotData'] = f.read(3*d['shotWidth']*d['shotHeight'])
            from PIL import Image
            d['screenshotImage'] = Image.frombytes("RGB",
                                         (d['shotWidth'], d['shotHeight']),
                                         d['screenshotData'])
            d['formVersion'] = unpack("uint8", f)
            d['pluginInfoSize'] = unpack("uint32", f)
            # Plugin
            plugin = StringIO(f.read(d['pluginInfoSize']))
            d['pluginCount'] = unpack("uint8", plugin)
            d['plugins'] = [unpack("wstring", plugin)
                            for i in range(d['pluginCount'])]
            # File Location Table
            formIDArrayCountOffset = unpack("uint32", f)
            unknownTable3Offset = unpack("uint32", f)
            globalDataTable1Offset = unpack("uint32", f)
            globalDataTable2Offset = unpack("uint32", f)
            changeFormsOffset = unpack("uint32", f)
            globalDataTable3Offset = unpack("uint32", f)
            globalDataTable1Count = unpack("uint32", f)
            globalDataTable2Count = unpack("uint32", f)
            globalDataTable3Count = unpack("uint32", f)
            changeFormCount = unpack("uint32", f)
            f.read(4*15)  # unused
            # Global Data 1
            f.seek(globalDataTable1Offset)
            gdata1 = []
            for i in range(globalDataTable1Count):
                gdata1.append(unpack("globalData", f))
            # Global Data 2
            f.seek(globalDataTable2Offset)
            gdata2 = []
            for i in range(globalDataTable2Count):
                gdata2.append(unpack("globalData", f))
            # changeForms
            f.seek(changeFormsOffset)
            d['changeforms'] = [unpack("ChangeForm", f) for i in
                range(changeFormCount)]
            # Global Data 3
            f.seek(globalDataTable3Offset)
            gdata3 = []
            for i in range(globalDataTable3Count):
                gdata3.append(unpack("globalData", f))
            d['gdata'] = {v[1]:v[2] for v in (gdata1 + gdata2 + gdata3)}
            # formID
            f.seek(formIDArrayCountOffset)
            formIDArrayCount = unpack("uint32", f)
            d['formid'] = struct.Struct('{}I'.format(formIDArrayCount)).unpack(
                f.read(formIDArrayCount*4))
            # Visited Worldspace
            visitedWorldspaceArrayCount = unpack("uint32", f)
            d['visitedWorldspaceArray'] = struct.Struct('{}I'.format(
                visitedWorldspaceArrayCount)).unpack(f.read(
                visitedWorldspaceArrayCount*4))
            # unknownTable3
            f.seek(unknownTable3Offset)
            ukt3count = unpack("uint32", f)
            assert(len(f.read()) == ukt3count)
            # EOF
            assert(f.read() == "")
            # Inventory
            for cf in d['changeforms']:
                if cf.type == 1 and cf.formid.value == 0x14:
                    break
            d['inventory'] = cf.d['inventory']

            self.d = d

    def populate_ids(self):
        for k, created in self.d['gdata']['Created Objects'].items():
            for item in created:
#                print "Created", k, hex(item.refID.value)
                RefID.createdid[item.refID.value] = item
        for i, formid in enumerate(self.d['formid']):
            if formid in RefID.defaultid:
                RefID.formid[i+1] = RefID.defaultid[formid]
            elif formid in RefID.createdid:
                RefID.formid[i+1] = RefID.createdid[formid]


#%%
def getSaveGames():
    """Get list of savegame files"""
    dll = ctypes.windll.shell32
    buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH + 1)
    try:
        if dll.SHGetSpecialFolderPathW(None, buf, 0x0005, False):
            savedir = osp.join(buf.value, "My Games", "Skyrim", "Saves")
            if not osp.exists(savedir) or not osp.isdir(savedir):
                raise RuntimeError("Could not find savegame directory.")
        else:
            raise RuntimeError("Could not find savegame directory.")
    except:
        raise RuntimeError("Could not find savegame directory.")
    savegames = [osp.join(savedir, f) for f in os.listdir(savedir) if f.endswith(".ess")]
    return savegames


#%%
def test_savegame():
    #%%
    savegames = getSaveGames()
    for filename in savegames:
        sg = Savegame(filename)
        sg.populate_createdid()
