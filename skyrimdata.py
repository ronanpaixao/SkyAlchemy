# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""

from __future__ import unicode_literals, division, print_function

import sys
import os
import os.path as osp
import re
import pickle
from io import BytesIO


#%% Data records to store
# from skyrimstructs._read_record_types.keys()
db_types = ['MGEF', 'INGR', 'ALCH', 'ARMO', 'ENCH', 'MISC', 'SCRL', 'BOOK',
            'WEAP', 'AMMO', 'SLGM', 'KEYM', 'KYWD']
# Only load once
#if 'db' not in locals():
#    print("db not in locals!")
db = {k: {} for k in db_types}
#else:
#    print("db in locals!")
#if 'lstrings' not in locals():
lstrings = {}

from skyrimtypes import unpack, RefID

#%% Fast printing to stdout
if "print" not in locals():
    __orig_print = print
    def print(*args, **kwargs):
        kwargs['file'] = sys.stdout
        __orig_print(*args, **kwargs)

#%% Find Skyrim folder
def getSteamLibraryFolders():
    with open(r"C:\Program Files (x86)\Steam\SteamApps\libraryfolders.vdf") as f:
        folders = [r"C:\Program Files (x86)\Steam"]
        lf = f.read()
        folders.extend([fn.replace("\\\\", "\\") for fn in
            re.findall('^\s*"\d*"\s*"([^"]*)"', lf, re.MULTILINE)])
    return folders

def getSkyrimFolder(folders):
    for folder in folders:
        folderpath = osp.join(folder, "SteamApps")
        if osp.exists(folderpath) and osp.exists(osp.join(folder, "SteamApps", "common")):
            if "Skyrim" in os.listdir(osp.join(folder, "SteamApps", "common")):
                return osp.join(folder, "SteamApps", "common", "Skyrim")


#%% Strings
def strdir(f):
    return (unpack("uint32", f), unpack("uint32", f))

def extract_strings(filename):
    """Extract strings from string table

    Based on data from:
    http://en.m.uesp.net/wiki/Tes5Mod:String_Table_File_Format
    """
    f = open(filename, 'rb')
    str_count = unpack("uint32", f)
    dataSize = unpack("uint32", f)
    strings = {}
    strings_dir = []
    for i in range(str_count):
        print("Reading directory: {}/{} = {:0.2f}".format(
            i, str_count, i/str_count*100))
        strings_dir.append(strdir(f))

    data = BytesIO(f.read(dataSize))
    f.close()
    if filename.lower().endswith(".strings"):
        for i, (id_, offset) in enumerate(strings_dir):
            print("Reading string: {}/{} = {:0.2f}".format(
                i, str_count, i/str_count*100))
            data.seek(offset)
            strings[id_] = unpack("zstring", data)
#    else:  # .dlstrings, .ilstrings
#        for i, (id_, offset) in enumerate(strings_dir):
#            print("Reading string: {}/{} = {:0.2f}".format(
#                i, str_count, i/str_count*100))
#            data.seek(offset + 4)  # ignore lenght
#            strings[id_] = unpack("zstring", data)
    return strings


__lstrings_file = osp.join("data", "lstrings.pkl")
__data_file = osp.join("data", "data.pkl")
def loadData():
    """load data from data files.

    This should be only done once per program, for performance.
    """
    if (not osp.exists(__data_file)) or (not osp.exists(__lstrings_file)):
        extractData()
        
    with open(__data_file, 'rb') as f:
        db.update(pickle.load(f))
    with open(__lstrings_file, 'rb') as f:
        lstrings.update(pickle.load(f))

    for k, v in db.items():
        RefID.defaultid.update(v)
#    db['unKYWD'] = {}
#    for k, v in db['KYWD'].items():
#        db['unKYWD'][v.EditorID] = k


def extractData():
    folders = getSteamLibraryFolders()
    folder = getSkyrimFolder(folders)
    if folder is None:
        raise RuntimeError("Could not find Skyrim folder")

    #%% Lstrings (localized strings)
    # Only supports English localization
    if osp.exists(__lstrings_file):
        print("lstrings file already exists. Skipping extraction. Delete {} "
              "to extract again.")
        if len(lstrings) == 0:
            with open(__lstrings_file, 'rb') as f:
                lstrings.update(pickle.load(f))

    else:
        strings_files = os.listdir(osp.join(folder, 'Data', 'Strings'))
        for strings_filename in strings_files:
            print("Extracting lstrings from {}".format(osp.basename(
                  strings_filename)))
            lstrings.update(extract_strings(osp.join(folder, "Data", "Strings",
                                                     strings_filename)))
        with open(__lstrings_file, 'wb') as f:
            pickle.dump(lstrings, f)

    #%% ***.esm data files

    data_filenames = [osp.join(folder, "Data", fn)
                      for fn in os.listdir(osp.join(folder, "Data"))
                      if fn.endswith('.esm')]
    from skyrimstructs import Group, Record, db
    if osp.exists(__data_file):
        print("Data is already extracted. Skipping.")
    else:
        for data_filename in data_filenames:
            print("Extracting data from {}".format(osp.basename(data_filename)))
            f = open(data_filename, 'rb')
            f.seek(0)
            records = []
            i = 0
            while True:
                type_ = f.read(4).decode("cp1252")
            #    if i == 10:
            #        break
                if type_ == "":  # EOF
                    break
                if type_ == "GRUP":
                    record = Group(f)
                else:
                    record = Record(f, type_)
                records.append(record)
                print(i, record, f.tell())
                sys.stdout.flush()
                i += 1

            f.close()

        #%% Save data
        with open(__data_file, 'wb') as f:
            pickle.dump(db, f)

#%% Execution
if __name__ == "__main__":
    extractData()
        #%%
#        print(records[27].records[0])
#        print(db['INGR'][0x001016B3].effects)
