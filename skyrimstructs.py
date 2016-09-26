# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""

from __future__ import unicode_literals

from cStringIO import StringIO
import zlib


#%% unpack and data
from skyrimtypes import _types, unpack, RefID
from skyrimdata import db

#%% Stat
_stat_categories = {
    0: "General",
    1: "Quest",
    2: "Combat",
    3: "Magic",
    4: "Crafting",
    5: "Crime",
    6: "DLC Stats",
}

class Stat(object):
    def __init__(self, f):
        self.name = unpack("wstring", f)
        self.category = unpack("uint8", f)
        self.category_name = _stat_categories[self.category]
        self.value = unpack("uint32", f)

    def __repr__(self):
        return "Stat<{}({}):{} = {}>".format(self.category_name,
                                              self.category,
                                              self.name,
                                              self.value)


def read_miscStats(f):
    count = unpack("uint32", f)
    return [Stat(f) for i in range(count)]
_types["miscStat"] = read_miscStats


#%% Form ID
class FormID(object):
    def __init__(self, f):
        self.name = unpack("wstring", f)
        self.category = unpack("uint8", f)
        self.category_name = _stat_categories[self.category]
        self.value = unpack("uint32", f)

    def __repr__(self):
        return "FormID<>".format()


#def read_formIDs(f):
#    count = unpack("uint32", f)
#    return [Stat(f) for i in range(count)]
_types["FormID"] = FormID

#%% Created objects
class EnchInfo(object):
    def __init__(self, f):
        self.magnitude = unpack("float", f)
        self.duration = unpack("uint32", f)
        self.area = unpack("uint32", f)

    def __repr__(self):
        return "EnchInfo<mag={}, dur={}, area={}>".format(self.magnitude,
                                              self.duration,
                                              self.area)
_types["EnchInfo"] = EnchInfo

class MagicEffect(object):
    def __init__(self, f):
        self.refID = unpack("RefID", f)
        self.info = unpack("EnchInfo", f)
        self.price = unpack("float", f)

    def __repr__(self):
        return "MagicEffect<{}:{} = {}>".format(self.refID,
                                              self.info,
                                              self.price)
_types["MagicEffect"] = MagicEffect


class Enchantment(object):
    def __init__(self, f):
        self.refID = unpack("RefID", f)
        RefID.createdid[self.refID.value] = self
        self.timesUsed = unpack("uint32", f)
        count = unpack("vsval", f)
        self.effects = [unpack("MagicEffect", f) for i in range(count)]

    def __repr__(self):
        return "Enchantment<{} x{}: {}>".format(self.refID,
                                              self.timesUsed,
                                              self.effects)
_types["Enchantment"] = Enchantment

def read_CreatedObjects(f):
    weaponCount = unpack("vsval", f)
    weapons = [Enchantment(f) for i in range(weaponCount)]
    armourCount = unpack("vsval", f)
    armours = [Enchantment(f) for i in range(armourCount)]
    potionCount = unpack("vsval", f)
    potions = [Enchantment(f) for i in range(potionCount)]
#    from IPython import embed; embed()
    poisonCount = unpack("vsval", f)
    poisons = [Enchantment(f) for i in range(poisonCount)]
    return {"weapons": weapons, "armours": armours, "potions": potions,
            "poisons": poisons}
_types["CreatedObjects"] = read_CreatedObjects

#%% Ingredient Shared
def read_IngredientsShared(f):
    count = unpack("uint32", f)
    return [(unpack("RefID", f), unpack("RefID", f)) for i in range(count)]



