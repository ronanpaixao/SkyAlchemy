# -*- coding: utf-8 -*-
"""
SkyAlchemy
Copyright ©2016 Ronan Paixão
Licensed under the terms of the MIT License.

See LICENSE for details.

@author: Ronan Paixão
"""


from __future__ import unicode_literals, division, print_function

import math
import copy
from itertools import combinations


#%% Utility functions
def alchemistPerk(perks=[]):
    if 0xc07cd in perks:
        return 100
    elif 0xc07cc in perks:
        return 80
    elif 0xc07cb in perks:
        return 60
    elif 0xc07ca in perks:
        return 40
    elif 0xbe127 in perks:
        return 20
    return 0


def physicianPerk(mgef, perks=[]):
    physPerk = 0x58215 in perks
    kwda = set(mgef.KWDA)
    if physPerk and not kwda.isdisjoint([0x42503, 0x42508, 0x42503]):
        return 25
    return 0


def benefactorPerk(mgef, making, perks=[]):
    beneficial = 0xF8A4E
    benefactor_perk = 0x58216 in perks
    kwda = set(mgef.KWDA)
    if benefactor_perk and making=="potion" and beneficial in kwda:
        return 25
    return 0


def poisonerPerk(mgef, making, perks=[]):
    harmful = 0x42509
    poisoner_perk = 0x58217 in perks
    kwda = set(mgef.KWDA)
    if poisoner_perk and making=="poison" and harmful in kwda:
        return 25
    return 0


def powerFactor(mgef, making, alch_skill, fortify_alch=0, perks=[]):
    fAlchemyIngredientInitMult  = 4.
    ingredientMult = fAlchemyIngredientInitMult
    fAlchemySkillFactor = 1.5
    skillFactor = fAlchemySkillFactor
    return (ingredientMult * (1 + (skillFactor - 1) * alch_skill / 100) *
            (1 + fortify_alch / 100) * (1 + alchemistPerk(perks) / 100) *
            (1 + physicianPerk(mgef, perks) / 100) *
            (1 + benefactorPerk(mgef, making, perks) / 100 +
             poisonerPerk(mgef, making, perks) / 100))


#%% Alchemy classes
class Recipe(object):
    """Represents a recipe (combination of ingredients)."""
    def __init__(self, alch_skill, fortify_alch=0, perks=[], ingrs=[]):
        try:
            ingrs.remove(None)
        except ValueError:
            pass
        ingrs.sort(key=lambda x: x.Value, reverse=True)
        self.ingrs = ingrs
        effects = {}
        for ingr in ingrs:
            for ef in ingr.effects:
                effects.setdefault(ef.MGEF.FullName, [ef, 0])[1]+=1
        effects = {k: v for k,v in effects.items() if v[1] > 1}
        effect_order = sorted([ef[0] for ef in effects.values()],
                              key=lambda x: x.Value,
                              reverse=True)
        if 0 < len(effect_order) >= len(ingrs) - 1:
            self.valid = True
        else:
            self.valid = False
            self.Name = "Invalid recipe"
            return
        self.Name = "{} of {}".format(effect_order[0].MGEF.alch_type.capitalize(),
                                      effect_order[0].MGEF.FullName)
        effect_order = copy.deepcopy(effect_order)
        valuesum = 0.
        making = effect_order[0].MGEF.alch_type
        del_effect = []
        for effect in effect_order:
            if 0x5821d in perks and effect.MGEF.alch_type != making:
                del_effect.append(effect)
                continue  # skip if Purity perk
            mgef = effect.MGEF
            pf = powerFactor(mgef, making, alch_skill, fortify_alch, perks)
            mag = round(effect.Magnitude * (pf if mgef.MGEFflags.b.PowerAffectsMagnitude else 1))
            dur = round(effect.Duration * (pf if mgef.MGEFflags.b.PowerAffectsDuration else 1))
            magfact = mag if mag > 0 else 1
            durfact = dur/10 if dur > 0 else 1
            value = math.floor(mgef.BaseCost * (magfact*durfact)**1.1)
            valuesum += value
            effect.Magnitude = mag
            effect.Duration = dur

        for effect in del_effect:
            effect_order.remove(effect)

        self.Value = valuesum
        self.effects = effect_order

    def __repr__(self):
        return "Recipe<{}>".format(self.Name)


