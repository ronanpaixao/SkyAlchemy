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
        return "Enchantment<{:08x} x{}: {}>".format(self.refID.value,
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
_ChangeForm_flags = {
    "CHANGE_FORM_FLAGS": 0x01,
    "CHANGE_REFR_MOVE": 0x02,
    "CHANGE_REFR_HAVOK_MOVE": 0x04,
    "CHANGE_REFR_CELL_CHANGED": 0x08,
    "CHANGE_REFR_SCALE": 0x10,
    "CHANGE_REFR_INVENTORY": 0x20,
    "CHANGE_REFR_EXTRA_OWNERSHIP": 0x40,
    "CHANGE_REFR_BASEOBJECT": 0x80,
    "CHANGE_REFR_PROMOTED": 0x2000000,
    "CHANGE_REFR_EXTRA_ACTIVATING_CHILDREN": 0x4000000,
    "CHANGE_REFR_LEVELED_INVENTORY": 0x8000000,
    "CHANGE_REFR_ANIMATION": 0x10000000,
    "CHANGE_REFR_EXTRA_ENCOUNTER_ZONE": 0x20000000,
    "CHANGE_REFR_EXTRA_CREATED_ONLY": 0x40000000,
    "CHANGE_REFR_EXTRA_GAME_ONLY": 0x80000000,
    "CHANGE_OBJECT_EXTRA_ITEM_DATA": 0x400,
    "CHANGE_OBJECT_EXTRA_AMMO": 0x800,
    "CHANGE_OBJECT_EXTRA_LOCK": 0x1000,
    "CHANGE_DOOR_EXTRA_TELEPORT": 0x20000,
    "CHANGE_OBJECT_EMPTY": 0x200000,
    "CHANGE_OBJECT_OPEN_DEFAULT_STATE": 0x400000,
    "CHANGE_OBJECT_OPEN_STATE": 0x800000,
}

extra_data_flags = (_ChangeForm_flags['CHANGE_REFR_EXTRA_OWNERSHIP'] |
                    _ChangeForm_flags['CHANGE_OBJECT_EXTRA_LOCK'] |
                    _ChangeForm_flags['CHANGE_REFR_EXTRA_ENCOUNTER_ZONE'] |
                    _ChangeForm_flags['CHANGE_REFR_EXTRA_GAME_ONLY'] |
                    _ChangeForm_flags['CHANGE_OBJECT_EXTRA_AMMO'] |
                    _ChangeForm_flags['CHANGE_DOOR_EXTRA_TELEPORT'] |
                    _ChangeForm_flags['CHANGE_REFR_PROMOTED'] |
                    _ChangeForm_flags['CHANGE_REFR_EXTRA_ACTIVATING_CHILDREN'] |
                    _ChangeForm_flags['CHANGE_OBJECT_EXTRA_ITEM_DATA'])


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
        self.d = {}

        if self.type == 0:  # REFR
            sdata = StringIO(data)
            if self.formid.value >= 0xFF000000:
                initialType = 5  # No hits
            elif self.changeFlags & (_ChangeForm_flags['CHANGE_REFR_PROMOTED'] |
                                     _ChangeForm_flags['CHANGE_REFR_CELL_CHANGED']):
                initialType = 6
            elif self.changeFlags & (_ChangeForm_flags['CHANGE_REFR_HAVOK_MOVE'] |
                                     _ChangeForm_flags['CHANGE_REFR_MOVE']):
                initialType = 4  # No hits
            else:
                initialType = 0
            self.d['initialType'] = initialType
            if not (self.changeFlags & (_ChangeForm_flags['CHANGE_REFR_INVENTORY'] |
                                        _ChangeForm_flags['CHANGE_REFR_LEVELED_INVENTORY'])):
                return  # TODO: not really interested right now
            sdata.read({5: 31, 6: 34, 4: 27, 0:0}[initialType])
            if self.changeFlags & _ChangeForm_flags['CHANGE_REFR_HAVOK_MOVE']:
                hmcount = unpack("vsval", sdata)
                self.d['hmcount'] = hmcount
                self.d['hmdata'] = sdata.read(hmcount)
            if self.changeFlags & _ChangeForm_flags['CHANGE_FORM_FLAGS']:
                self.d['flag'] = unpack("uint32", sdata)
                self.d['flagdata'] = unpack("uint16", sdata)
            if self.changeFlags & _ChangeForm_flags['CHANGE_REFR_BASEOBJECT']:
                self.d['baseobject'] = unpack("RefID", sdata)
            if self.changeFlags & _ChangeForm_flags['CHANGE_REFR_SCALE']:
                self.d['scale'] = unpack("float", sdata)
            if self.changeFlags & (_ChangeForm_flags['CHANGE_REFR_INVENTORY'] |
                                 _ChangeForm_flags['CHANGE_REFR_LEVELED_INVENTORY']):
                if self.changeFlags & extra_data_flags:
                    self.d['extraData'] = unpack("ExtraData", sdata)
                invcount = unpack("vsval", sdata)
    #            cf.items = [unpack("InventoryItem", sdata) for i in range(invcount)]
                self.d['inventory'] = []
                for i in range(invcount):
                    self.d['inventory'].append(unpack("InventoryItem", sdata))
            # Skip Animation
            # Skip Explosion

        elif self.type == 16:  # INGR
            self.d['ingr_data'] = unpack("uint32", data)

        elif self.type == 1 and self.formid.value == 0x14:  # Player ACHR
            sdata = StringIO(data)
            sdata.seek(829)
            itemcount = unpack("vsval", sdata)
#            inventory = []
            #for i in range(itemcount):
            #    print(i, hex(sdata.tell()))
            #    inventory.append(unpack("InventoryItem", sdata))

            self.d['inventory'] = [unpack("InventoryItem", sdata) for i in range(itemcount)]

    def __repr__(self):
        return "ChangeForm<{}>".format(self.formid)

_types["ChangeForm"] = ChangeForm



#%% Inventory
_dataTypeNames = {
    22: "Worn",
    23: "WornLeft",
    24: "PackageStartLocation",
    25: "Package",
    26: "TresPassPackage",
    27: "RunOncePacks",
    28: "ReferenceHandle",
    29: "unknown29",
    30: "LevCreaModifier",
    31: "Ghost",
    33: "Ownership",
    34: "Global",
    35: "Rank",
    36: "Count",
    37: "Health",
    39: "TimeLeft",
    40: "Charge",
    42: "Lock",
    43: "Teleport",
    44: "MapMarker",
    45: "LeveledCreature",
    46: "LeveledItem",
    47: "Scale",
    49: "NonActorMagicCaster",
    50: "NonActorMagicTarget",
    52: "PlayerCrimeList",
    56: "ItemDropper",
    61: "CannotWear",
    62: "ExtraPoison",
    68: "FriendHits",
    69: "HeadingTarget",
    72: "StartingWorldOrCell",
    73: "Hotkey",
    76: "InfoGeneralTopic",
    77: "HasNoRumors",
    79: "TerminalState",
    83: "unknown83",
    84: "CanTalkToPlayer",
    85: "ObjectHealth",
    88: "ModelSwap",
    89: "Radius",
    91: "FactionChanges",
    92: "DismemberedLimbs",
    93: "ActorCause",
    101: "CombatStyle",
    104: "OpenCloseActivateRef",
    106: "Ammo",
    108: "PackageData",
    111: "SayTopicInfoOnceADay",
    112: "EncounterZone",
    113: "SayToTopicInfo",
    120: "GuardedRefData",
    133: "AshPileRef",
    135: "FollowerSwimBreadcrumbs",
    136: "AliasInstanceArray",
    140: "PromotedRef",
    142: "OutfitItem",
    146: "SceneData",
    149: "FromAlias",
    150: "ShouldWear",
    152: "AttachedArrows3D",
    153: "TextDisplayData",
    155: "Enchantment",
    156: "Soul",
    157: "ForcedTarget",
    159: "UniqueID",
    160: "Flags",
    161: "RefrPath",
    164: "ForcedLandingMarker",
    169: "Interaction",
    174: "GroupConstraint",
    175: "ScriptedAnimDependence",
    176: "CachedScale",
}


class MagicTarget(object):
    def __init__(self, f):
        self.ref = unpack("RefID", f)
        unpack("uint8", f)
        unpack("vsval", f)
        count = unpack("RefID", f)
        self.data = [unpack("uint8", f) for i in range(count)]
    def __repr__(self):
        return "MagicTarget<{}>".format()

_types["MagicTarget"] = MagicTarget


class MagicCaster(object):
    def __init__(self, f):
        unpack("uint32", f)
        self.dataref = unpack("RefID", f)
        unpack("uint32", f)
        unpack("uint32", f)
        self.dataref2 = unpack("RefID", f)
        unpack("float", f)
        self.ref = unpack("RefID", f)
        self.ref2 = unpack("RefID", f)
    def __repr__(self):
        return "MagicCaster<{}>".format()
_types["MagicCaster"] = MagicCaster


class ExtraDataType(object):
    def __init__(self, f):
        type_ = unpack("uint8", f)
        self.type = type_
        self.typeName = _dataTypeNames[type_]
        if type_ == 22:
            pass
        elif type_ == 23:
            pass
        elif type_ == 24:
            self.data = [unpack("RefID", f), unpack("RefID", f),
                         unpack("uint32", f), f.read(3)]
        elif type_ == 25:
            self.data = [unpack("RefID", f), unpack("RefID", f),
                         unpack("uint32", f), unpack("uint8", f),
                         unpack("uint8", f), unpack("uint8", f)]
        elif type_ == 26:
            self.data = [unpack("RefID", f)]
            if self.data[0].value != 0:
                raise NotImplementedError("There's more unknown data")
        elif type_ == 27:
            count = unpack("vsval", f)
            self.data = [(unpack("RefID", f), unpack("uint8", f)) for i in range(count)]
        elif type_ == 28:
            self.data = [unpack("RefID", f)]
        elif type_ == 30:
            self.data = [unpack("uint32", f)]
        elif type_ == 31:
            self.data = [unpack("uint8", f)]
        elif type_ == 32:
            self.data = [unpack("RefID", f)]
        elif type_ == 33:
            self.data = [unpack("RefID", f)]
        elif type_ == 34:
            self.data = [unpack("RefID", f)]
        elif type_ == 35:
            self.data = [unpack("RefID", f)]
        elif type_ == 36:
            self.data = [unpack("uint16", f)]
        elif type_ == 37:
            self.data = [unpack("float", f)]
        elif type_ == 39:
            self.data = [unpack("uint32", f)]
        elif type_ == 40:
            self.data = [unpack("float", f)]
        elif type_ == 42:
            self.data = [unpack("uint8", f), unpack("uint8", f),
                         unpack("RefID", f), unpack("uint32", f),
                         unpack("uint32", f)]
        elif type_ == 43:
            self.data = [unpack("float", f) for i in range(6)]
            self.data.extend([unpack("uint8", f), unpack("RefID", f)])
        elif type_ == 44:
            self.data = [unpack("uint8", f)]
        elif type_ == 45:
            raise NotImplementedError("Too big for now")  # TODO: fix
        elif type_ == 46:
            self.data = [unpack("uint32", f), unpack("uint8", f)]
        elif type_ == 47:
            self.data = [unpack("float", f)]
        elif type_ == 49:
            self.data = [unpack("MagicCaster", f)]
        elif type_ == 50:
            self.data = [unpack("RefID", f)]
            count = unpack("vsval", f)
            self.data.extend([unpack("MagicTarget", f) for i in range(count)])
        elif type_ == 52:
            count = unpack("vsval", f)
            self.data = [(unpack("uint32", f), unpack("uint32", f)) for i in
                         range(count)]
        elif type_ == 56:
            self.data = [unpack("RefID", f)]
        elif type_ == 62:
            self.data = [unpack("RefID", f), unpack("uint32", f)]
        elif type_ == 68:
            count = unpack("vsval", f)
            self.data = [unpack("float", f) for i in range(count)]
        elif type_ == 69:
            self.data = [unpack("RefID", f)]
        elif type_ == 72:
            self.data = [unpack("RefID", f)]
        elif type_ == 73:
            self.data = [unpack("uint8", f)]
        elif type_ == 76:
            self.data = [unpack("wstring", f)]
            self.data.extend([unpack("uint8", f) for i in range(5)])
            self.data.extend([unpack("RefID", f) for i in range(4)])
        elif type_ == 77:
            self.data = [unpack("uint8", f)]
        elif type_ == 79:
            self.data = [unpack("uint8", f), unpack("uint8", f)]
        elif type_ == 83:
            self.data = [unpack("uint32", f)]
        elif type_ == 84:
            self.data = [unpack("uint8", f)]
        elif type_ == 85:
            self.data = [unpack("float", f)]
        elif type_ == 88:
            self.data = [unpack("RefID", f), unpack("uint32", f)]
        elif type_ == 89:
            self.data = [unpack("uint32", f)]
        elif type_ == 91:
            count = unpack("vsval", f)
            self.data = [(unpack("RefID", f), unpack("int8", f)) for i in range(count)]
            self.data.append(unpack("RefID", f))
            self.data.append(unpack("int8", f))
        elif type_ == 92:
            raise NotImplementedError("Too big for now")  # TODO: fix
        elif type_ == 93:
            self.data = [unpack("uint32", f)]
        elif type_ == 101:
            self.data = [unpack("RefID", f)]
        elif type_ == 104:
            self.data = [unpack("RefID", f)]
        elif type_ == 106:
            self.data = [unpack("RefID", f), unpack("uint32", f)]
        elif type_ == 108:
            self.data = [unpack("uint8", f)]
            if self.data != -1:
                raise NotImplementedError("There's more unknown data")
        elif type_ == 111:
            count = unpack("vsval", f)
            self.data = [(unpack("RefID", f), unpack("uint32", f),
                          unpack("uint32", f)) for i in range(count)]
        elif type_ == 112:
            self.data = [unpack("RefID", f)]
        elif type_ == 113:
            raise NotImplementedError("Too big for now")  # TODO: fix
        elif type_ == 120:
            count = unpack("vsval", f)
            self.data = [(unpack("RefID", f), unpack("uint32", f),
                          unpack("uint8", f)) for i in range(count)]
        elif type_ == 133:
            self.data = [unpack("RefID", f)]
        elif type_ == 135:
            self.data = [unpack("float", f), unpack("float", f),
                         unpack("float", f), unpack("RefID", f),
                         unpack("uint32", f)]
            count = unpack("vsval", f)
            self.data.extend([(unpack("float", f), unpack("float", f),
                               unpack("float", f), unpack("RefID", f),
                               unpack("float", f), unpack("float", f),
                               unpack("float", f), unpack("RefID", f),
                               unpack("uint8", f)) for i in range(count)])
        elif type_ == 136:
            count = unpack("vsval", f)
            self.data = [(unpack("RefID", f), unpack("uint32", f)) for i in range(count)]
        elif type_ == 140:
            count = unpack("vsval", f)
            self.data = [unpack("RefID", f) for i in range(count)]
        elif type_ == 142:
            self.data = [unpack("RefID", f)]
        elif type_ == 146:
            self.data = [unpack("RefID", f)]
        elif type_ == 149:
            self.data = [unpack("RefID", f), unpack("uint32", f)]
        elif type_ == 150:
            self.data = [unpack("uint8", f)]
        elif type_ == 152:
            raise NotImplementedError("Too big for now")  # TODO: fix
        elif type_ == 153:
            self.data = [unpack("RefID", f), unpack("RefID", f),
                         unpack("int32", f)]
            if (self.data[2] == -2 and self.data[0].value == 0 and
                self.data[1].value == 0):
                    self.data.append(unpack("wstring", f))
        elif type_ == 155:
            self.data = [unpack("RefID", f), unpack("uint16", f)]
        elif type_ == 156:
            self.data = [unpack("uint8", f)]
        elif type_ == 157:
            self.data = [unpack("RefID", f)]
        elif type_ == 159:
            self.data = [unpack("uint32", f), unpack("uint16", f)]
        elif type_ == 160:
            self.data = [unpack("uint32", f)]
        elif type_ == 161:
            self.data = [unpack("float", f) for i in range(3*6)]
            self.data.extend([unpack("uint32", f) for i in range(4)])
        elif type_ == 164:
            self.data = [unpack("RefID", f)]
        elif type_ == 169:
            self.data = [unpack("uint32", f), unpack("RefID", f),
                         unpack("RefID", f), unpack("uint8", f)]
        elif type_ == 174:
            raise NotImplementedError("Too big for now")  # TODO: fix
        elif type_ == 175:
            self.data = [unpack("RefID", f)]
        elif type_ == 176:
            self.data = [unpack("RefID", f)]
        else:
            raise RuntimeError("Shouldn't get here! ExtraDataType = %d" % type_)
#        self.changeFlags = unpack("uint32", f)

    def __repr__(self):
        return "ExtraDataType<{}:{}>".format(self.type, self.typeName)

_types["ExtraDataType"] = ExtraDataType


class ExtraData(object):
    def __init__(self, f):
        self.count = unpack("vsval", f)
        self.data = [unpack("ExtraDataType", f) for i in range(self.count)]

    def __repr__(self):
        return "ExtraData<>".format()

_types["ExtraData"] = ExtraData


class InventoryItem(object):
    def __init__(self, f):
        self.item = unpack("RefID", f)
        self.itemcount = unpack("int32", f)
        extracount = unpack("vsval", f)
        self.extraData = [unpack("ExtraData", f) for i in range(extracount)]
#        print "Position", f.tell()

    def __repr__(self):
        return "InventoryItem<{}x {}>".format(self.itemcount,
                                              self.item)

_types["InventoryItem"] = InventoryItem


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
        self.FullName = "Unnamed"
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


class ALCH(Record):
    def __init__(self, fd, type_="ALCH"):
        super(ALCH, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.Weight = unpack("float", field.data)
            elif field.type == "ENIT":
                self.Value = unpack("uint32", field.data[:4])
                flags = unpack("uint32", field.data[4:8])
                flag_bits = {0x1: "ManualCalc", 0x2: "Food",
                             0x10000: "Medicine", 0x20000: "Poison"}
                self.Flags = [v for k, v in flag_bits.items() if k & flags]
            elif field.type == "EFID":
                self.effects.append(Effect(unpack("formid", field.data)))
            elif field.type == "EFIT":
                last_effect = self.effects[-1]
                last_effect.Magnitude = unpack("float", field.data[:4])
                last_effect.AreaOfEffect = unpack("uint32", field.data[4:8])
                last_effect.Duration = unpack("uint32", field.data[8:])
        db['ALCH'][self.id] = self

    def __repr__(self):
        return "ALCH<{:08X}:{}>".format(self.id, self.FullName)

_types["ALCH"] = ALCH



class EnchantedItem(object):
    def __init__(self, f):
        self.cost = unpack("uint32", f)
        flags = unpack("uint32", f)
        flag_bits = {0x1: "ManualCalc", 0x4: "ExtendDurationOnRecast"}
        self.flags = [v for k, v in flag_bits.items() if k & flags]
        self.CastType = {0x00: "Constant Effect", 0x01: "Fire and Forget",
                         0x02: "Concentration"}[unpack("uint32", f)]
        self.enchAmount = unpack("uint32", f)
        self.delivery = {0x00: "Self", 0x01: "Touch", 0x02: "Aimed",
                         0x03: "Target Actor", 0x04: "Target Location"
                         }[unpack("uint32", f)]
        self.EnchantType = {0x06: "Enchantment", 0x0C: "Staff Enchantment"
                         }[unpack("uint32", f)]
        self.ChargeTime = unpack("float", f)
        self.BaseEnchantment = unpack("formid", f)

    def __repr__(self):
        return "EnchantedItem<>".format()

_types["EnchantedItem"] = EnchantedItem


class ENCH(Record):
    def __init__(self, fd, type_="ENCH"):
        super(ENCH, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "ENIT":
                self.ArmorRating = unpack("EnchantedItem", StringIO(field.data))
            elif field.type == "EFID":
                self.effects.append(Effect(unpack("formid", field.data)))
            elif field.type == "EFIT":
                last_effect = self.effects[-1]
                last_effect.Magnitude = unpack("float", field.data[:4])
                last_effect.AreaOfEffect = unpack("uint32", field.data[4:8])
                last_effect.Duration = unpack("uint32", field.data[8:])
        db['ENCH'][self.id] = self

    @property
    def cost(self):
        return sum([ef.cost for ef in self.effects])

    def __repr__(self):
        return "ENCH<{:08X}:{}>".format(self.id, self.FullName)

_types["ENCH"] = ENCH


class ARMO(Record):
    def __init__(self, fd, type_="ARMO"):
        super(ARMO, self).__init__(fd, type_)
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "EITM":
                self.enchantment = unpack("formid", field.data)
            elif field.type == "EAMT":
                self.enchantment_amount = unpack("uint16", field.data)
            elif field.type == "DESC":
                self.enchantment_amount = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.BaseValue = unpack("uint32", field.data[:4])
                self.Weight = unpack("float", field.data[4:])
            elif field.type == "DNAM":
                self.ArmorRating = unpack("uint32", field.data)
        db['ARMO'][self.id] = self

    @property
    def cost(self):
        return self.BaseValue + (self.enchantment.cost + 0.5)

    def __repr__(self):
        return "ARMO<{:08X}:{}>".format(self.id, self.FullName)

_types["ARMO"] = ARMO


class MISC(Record):
    def __init__(self, fd, type_="MISC"):
        super(MISC, self).__init__(fd, type_)
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.cost = unpack("uint32", field.data[:4])
                self.Weight = unpack("float", field.data[4:])
        db['MISC'][self.id] = self

    def __repr__(self):
        return "MISC<{:08X}:{}>".format(self.id, self.FullName)

_types["MISC"] = MISC


class SCRL(Record):
    def __init__(self, fd, type_="SCRL"):
        super(SCRL, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DESC":
                self.Description = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.cost = unpack("uint32", field.data[:4])
                self.Weight = unpack("float", field.data[4:])
            elif field.type == "EFID":
                self.effects.append(Effect(unpack("formid", field.data)))
            elif field.type == "EFIT":
                last_effect = self.effects[-1]
                last_effect.Magnitude = unpack("float", field.data[:4])
                last_effect.AreaOfEffect = unpack("uint32", field.data[4:8])
                last_effect.Duration = unpack("uint32", field.data[8:])
        db['SCRL'][self.id] = self

    def __repr__(self):
        return "SCRL<{:08X}:{}>".format(self.id, self.FullName)

_types["SCRL"] = SCRL


class BOOK(Record):
    def __init__(self, fd, type_="BOOK"):
        super(BOOK, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DESC":
                self.Description = unpack("lstring", field.data)
            elif field.type == "CNAM":
                self.Description2 = unpack("lstring", field.data)
            elif field.type == "DATA":
                sdata = StringIO(field.data)
                flags = unpack("uint8", sdata)
                flag_bits = {0x1: "Teaches Skill", 0x2: "Can't be Taken",
                             0x4: "Teaches Spell", 0x8: "Read"}
                self.flags = [v for k, v in flag_bits.items() if k & flags]
                self.type = {0: "Book/Tome", 255: "Note/Scroll"
                             }[unpack("uint8", sdata)]
                unpack("uint8", sdata)  # Always 0
                self.teaches = unpack("uint32", sdata)
                self.cost = unpack("uint32", sdata)
                self.Weight = unpack("float", sdata)
        db['BOOK'][self.id] = self

    def __repr__(self):
        return "BOOK<{:08X}:{}>".format(self.id, self.FullName)

_types["BOOK"] = BOOK


class WEAP(Record):
    def __init__(self, fd, type_="WEAP"):
        super(WEAP, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DESC":
                self.Description = unpack("lstring", field.data)
            elif field.type == "CNAM":
                self.cnam = unpack("formid", field.data)
            elif field.type == "DATA":
                sdata = StringIO(field.data)
                self.cost = unpack("uint32", sdata)
                self.Weight = unpack("float", sdata)
                self.damage = unpack("uint16", sdata)
            elif field.type == "EAMT":
                self.enchantment_charge = unpack("uint16", field.data)
            elif field.type == "EITM":
                self.enchantment = unpack("formid", field.data)
            # TODO: include DNAM field?

        db['WEAP'][self.id] = self

    def __repr__(self):
        return "WEAP<{:08X}:{}>".format(self.id, self.FullName)

_types["WEAP"] = WEAP


class AMMO(Record):
    def __init__(self, fd, type_="AMMO"):
        super(AMMO, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DESC":
                self.Description = unpack("lstring", field.data)
            elif field.type == "CNAM":
                self.cnam = unpack("formid", field.data)
            elif field.type == "DATA":
                sdata = StringIO(field.data)
                self.projID = unpack("formid", sdata)
                flags = unpack("uint32", sdata)
                flag_bits = {0x1: "Ignores Normal Weapon Resistance",
                             0x2: "Non-Playable",
                             0x4: "Non-Bolt"}
                self.flags = [v for k, v in flag_bits.items() if k & flags]
                self.damage = unpack("float", sdata)
                self.cost = unpack("uint32", sdata)
            elif field.type == "EAMT":
                self.enchantment_charge = unpack("uint16", field.data)
            elif field.type == "EITM":
                self.enchantment = unpack("formid", field.data)
            # TODO: include DNAM field?

        db['AMMO'][self.id] = self

    def __repr__(self):
        return "AMMO<{:08X}:{}>".format(self.id, self.FullName)

_types["AMMO"] = AMMO


class SLGM(Record):
    def __init__(self, fd, type_="SLGM"):
        super(SLGM, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "SOUL":
                self.soul = {0: "Empty", 1: "Petty", 2: "Lesser", 3: "Common",
                             4: "Greater", 5: "Grand"
                             }[unpack("uint8", field.data)]
            elif field.type == "DATA":
                self.cost = unpack("uint32", field.data[:4])
                self.weight = unpack("float", field.data[4:])
            elif field.type == "SLCP":
                self.capacity = {0: "Empty", 1: "Petty", 2: "Lesser",
                                 3: "Common", 4: "Greater", 5: "Grand"
                                }[unpack("uint8", field.data)]

        db['SLGM'][self.id] = self

    def __repr__(self):
        return "SLGM<{:08X}:{}:{}>".format(self.id, self.FullName,
                                           self.capacity)

_types["SLGM"] = SLGM


class KEYM(Record):
    def __init__(self, fd, type_="KEYM"):
        super(KEYM, self).__init__(fd, type_)
        self.effects = []
        self.FullName = "Unnamed"
        for field in self.fields:
            if field.type == "EDID":
                self.EditorID = unpack("zstring", field.data)
            elif field.type == "FULL":
                self.FullName = unpack("lstring", field.data)
            elif field.type == "DATA":
                self.cost = unpack("uint32", field.data[:4])
                self.weight = unpack("float", field.data[4:])

        db['KEYM'][self.id] = self

    def __repr__(self):
        return "KEYM<{:08X}:{}>".format(self.id, self.FullName)

_types["KEYM"] = KEYM


#%% Group
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

_read_record_types = {'INGR': INGR, 'GRUP': Group, 'MGEF': MGEF, 'ALCH': ALCH,
                      'ENCH': ENCH, 'ARMO': ARMO, 'MISC': MISC, 'SCRL': SCRL,
                      'BOOK': BOOK, 'WEAP': WEAP, 'AMMO': AMMO, 'SLGM': SLGM,
                      'KEYM': KEYM}