#%% Global Data
_gdata_type_names = {
    0: ("Misc Stats", read_miscStats),
    1: ("Player Location", lambda f: "Not implemented"),
    2: ("TES", lambda f: "Not implemented"),
    3: ("Global Variables", lambda f: "Not implemented"),
    4: ("Created Objects", read_CreatedObjects),
    5: ("Effects", lambda f: "Not implemented"),
    6: ("Weather", lambda f: "Not implemented"),
    7: ("Audio", lambda f: "Not implemented"),
    8: ("SkyCells", lambda f: "Not implemented"),
    100: ("Process Lists", lambda f: "Not implemented"),
    101: ("Combat", lambda f: "Not implemented"),
    102: ("Interface", lambda f: "Not implemented"),
    103: ("Actor Causes", lambda f: "Not implemented"),
    104: ("Unknown 104", lambda f: "Not implemented"),
    105: ("Detection Manager", lambda f: "Not implemented"),
    106: ("Location MetaData", lambda f: "Not implemented"),
    107: ("Quest Static Data", lambda f: "Not implemented"),
    108: ("StoryTeller", lambda f: "Not implemented"),
    109: ("Magic Favorites", lambda f: "Not implemented"),
    110: ("PlayerControls", lambda f: "Not implemented"),
    111: ("Story Event Manager", lambda f: "Not implemented"),
    112: ("Ingredient Shared", read_IngredientsShared),
    113: ("MenuControls", lambda f: "Not implemented"),
    114: ("MenuTopicManager", lambda f: "Not implemented"),
    1000: ("Temp Effects", lambda f: "Not implemented"),
    1001: ("Papyrus", lambda f: "Not implemented"),
    1002: ("Anim Objects", lambda f: "Not implemented"),
    1003: ("Timer", lambda f: "Not implemented"),
    1004: ("Synchronized Animations", lambda f: "Not implemented"),
    1005: ("Main", lambda f: "Not implemented"),
}

def read_globalData(f):
    startpos = f.tell()
    type_ = unpack("uint32", f)
    type_name, type_decoder = _gdata_type_names[type_]
    length = unpack("uint32", f)
    print type_name, startpos, "->", f.tell()+length
    return (type_, type_name, type_decoder(StringIO(f.read(length))))
_types["globalData"] = read_globalData


#%% Change Form
#ingr = None
class ChangeForm(object):
    def __init__(self, f):
        self.formid = unpack("RefID", f)
        self.changeFlags = unpack("uint32", f)
        type_ = unpack("uint8", f)
        sizeFlag = {0: "uint8", 1: "uint16", 2: "uint32"}[type_ >> 6]
        self.type = type_ & 0b111111
        self.version = unpack("uint8", f)
        length1 = unpack(sizeFlag, f)
        length2 = unpack(sizeFlag, f)
        data = f.read(length1)
        if length2 != 0:
            data = zlib.decompress(data, 0, length2)
        self.data = data
#        if self.type == 16:  # INGR
#            ingr = unpack("INGR", data)
#            print ingr

    def __repr__(self):
        return "ChangeForm<{}>".format(self.formid)

_types["ChangeForm"] = ChangeForm


#%% Field
class Field(object):
    def __init__(self, f):
        self.type = f.read(4)
        size = unpack("uint16", f)
        self.data = f.read(size)

    def __repr__(self):
        return "Field<{}>".format(self.type)
_types["Field"] = Field

#%% Record
class Record(object):
    def __init__(self, fd, type_):
        self.type = type_
        dataSize = unpack("uint32", fd)
#        if type_ == "GRUP":
#            self.label = fd.read(4).decode("cp1252")
#            self.groupType = unpack("int32", fd)
#            self.stamp = unpack("uint16", fd)
#            unpack("uint16", fd)  # Unknown
#            self.version = unpack("uint16", fd)
#            unpack("uint16", fd)  # Unknown
##            children = []
##            group_end = fd.tell() + self.size - 24
##            while fd.tell() < group_end:
##                type_ = f.read(4).decode("cp1252")
##                children.append(Record(fd, type_))
##            self.children = children
##            self.data = fd.read(self.size - 24)
#            if self.label in _read_record_types:
#                data = StringIO(fd.read(self.size - 24))
#            else:  # skip
#                fd.seek(fd.tell() + self.size - 24)
#            return
        self.flags = unpack("uint32", fd)
        self.id = unpack("uint32", fd)
        self.revision = unpack("uint32", fd)
        self.version = unpack("uint16", fd)
        unpack("uint16", fd)  # Unknown
        if self.flags & 0x00040000:  # Data is compressed
            decompSize = unpack("uint32", fd)
            compData = fd.read(dataSize - 4)
            data = zlib.decompress(compData, 0, decompSize)
            dataSize = decompSize
        else:
            data = fd.read(dataSize)
        data = StringIO(data)
        fields = []
        while data.tell() < dataSize:
            fields.append(Field(data))
        self.fields = fields
    def __repr__(self):
        if self.type == "GRUP":
            return "{}:{}".format(self.type, self.label)
        return self.type