#%%
class RecipeFactory(object):
    def __init__(self, ingrs=[]):
        self.ingrs = ingrs

    @property
    def ingrs(self):
        return self._ingrs

    @ingrs.setter
    def ingrs(self, ingrs):
        ingrs.sort(key=lambda x: x.Value, reverse=True)
        self._ingrs = ingrs

    def calcRecipesIter(self, alch_skill, fortify_alch=0, perks=[], calc2=True, calc3=True):
        if calc2 and calc3:
            ingrs = copy.copy(self._ingrs)
            ingrs.append(None)
            calc_n = 3
        elif calc2 and not calc3:
            ingrs = self._ingrs
            calc_n = 2
        elif not calc2 and calc3:
            ingrs = self._ingrs
            calc_n = 3
        else:
            raise ValueError("One of calc2 or calc3 must be True")
        for ingr_comb in combinations(ingrs, calc_n):
            recipe = Recipe(alch_skill, fortify_alch, perks, list(ingr_comb))
            yield recipe

    def calcRecipes(self, alch_skill, fortify_alch=0, perks=[], calc2=True, calc3=True):
        recipes = []
        for recipe in self.calcRecipesIter(alch_skill, fortify_alch, perks,
                                           calc2, calc3):
            if recipe.valid:
                recipes.append(recipe)
        recipes.sort(key=lambda x: x.Value, reverse=True)
        self.recipes = recipes
        return recipes

#%% Tests
def test_alchemy():
    import skyrimdata
    skyrimdata.loadData()
    for ingr_id, ingr in skyrimdata.db['INGR'].items():
        if ingr.FullName == "Briar Heart":
            bh = ingr
        elif ingr.FullName == "Imp Stool":
            imp = ingr
        elif ingr.FullName == "Slaughterfish Scales":
            ss = ingr
        elif ingr.FullName == "Red Mountain Flower":
            red = ingr
        elif ingr.FullName == "Blue Mountain Flower":
            blue = ingr
        elif ingr.FullName == "Frost Salts":
            frost = ingr
        elif ingr.FullName == "Fire Salts":
            fire = ingr
        elif ingr.FullName == "Bear Claws":
            bear = ingr
        elif ingr.FullName == "Rock Warbler Egg":
            rock = ingr

    # Poison of Paralysis
    pp = Recipe(49, ingrs=[bh, imp, ss])
    assert pp.valid == True
    assert pp.Name == "Poison of Paralysis"
    assert pp.Value == 348.0
    assert [e.Value for e in pp.effects] == [233.0, 70.0, 45.0]
    assert len(pp.effects) == 3
    assert [e.Description for e in pp.effects]

    # Potion of Restore Magicka
    perks60 = [0xc07cb, 0x58215, 0x58216, 0x58217, 0x5821d]
    prm = Recipe(100, ingrs=[frost, fire, None], perks=perks60)
    assert prm.valid == True
    assert prm.Name == "Potion of Restore Magicka"
    assert prm.Value == 69.0
    assert [e.Value for e in prm.effects] == [69.0]
    assert len(prm.effects) == 1
    assert [e.Description for e in prm.effects]

    # Poison of Damage Magicka Regen
    pdmr = Recipe(100, ingrs=[bear, blue, rock], perks=perks60)
    assert pdmr.valid == True
    assert pdmr.Name == "Poison of Damage Magicka Regen"
    assert pdmr.Value == 568
    assert [e.Value for e in pdmr.effects] == [568.0]
    assert len(pdmr.effects) == 1
    assert [e.Description for e in pdmr.effects] == [
        "Decrease the target's Magicka regeneration by 100.0% for 60.0 seconds."]


    # Invalid recipes
    ir = Recipe(100)
    assert ir.valid == False

    ir = Recipe(100, ingrs=[red, blue])
    assert ir.valid == False

    # Recipe factory
    rf = RecipeFactory([bh, imp, ss])
    rf.calcRecipes(49)
    assert rf.ingrs == [bh, ss, imp]
    assert len(rf.recipes) == 4
    assert [r.Value for r in rf.recipes] == [348.0, 233.0, 70.0, 45.0]
    assert [r.Name for r in rf.recipes] == ['Poison of Paralysis',
                                            'Poison of Paralysis',
                                            'Poison of Lingering Damage Health',
                                            'Potion of Fortify Block']

    rf = RecipeFactory([frost, fire])
    rf.calcRecipes(100, perks=perks60)
    assert rf.ingrs == [frost, fire]
    assert len(rf.recipes) == 1
    assert [r.Value for r in rf.recipes] == [69.0]
    assert [r.Name for r in rf.recipes] == ['Potion of Restore Magicka']
    for recipe in rf.calcRecipesIter(100, perks=perks60):
        assert recipe.ingrs == [frost, fire]
        assert recipe.Value == 69.0
        assert recipe.Name == 'Potion of Restore Magicka'

    rf = RecipeFactory([bear, blue, rock])
    rf.calcRecipes(100, perks=perks60)
    assert rf.ingrs == [bear, blue, rock]
    assert len(rf.recipes) == 4
    assert [r.Value for r in rf.recipes] == [568, 568, 253, 57]
    assert [r.Name for r in rf.recipes] == ['Poison of Damage Magicka Regen',
                                            'Poison of Damage Magicka Regen',
                                            'Potion of Fortify One-handed',
                                            'Potion of Restore Health']