class Effect(object):
    def __init__(self, id_):
        self.EffectID = id_
        self.MGEF = db['MGEF'][id_]
        self.Magnitude = 0
        self.AreaOfEffect = 0
        self.Duration = 0

    def cost(self):
        try:
            return (db['MGEF'][self.EffectID].BaseCost *
                    (self.Magnitude * self.Duration / 10) ** 1.1)
        except:
            return -1

    def __repr__(self):
        return "Effect<{}, {} pts for {} sec>".format(self.MGEF.FullName,
            self.Magnitude, self.Duration)
_types["Effect"] = Effect


class INGR(Record):
    def __init__(self, fd, type_="INGR"):
        super(INGR, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Nameless"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.Value = unpack("uint32", field.data[:4])
                self.Weight = unpack("float", field.data[4:])
            elif field.type == "EFID":
                self.effects.append(Effect(unpack("formid", field.data)))
            elif field.type == "EFIT":
                last_effect = self.effects[-1]
                last_effect.Magnitude = unpack("float", field.data[:4])
                last_effect.AreaOfEffect = unpack("uint32", field.data[4:8])
                last_effect.Duration = unpack("uint32", field.data[8:])
        db['INGR'][self.id] = self

    def __repr__(self):
        return "INGR<{:08X}:{}>".format(self.id, self.FullName)

_types["INGR"] = INGR


class MGEF(Record):
    """Magic Effect.

    Data about magic effects from spells, enchantments and potions.

    Reference:
        http://en.m.uesp.net/wiki/Tes5Mod:Mod_File_Format/MGEF
    """
    def __init__(self, fd, type_="MGEF"):
        super(MGEF, self).__init__(fd, type_)
        self.FullName = "Nameless"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                fdata = StringIO(field.data)
                self.Flags = unpack("uint32", fdata)
                self.BaseCost = unpack("float", fdata)
                self.RelatedID = unpack("formid", fdata)
                self.Skill = unpack("int32", fdata)
                self.ResistanceAV = unpack("uint32", fdata)
                fdata.read(16)
                self.SkillLevel = unpack("uint32", fdata)
                self.Area = unpack("uint32", fdata)
                self.CastingTime = unpack("float", fdata)
                fdata.read(12)
                self.EffectType = unpack("uint32", fdata)
                self.PrimaryAV = unpack("int32", fdata)
            elif field.type == "ESCE":
                self.CounterEffects = unpack("formid", fdata)
            elif field.type == "DNAM":
                self.Description = unpack("lstring", fdata)
        db['MGEF'][self.id] = self

    def __repr__(self):
        return "MGEF<{:08X}:{}>".format(self.id, self.FullName)

_types["MGEF"] = MGEF


class Group(object):
    def __init__(self, fd, type_="GRUP"):
        self.type = type_
        self.size = unpack("uint32", fd)
        group_end = fd.tell() + self.size - 24
        self.label = fd.read(4).decode("cp1252")
        self.groupType = unpack("int32", fd)
        self.stamp = unpack("uint16", fd)
        unpack("uint16", fd)  # Unknown
        self.version = unpack("uint16", fd)
        unpack("uint16", fd)  # Unknown
        records = []
        if self.label in _read_record_types:  # Only read some groups
            while fd.tell() < group_end:
                type_ = fd.read(4).decode("cp1252")
#                data = StringIO(fd.read(self.size - 24))

                if type_ == "":  # EOF
                    break
                record = _read_record_types[type_](fd, type_)
                records.append(record)
            self.records = records
        else:  # skip uninteresting groups
            fd.seek(fd.tell() + self.size - 24)
    def __repr__(self):
        if self.type == "GRUP":
            return "{}:{}".format(self.type, self.label)
        return self.type

_read_record_types = {'INGR': INGR, 'GRUP': Group, 'MGEF': MGEF}
