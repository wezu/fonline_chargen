'''
Copyright (c) 2017-2018, wezu (wezu.dev@gmail.com)

Permission to use, copy, modify, and/or distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES
OF MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE
FOR ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR
ANY DAMAGES WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS,
WHETHER IN AN ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION,
ARISING OUT OF OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
'''
from __future__ import print_function
import sys
if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins
import math
import random
import string
import datetime
import os
import copy
from contextlib import contextmanager

#this is the template string for formating the info in the 'stats' frame
stat_template='''
Armor Class:     {ac:>3}    Hit Points:    {max_hp:>3}   Crit. Power/CC:{crit_power:>3}/{crit_power_cc:>3}  Bonus Damage:   {bonus_dmg:>2}%   HEX for 95% vs AC50 (eye aim):
Action Points:   {ap:>3}    HP/Level:      {hp_per_level:>3}   Critical Res.:     {crit_res:>3}  Bonus Fire Dmg.:{bonus_fire_dmg:>2}%     SG:             {sg_range:>4}({sg_range_aim:>3})
Carry Weight:    {carry_weight:>3}    Skill Points:  {sp:>3}   Crit. Res. Head:   {crit_res_head:>3}  Target DR:       {target_dr:>2}     SG long range:  {sg_longrange:>4}({sg_longrange_aim:>3})
Melee Damage:    {melee:>3}    SP/Level:      {sp_per_level:>3}   Normal DT/DR:   {normal_dt}/{normal_dr:>3}%  Bonus XP:       {bonus_xp:>2}%     BG:             {bg_range:>4}({bg_range_aim:>3})
Poison Res.:     {poision_res:>3}    Party Points:  {pp:>3}   Laser DT/DR:    {laser_dt}/{laser_dr:>3}%  Drug time:     {drug_duration:>3}%     BG long range:  {bg_longrange:>4}({bg_longrange_aim:>3})
Radiation Res.:  {radiation_res:>3}    Total Perks:   {max_perks:>3}   Fire DT/DR:     {fire_dt}/{fire_dr:>3}%  Drug heal:     {drug_heal:>3}%     EW:             {ew_range:>4}({ew_range_aim:>3})
Healing Rate:    {healing_rate:>3}    Unused Perks:  {free_perks:>3}   Plasma DT/DR:   {plasma_dt}/{plasma_dr:>3}%  FA healed:     ~{fa_healed:>3}     EW long range:  {ew_longrange:>4}({ew_longrange_aim:>3})
Crit. Chance:    {crit_chance:>3}    Sight: {sight_a}/{sight_b}/{sight_c}/{sight_d:>2}   Explode DT/DR:  {explode_dt}/{explode_dr:>3}%  FA cooldown:    {fa_cooldown:>3}     Throwing:       {tw_range:>4}({tw_range_aim:>3})
CC. Crit. Chance:{crit_chance_cc:>3}    Level:         {lvl:>3}   Electric DT/DR: {electrical_dt}/{electrical_dr:>3}%  Doc cooldown:   {doc_cooldown:>3}
'''
#this is the template string for formating the info in the 'target' frame
target_template='''Armor Class:  30
                DT:        DR:
NORMAL:       {normal_dt:>2}          {normal_dr:>2}
LASER:        {laser_dt:>2}          {laser_dr:>2}
FIRE:         {fire_dt:>2}          {fire_dr:>2}
PLASMA:       {plasma_dt:>2}          {plasma_dr:>2}
EXPLODE:      {explode_dt:>2}          {explode_dr:>2}
ELECTRIC:     {electric_dt:>2}          {electric_dr:>2}
       CRITICAL RESISTANCE:
POWER:       {crit_pow:>2}
CHANCE:      {crit_c:>2}
ENDURANCE:   {e:>2}
LUCK:        {l:>2}
STRENGTH:    {s:>2}
'''


class Stats():
    '''
    This calss handels calculating all Fonline stats
    '''
    def __init__(self):
        #create some data structures used later
        self.memory=[]
        self.bonuses={}
        self.perks={}
        self.traits={}
        self.skills={}
        self.last_level_skills={}
        self.tags={}
        #fill in some data structures
        self.current_gun=None
        self.level=1
        self.aim_mode='UNAIMED'
        self.special={'s':5,'p':5,'e':5,'c':5,'i':5,'a':5,'l':5,'none':5}
        self.target_stats={ 'ac':0, 'normal_dr':0, 'normal_dt':0, 'laser_dr':0,
                            'laser_dt': 0, 'fire_dr':0, 'fire_dt':0,
                            'plasma_dr':0, 'plasma_dt': 0, 'explode_dr': 0,
                            'explode_dt': 0, 'electric_dr':0, 'electric_dt':0,
                            'crit_c':0  ,'crit_pow':0, 'l':5, 's':5, 'e':5, None:0}
        #bonus for aim modes critical chance and also to-hit penalty
        self.aim_bonus={'EYE':60,
                        'HEAD':40,
                        'TORSO':0,
                        'GROIN':30,
                        'HANDS':30,
                        'LEGS':20,
                        'UNAIMED':0,
                        'BURST':0}
        self.derived={'max_hp':0,'hp_per_level':0, 'sp':0, 'sp_per_level':0,'pp':0,
                     'max_perks':8, 'free_perks':0, 'sight':0, 'sequence':0,'lvl':0,
                     'ac':0, 'ap':0, 'carry_weight':0, 'melee':0, 'poision_res':0,
                     'radiation_res':0, 'healing_rate':0, 'crit_chance':0}
        #some traits change SPECIAL, they are listed here
        self.trait_special={'Bruiser':{'s':4},'Bonehead':{'i':-1}}
        #maximum level of skills
        self.skill_limits={'Small Guns':300,'Big Guns':300,'Energy Guns':300,
                          'Close Combat':300,'Throwing':300,'First Aid':200,
                          'Doctor':200,'Lockpick':150,'Repair':125,'Science':125,
                          'Outdoorsman':175,'Scavenging':0,'Sneak':270,'Steal':150,
                          'Traps':150,'Speech':300,'Gambling':150,'Barter':150}
        #requirements for perks:
        # perk_point -1 or 0, if 0 then the perk is a 'free' support perk
        # level - minimum character level to buy perk
        # skill - dictionary of minimum required skill levels to buy perk
        # min_special - dictionary of minimum required special to buy perk (empty dict for no requirements)
        # max_special- dictionary of maximum special to buy perk (empty dict for no requirements)
        # perks - list of perk names required to buy this perk
        self.perk_req={
                    'More Critical':{'perk_point':1, 'level':3, 'skill':{'Small Guns':100,'Big Guns':100,'Energy Guns':100,'Close Combat':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Quick Pockets':{'perk_point':1, 'level':3, 'skill':{}, 'min_special':{'a':5}, 'max_special':{}, 'perks':[]},
                    'Adrenaline Rush':{'perk_point':1, 'level':3, 'skill':{}, 'min_special':{'s':5}, 'max_special':{}, 'perks':[]},
                    'Quick Recovery':{'perk_point':1, 'level':3, 'skill':{}, 'min_special':{'s':6}, 'max_special':{}, 'perks':[]},
                    'Weapon Handling':{'perk_point':1, 'level':3, 'skill':{'Small Guns':100,'Big Guns':100,'Energy Guns':100,'Close Combat':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'In Your Face!':{'perk_point':1, 'level':6, 'skill':{'Close Combat':125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Even More Criticals':{'perk_point':1, 'level':6, 'skill':{'Small Guns':125,'Big Guns':125,'Energy Guns':125,'Close Combat':125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Silent Running':{'perk_point':1, 'level':6, 'skill':{'Sneak':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Toughness':{'perk_point':1, 'level':6, 'skill':{}, 'min_special':{'e':4}, 'max_special':{}, 'perks':[]},
                    'Sharpshooter':{'perk_point':1, 'level':9, 'skill':{'Small Guns':150,'Big Guns':150,'Energy Guns':150,'Close Combat':150}, 'min_special':{'i':3}, 'max_special':{}, 'perks':[]},
                    'Pyromaniac':{'perk_point':1, 'level':9, 'skill':{'Small Guns':100,'Big Guns':100,'Energy Guns':100,'Close Combat':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Close Combat Master':{'perk_point':1, 'level':9, 'skill':{'Close Combat':150}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Even Tougher':{'perk_point':1, 'level':9, 'skill':{}, 'min_special':{'e':6}, 'max_special':{}, 'perks':[]},
                    'Stonewall':{'perk_point':1, 'level':9, 'skill':{}, 'min_special':{'s':6}, 'max_special':{}, 'perks':[]},
                    'Medic':{'perk_point':1, 'level':9, 'skill':{'Doctor':125, 'First Aid':125}, 'min_special':{'i':3}, 'max_special':{}, 'perks':[]},
                    'Heave Ho!':{'perk_point':1, 'level':9, 'skill':{'Throwing':125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Bonus Ranged Dmg.':{'perk_point':1, 'level':9, 'skill':{'Small Guns':150,'Big Guns':150,'Energy Guns':150}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Lifegiver 1':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Gain ST':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'s':9}, 'perks':[]},
                    'Gain PE':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'p':9}, 'perks':[]},
                    'Gain EN':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'e':9}, 'perks':[]},
                    'Gain CH':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'c':9}, 'perks':[]},
                    'Gain IN':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'i':9}, 'perks':[]},
                    'Gain AG':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'a':9}, 'perks':[]},
                    'Gain LK':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{}, 'max_special':{'l':9}, 'perks':[]},
                    'Better Critical':{'perk_point':1, 'level':12, 'skill':{'Small Guns':175,'Big Guns':175,'Energy Guns':175,'Close Combat':175}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Ghost':{'perk_point':1, 'level':12, 'skill':{'Sneak':150}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Action Boy 1':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{'a':6}, 'max_special':{}, 'perks':[]},
                    'Action Boy 2':{'perk_point':1, 'level':12, 'skill':{}, 'min_special':{'a':6}, 'max_special':{}, 'perks':[]},
                    'Lifegiver 2':{'perk_point':1, 'level':15, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Dodger 1':{'perk_point':1, 'level':15, 'skill':{'Close Combat':150 }, 'min_special':{'a':8}, 'max_special':{}, 'perks':[]},
                    'Dodger 2':{'perk_point':1, 'level':18, 'skill':{'Close Combat':175 }, 'min_special':{'a':10}, 'max_special':{}, 'perks':['Dodger 1']},
                    'Livewire':{'perk_point':1, 'level':15, 'skill':{}, 'min_special':{'a':6}, 'max_special':{}, 'perks':[]},
                    'Man of Steel':{'perk_point':15, 'level':3, 'skill':{}, 'min_special':{'e':8}, 'max_special':{}, 'perks':[]},
                    'Field Medic':{'perk_point':1, 'level':15, 'skill':{'Doctor':175, 'First Aid':175}, 'min_special':{}, 'max_special':{}, 'perks':['Medic']},
                    'Iron Limbs':{'perk_point':1, 'level':15, 'skill':{}, 'min_special':{'s':6, 'e':6}, 'max_special':{}, 'perks':[]},
                    'Silent Death':{'perk_point':1, 'level':15, 'skill':{'Sneak':175}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'More Ranged Dmg.':{'perk_point':1, 'level':15, 'skill':{'Small Guns':200,'Big Guns':200,'Energy Guns':200}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Lifegiver 3':{'perk_point':1, 'level':18, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Bonus Rate of Attack':{'perk_point':1, 'level':18, 'skill':{'Small Guns':180,'Big Guns':180,'Energy Guns':180,'Close Combat':180}, 'min_special':{}, 'max_special':{}, 'perks':[]},

                    'Boneyard Guard SG':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Boneyard Guard BG':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Boneyard Guard EW':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Boneyard Guard CC':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Boneyard Guard THW':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Cautious Nature':{'perk_point':0, 'level':2, 'skill':{'Outdoorsman':100}, 'min_special':{'p':6}, 'max_special':{}, 'perks':[]},
                    'Dead Man Walking':{'perk_point':0, 'level':2, 'skill':{'Doctor':50}, 'min_special':{'i':5}, 'max_special':{}, 'perks':[]},
                    'Demolition Expert':{'perk_point':0, 'level':2, 'skill':{'Traps':125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Dismantler':{'perk_point':0, 'level':2, 'skill':{'Science':120}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Educated':{'perk_point':0, 'level':2, 'skill':{'Science':100}, 'min_special':{'i':8}, 'max_special':{}, 'perks':[]},
                    'Explorer':{'perk_point':0, 'level':2, 'skill':{'Outdoorsman':150}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Faster Healing':{'perk_point':0, 'level':2, 'skill':{'Doctor':75}, 'min_special':{'i':6}, 'max_special':{}, 'perks':[]},
                    'Gecko Skinning':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Harmless':{'perk_point':0, 'level':2, 'skill':{'Steal':125}, 'min_special':{'c':6}, 'max_special':{}, 'perks':[]},
                    'Light Step':{'perk_point':0, 'level':2, 'skill':{'Traps': 100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Magnetic Personality':{'perk_point':0, 'level':2, 'skill':{'Speech':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Master Thief':{'perk_point':0, 'level':2, 'skill':{'Steal':125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Mr. Fixit':{'perk_point':0, 'level':2, 'skill':{'Repair':120}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Negotiator':{'perk_point':0, 'level':2, 'skill':{'Barter': 125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Pack Rat':{'perk_point':0, 'level':3, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Pathfinder':{'perk_point':0, 'level':2, 'skill':{'Outdoorsman':150}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Pickpocket':{'perk_point':0, 'level':2, 'skill':{'Steal': 125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Rad Resistance':{'perk_point':0, 'level':2, 'skill':{'Doctor':100}, 'min_special':{'i':7}, 'max_special':{}, 'perks':[]},
                    'Ranger':{'perk_point':0, 'level':2, 'skill':{'Outdoorsman':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Scout':{'perk_point':0, 'level':2, 'skill':{'Outdoorsman':150}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Sex Appeal':{'perk_point':0, 'level':2, 'skill':{'Speech':75}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Snakeater':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{'e':6}, 'max_special':{}, 'perks':[]},
                    'Speaker':{'perk_point':0, 'level':2, 'skill':{'Speech': 125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Stealth Girl':{'perk_point':0, 'level':2, 'skill':{'Sneak':100, 'Repair':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Strong Back':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{'e':6}, 'max_special':{}, 'perks':[]},
                    'Swift Learner':{'perk_point':0, 'level':2, 'skill':{'Science':50}, 'min_special':{'i':6}, 'max_special':{}, 'perks':[]},
                    'Thief':{'perk_point':0, 'level':2, 'skill':{'Steal':100}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Treasure Hunter':{'perk_point':0, 'level':2, 'skill':{'Lockpick':125}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Repair x10':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'First Aid x10':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Small Guns x10':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Outdoorsman x10':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Barter x10':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]},
                    'Science x10':{'perk_point':0, 'level':2, 'skill':{}, 'min_special':{}, 'max_special':{}, 'perks':[]}
                    }

        #some perks give skill bonus, this dict tell how much and of what skill
        #the values are in 'skill points' not raw points
        self.perk_skill_bonus={'Repair x10':{'Repair':60},
                               'First Aid x10':{'First Aid':60},
                               'Small Guns x10':{'Small Guns':60},
                               'Outdoorsman x10':{'Outdoorsman':60},
                               'Barter x10':{'Barter':60},
                               'Science x10':{'Science':60},
                               'Boneyard Guard SG':{'Small Guns':10},
                               'Boneyard Guard BG':{'Big Guns':10},
                               'Boneyard Guard CC':{'Close Combat':10},
                               'Boneyard Guard THW':{'Throwing':10},
                               'Boneyard Guard EW':{'Energy Guns':10}}
        #some perks give special bonuses,this dict tell how much
        self.perk_special_bonus={'Gain ST':{'s':2},
                                'Gain PE':{'p':2},
                                'Gain EN':{'e':2},
                                'Gain CH':{'c':2},
                                'Gain IN':{'i':2},
                                'Gain AG':{'a':2},
                                'Gain LK':{'l':2}}
        #known guns (or other weapons)
        #min_dmg and max_dmg - damage dealt by gun
        #max_range - maximum gun range
        #min_burst - minimum number of bullets hitting a target when using burst mode, or 0 if gun can't burst
        #max_burst - maximum number of bullets hitting a target when using burst mode, or 0 if gun can't burst
        #skill - name of the skill used by this gun
        #ammo_dr - ammunition DR modifier (should be negative)
        #ammo_ac- ammunition AC modifier
        #ammo_dmg - ammunition DM modifier (or damage adjustment), should be float if !=1 (eg. 1.5 not 3/2 unless running py3+)
        #min_st - minimum strength required by gun
        #ap - action points needed to fire (in single mode)
        #dmg_type - type of damage dealt by weapon ('normal','laser','fire', 'plasma','explode','electric')
        #hands - number of hands needed to use gun
        #perks - list of perks the gun(and ammo!) has
        self.guns={
                   '.223 Pistol':{'min_dmg':30, 'max_dmg':40, 'max_range':30, 'min_burst':0, 'max_burst':0,
                           'skill':'Small Guns', 'ammo_dr':-30, 'ammo_ac':-20, 'ammo_dmg':1,'min_st':5, 'ap':4,
                           'dmg_type':'normal','hands':1, 'perks':{'Penetrate'}},
                   'Assault Rifle':{'min_dmg':25, 'max_dmg':35, 'max_range':50, 'min_burst':4, 'max_burst':6,
                           'skill':'Small Guns', 'ammo_dr':-35, 'ammo_ac':0, 'ammo_dmg':0.667,'min_st':5, 'ap':5,
                           'dmg_type':'normal','hands':2, 'perks':{'Long Range','Penetrate'}},
                   'Sniper Rifle':{'min_dmg':20, 'max_dmg':40, 'max_range':50, 'min_burst':0, 'max_burst':0,
                           'skill':'Small Guns', 'ammo_dr':-30, 'ammo_ac':-20, 'ammo_dmg':1,'min_st':5, 'ap':5,
                           'dmg_type':'normal','hands':2, 'perks':{'Long Range'}},
                   'Needler Pistol':{'min_dmg':15, 'max_dmg':30, 'max_range':24, 'min_burst':0, 'max_burst':0,
                           'skill':'Small Guns', 'ammo_dr':0, 'ammo_ac':-35, 'ammo_dmg':1.5,'min_st':3, 'ap':4,
                           'dmg_type':'normal','hands':1, 'perks':{'Penetrate'}},
                   'H&K CAWS':{'min_dmg':22, 'max_dmg':30, 'max_range':25, 'min_burst':5, 'max_burst':5,
                           'skill':'Small Guns', 'ammo_dr':-25, 'ammo_ac':-10, 'ammo_dmg':1,'min_st':6, 'ap':5,
                           'dmg_type':'normal','hands':2, 'perks':{'Penetrate','Knockback'}},
                   'H&K P90c':{'min_dmg':15, 'max_dmg':25, 'max_range':30, 'min_burst':5, 'max_burst':7,
                           'skill':'Small Guns', 'ammo_dr':-35, 'ammo_ac':0, 'ammo_dmg':0.8571,'min_st':4, 'ap':4,
                           'dmg_type':'normal','hands':1, 'perks':{'Penetrate'}},
                   'FN FAL':{'min_dmg':22, 'max_dmg':33, 'max_range':35, 'min_burst':10, 'max_burst':10,
                           'skill':'Small Guns', 'ammo_dr':-10, 'ammo_ac':-5, 'ammo_dmg':1.2,'min_st':5, 'ap':5,
                           'dmg_type':'normal','hands':2, 'perks':{'Fast Reload'}},
                   'M79':{'min_dmg':50, 'max_dmg':90, 'max_range':25, 'min_burst':0, 'max_burst':0,
                           'skill':'Small Guns', 'ammo_dr':-15, 'ammo_ac':0, 'ammo_dmg':1,'min_st':5, 'ap':6,
                           'dmg_type':'explode','hands':2, 'perks':{}},
                   'Avenger':{'min_dmg':12, 'max_dmg':15, 'max_range':35, 'min_burst':14, 'max_burst':20,
                           'skill':'Big Guns',  'ammo_dr':-35, 'ammo_ac':0, 'ammo_dmg':0.667,'min_st':7, 'ap':7,
                           'dmg_type':'normal','hands':2, 'perks':{'Accurate','Penetrate'}},
                   'Incinerator':{'min_dmg':100, 'max_dmg':125, 'max_range':10, 'min_burst':0, 'max_burst':0,
                           'skill':'Big Guns', 'ammo_dr':0, 'ammo_ac':-20, 'ammo_dmg':1,'min_st':7, 'ap':7,
                           'dmg_type':'fire','hands':1, 'perks':{}},
                   'Rocket Launcher':{'min_dmg':40, 'max_dmg':100, 'max_range':40, 'min_burst':0, 'max_burst':0,
                           'skill':'Big Guns', 'ammo_dr':-25, 'ammo_ac':-15, 'ammo_dmg':1,'min_st':7, 'ap':7,
                           'dmg_type':'explode','hands':1, 'perks':{'Long Range','Penetrate'}},
                   'LSW':{'min_dmg':22, 'max_dmg':37, 'max_range':45, 'min_burst':5, 'max_burst':5,
                           'skill':'Big Guns',  'ammo_dr':-30, 'ammo_ac':-20, 'ammo_dmg':1, 'min_st':6, 'ap':5,
                           'dmg_type':'normal','hands':1, 'perks':{'Long Range'}},
                   'Laser Rifle':{'min_dmg':50, 'max_dmg':60, 'max_range':47, 'min_burst':0, 'max_burst':0,
                           'skill':'Energy Guns', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':6, 'ap':5,
                           'dmg_type':'laser','hands':2, 'perks':{'Long Range'}},
                   'Plasma Pistol':{'min_dmg':30, 'max_dmg':45, 'max_range':32, 'min_burst':0, 'max_burst':0,
                           'skill':'Energy Guns', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':4,
                           'dmg_type':'plasma','hands':1, 'perks':{}},
                   'Plasma Rifle':{'min_dmg':30, 'max_dmg':45, 'max_range':32, 'min_burst':0, 'max_burst':0,
                           'skill':'Energy Guns', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':4,
                           'dmg_type':'plasma','hands':2, 'perks':{'Long Range'}},
                   'Gatling Laser':{'min_dmg':64, 'max_dmg':84, 'max_range':40, 'min_burst':4, 'max_burst':6,
                           'skill':'Energy Guns', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':7, 'ap':7,
                           'dmg_type':'laser','hands':2, 'perks':{'Long Range'}},
                   'Pulse Pistol':{'min_dmg':35, 'max_dmg':50, 'max_range':30, 'min_burst':0, 'max_burst':0,
                           'skill':'Energy Guns', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':3, 'ap':4,
                           'dmg_type':'electric','hands':1, 'perks':{'Penetrate'}},
                   'Mega Power Fist':{'min_dmg':21, 'max_dmg':41, 'max_range':1, 'min_burst':0, 'max_burst':0,
                           'skill':'Close Combat', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':1, 'ap':3,
                           'dmg_type':'electric','hands':1, 'perks':{'Penetrate'}},
                   'Wakizashi Blade':{'min_dmg':15, 'max_dmg':27, 'max_range':1, 'min_burst':0, 'max_burst':0,
                           'skill':'Close Combat', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':2, 'ap':4,
                           'dmg_type':'normal','hands':1, 'perks':{'Penetrate'}},
                   'Super Sledge':{'min_dmg':36, 'max_dmg':72, 'max_range':2, 'min_burst':0, 'max_burst':0,
                           'skill':'Close Combat', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':5, 'ap':4,
                           'dmg_type':'normal','hands':2, 'perks':{'Knockback'}},
                   'Super Cattle Prod':{'min_dmg':40, 'max_dmg':62, 'max_range':1, 'min_burst':0, 'max_burst':0,
                           'skill':'Close Combat', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':3,
                           'dmg_type':'electric','hands':1, 'perks':{'Accurate'}},
                   'Louisville Slugger':{'min_dmg':24, 'max_dmg':60, 'max_range':1, 'min_burst':0, 'max_burst':0,
                           'skill':'Close Combat', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':4,
                           'dmg_type':'normal','hands':1, 'perks':{'Knockback','Knockout'}},
                   'Ripper':{'min_dmg':16, 'max_dmg':33, 'max_range':1, 'min_burst':0, 'max_burst':0,
                           'skill':'Close Combat', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':3,
                           'dmg_type':'normal','hands':1, 'perks':{'Penetrate'}},
                   'Frag Grenade':{'min_dmg':35, 'max_dmg':60, 'max_range':15, 'min_burst':0, 'max_burst':0,
                           'skill':'Throwing', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':3, 'ap':5,
                           'dmg_type':'explode','hands':1, 'perks':{}},
                   'Plasma Grenade':{'min_dmg':60, 'max_dmg':120, 'max_range':15, 'min_burst':0, 'max_burst':0,
                           'skill':'Throwing', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':4,
                           'dmg_type':'plasma','hands':1, 'perks':{}},
                   'Fire Grenade':{'min_dmg':40, 'max_dmg':80, 'max_range':15, 'min_burst':0, 'max_burst':0,
                           'skill':'Throwing', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':4, 'ap':4,
                           'dmg_type':'fire','hands':1, 'perks':{}},
                    'Dynacord':{'min_dmg':60, 'max_dmg':100, 'max_range':15, 'min_burst':0, 'max_burst':0,
                           'skill':'Throwing', 'ammo_dr':0, 'ammo_ac':0, 'ammo_dmg':1,'min_st':3, 'ap':5,
                           'dmg_type':'explode','hands':1, 'perks':{}}
                  }
        #armor statistics presets
        self.armor_stats={'Thermal':{ 'ac': 10, 'normal_dr': 30, 'normal_dt': 4, 'laser_dr': 20, 'laser_dt': 0, 'fire_dr': 75, 'fire_dt': 4, 'plasma_dr': 10, 'plasma_dt': 0, 'explode_dr': 35, 'explode_dt': 4, 'electric_dr': 40, 'electric_dt': 1, 'crit_c': -10  ,'crit_pow': -5 },
                          'Tesla':{ 'ac': 15, 'normal_dr': 25, 'normal_dt': 3, 'laser_dr': 85, 'laser_dt': 10, 'fire_dr': 10, 'fire_dt': 0, 'plasma_dr': 75, 'plasma_dt': 10, 'explode_dr': 20, 'explode_dt': 1, 'electric_dr': 80, 'electric_dt': 12, 'crit_c': -5  ,'crit_pow': -10 },
                          'CA':{ 'ac': 20, 'normal_dr': 40, 'normal_dt': 5, 'laser_dr': 60, 'laser_dt': 6, 'fire_dr': 25, 'fire_dt': 3, 'plasma_dr': 50, 'plasma_dt': 4, 'explode_dr': 40, 'explode_dt': 5, 'electric_dr': 45, 'electric_dt': 2, 'crit_c': -10  ,'crit_pow': -10 },
                          'CA mk2':{ 'ac': 25, 'normal_dr': 40, 'normal_dt': 6, 'laser_dr': 65, 'laser_dt': 7, 'fire_dr': 30, 'fire_dt': 4, 'plasma_dr': 50, 'plasma_dt': 5, 'explode_dr': 40, 'explode_dt': 6, 'electric_dr': 50, 'electric_dt': 3, 'crit_c': -10  ,'crit_pow': -10 },
                          'PA':{ 'ac': 30, 'normal_dr': 40, 'normal_dt': 12, 'laser_dr': 80, 'laser_dt': 18, 'fire_dr': 60, 'fire_dt': 12, 'plasma_dr': 40, 'plasma_dt': 10, 'explode_dr': 50, 'explode_dt': 20, 'electric_dr': 40, 'electric_dt': 12, 'crit_c': -15  ,'crit_pow': -15 },
                          'APA':{ 'ac': 30, 'normal_dr': 55, 'normal_dt': 15, 'laser_dr': 90, 'laser_dt': 19, 'fire_dr': 70, 'fire_dt': 16, 'plasma_dr': 60, 'plasma_dt': 15, 'explode_dr': 65, 'explode_dt': 20, 'electric_dr': 60, 'electric_dt': 15, 'crit_c': -15  ,'crit_pow': -15 }
                        }
        #damage modifier for critical hits
        #the values are pairs, such that the first value is the chance (eg 20=20%) and the second the modifier (eg. 3.0 =x3)
        #the order is relevant, the first pair is for the lowest critical hit power roll, the last for the highest
        self.critical_hit_dmg={
                        'EYE':    [[20, 3.0],[25, 3.0], [25,3.0],[20,3.5], [10, 3.5],[0, 3.5]],
                        'HEAD':   [[20, 3.0],[25, 3.0], [25,3.0],[20,3.0], [10, 3.0],[0, 3.0]],
                        'TORSO':  [[20, 3.0],[25, 3.0], [25,3.0],[20,3.5], [10, 3.5],[0, 3.5]],
                        'GROIN':  [[20, 2.5],[25, 2.5], [25,3.0],[20,3.0], [10, 3.0],[0, 3.0]],
                        'HANDS'  :[[20, 2.5],[25, 2.5], [25,2.5],[20,3.0], [10, 3.0],[0, 3.0]],
                        'LEGS':   [[20, 2.5],[25, 2.5], [25,2.5],[20,3.0], [10, 3.0],[0, 3.0]],
                        'UNAIMED':[[20, 1.5],[25, 1.5], [25,1.5],[20,2.0], [10, 2.0],[0, 2.0]],
                        'BURST':  [[20, 1.5],[25, 1.5], [25,1.5],[20,2.0], [10, 2.0],[0, 2.0]]
                        }
        #effects of critiacl hits
        #the values are pairs, such that the first value is the chance (eg 20=20%),
        #the second is a dictionary mess...
        # the key is either None for guaranteed effects
        #  or a tuple with a s.p.e.c.i.a.l. name and roll penalty value
        #  eg. ('e',-2) = "Roll EN-2"
        #  the s.p.e.c.i.a.l. vale of None is used for the uncanny nameless 'Roll'
        # the value in the dict is a tuple of effects names (note the "," on one value entries!)
        #just like self.critical_hit_dmg, the order is relevant, the first entry is for the lowest critical hit power roll, the last for the highest
        # TODO(low):change this data structure for something sane!
        self.critical_hit_effect={
                        'EYE':    [[20, None],
                                   [25, {(None, 5):('Knockdown',)}],
                                   [25, {('l',0):('Knockdown','Blinded')}],
                                   [20, {('e',-2):('Knockdown','Blinded'), None:('Blinded',)}],
                                   [10, {('l',0):('Knockout',), None:('Knockout','Blinded')}],
                                   [0,  {('e',0):('Death',), None:('Knockout','Blinded')}]
                                  ],
                        'HEAD':   [[20, {('e',0):('Knockdown',)}],
                                   [25, {(None, 5):('Knockdown',)}],
                                   [25, {('e',-2):('Knockdown',)}],
                                   [20, {('e',-2):('Knockout',), None:('Knockdown',)}],
                                   [10, {None:('Knockout',)}],
                                   [0,  {('e',0):('Death',), None:('Knockout',)}]
                                  ],
                        'TORSO':  [[20, {None:('Knockdown',)}],
                                   [25, {None:('Knockdown',)}],
                                   [25, {None:('Knockdown',)}],
                                   [20, {None:('Knockdown',)}],
                                   [10, {None:('Knockdown',)}],
                                   [0,  {None:('Knockdown',)}]
                                  ],
                        'GROIN':  [[20, {('e',0):('Knockdown',)}],
                                   [25, {('e',3):('Knockout',), None:('Knockdown',)}],
                                   [25, {('e',0):('Knockout',), None:('Knockdown',)}],
                                   [20, {('e',-2):('Knockout',), None:('Knockdown',)}],
                                   [10, {None:('Knockout',)}],
                                   [0,  {('e',3):('Death',), None:('Knockout',)}],
                                  ],
                        'HANDS':  [[20, {('s',3):('Weapon Drop',)}],
                                   [25, {('s',2):('Weapon Drop',)}],
                                   [25, {('s',1):('Weapon Drop',)}],
                                   [20, {('s',0):('Cripple Hand',), None:('Weapon Drop',)}],
                                   [10, {None:('Weapon Drop','Cripple Hand')}],
                                   [0,  {None:('Weapon Drop','Cripple Hand')}]
                                  ],
                        'LEGS':   [[20, {('e',5):('Cripple Leg',), None:('Knockdown',)}],
                                   [25, {('e',2):('Cripple Leg',), None:('Knockdown',)}],
                                   [25, {('e',0):('Cripple Leg',), None:('Knockdown',)}],
                                   [20, {('e',0):('Cripple Leg',), None:('Knockdown',)}],
                                   [10, {('e',0):('Knockout',), None:('Knockdown','Cripple Leg')}],
                                   [0,  {None:('Knockout','Cripple Leg')}]
                                  ],
                        'UNAIMED':[[20, None],
                                   [25, None],
                                   [25, None],
                                   [20, {None:('Knockdown',)}],
                                   [10, {None:('Knockdown',)}],
                                   [0,  {None:('Knockout',)}]
                                  ],
                        'BURST':  [[20, None],[25, None], [25,None],[20,None], [10, None],[0, None]] #???
                        }
        self._calc_derived()

    def _on_load(self):
        self.bonuses={}
        self.current_gun=None
        self.aim_mode='UNAIMED'
        self.target_stats={ 'ac':0, 'normal_dr':0, 'normal_dt':0, 'laser_dr':0,
                            'laser_dt': 0, 'fire_dr':0, 'fire_dt':0,
                            'plasma_dr':0, 'plasma_dt': 0, 'explode_dr': 0,
                            'explode_dt': 0, 'electric_dr':0, 'electric_dt':0,
                            'crit_c':0  ,'crit_pow':0, 'l':5, 's':5, 'e':5, None:0}

        for name, element in game.gui.elements.items():
            if (
                name.startswith('trait_frame_button_') or
                name.startswith('perk_frame_button_') or
                name.startswith('skill_frame_button_') or
                name.startswith('bonus_frame_button_') or
                name.startswith('weapon_frame_button_') or
                name.startswith('target_frame_button_') or
                name.startswith('hit_frame_button_')
               ):
                game.gui.highlight(on=False, name=name)

        for name in self.traits:
            button_name='trait_frame_button_'+name.lower().replace(' ', '')
            game.gui.highlight(on=True, name=button_name)
        for name in self.perks:
            button_name='perk_frame_button_'+name.lower().replace(' ', '')
            game.gui.highlight(on=True, name=button_name)
        for name in self.tags:
            button_name='skill_frame_button_'+name.lower().replace(' ', '')
            game.gui.highlight(on=True, name=button_name)

        self.update_ui()

    def _cals_skills(self):
        '''
        Calculates the starting values for all skills
        '''
        if self.level==1:
            self.skills['Small Guns']=5 + (4 *self.special['a'])
            self.skills['Big Guns']=2 *self.special['a']
            self.skills['Energy Guns']=10 + (1 *self.special['a'])
            self.skills['Close Combat']= 30 + 2 * (self.special['a'] + self.special['s'])
            self.skills['Throwing']=40 + self.special['a']
            self.skills['First Aid']=30 + ((self.special['p']+self.special['i'])//2)
            self.skills['Doctor']=15 + ((self.special['p']+self.special['i'])//2)
            self.skills['Lockpick']= 10 + (self.special['p'] +self.special['a'])
            self.skills['Repair']=  20 + (self.special['i'])
            self.skills['Science']= 25 + (2 * self.special['i'])
            self.skills['Outdoorsman']=5 + (1 * (self.special['i'] + self.special['e'])//2)
            self.skills['Scavenging']=0
            self.skills['Sneak']=5 + 3 *self.special['a']
            self.skills['Steal']= 3 *self.special['a']
            self.skills['Traps']= 20+ (self.special['p'] + self.special['a'] )//2
            self.skills['Speech']= 25 + (2 * self.special['c'])
            self.skills['Gambling']= 5*self.special['l']
            self.skills['Barter']=20 + (2 * self.special['c'])
            for name in self.tags:
                self.skills[name]+=20

    def _calc_derived(self):
        '''
        Calculate all 'derived' stats.
        '''
        #these are not affected by bonuse
        self._cals_skills()
        self.derived['hp_per_level']=self.special['e']/2
        self.derived['max_hp']=math.ceil(55+self.special['s']+(2*self.special['e'])+min(self.level-1, 23)*self.derived['hp_per_level'])+(30 if 'Lifegiver 1' in self.perks else 0)+(30 if 'Lifegiver 2' in self.perks else 0)+(30 if 'Lifegiver 3' in self.perks else 0)
        self.derived['sp_per_level']=5+ self.special['i']*2 + (5 if 'Skilled' in self.traits else 0) + (2 if 'Educated' in self.perks else 0)
        #these are
        with self._special_bonus():
            self.derived['max_perks']= 6 if 'Skilled' in self.traits else 8
            self.derived['pp']= 10*self.special['c']+self.skills['Speech']//3 +(50 if 'Magnetic Personality' in self.perks else 0) +(50 if 'Good Natured' in self.traits else 0)
            self.derived['sight']=20+self.special['p']*3 +(6 if 'Sharpshooter' in self.perks else 0)
            self.derived['sight_a']=20+self.special['p']*3 +(6 if 'Sharpshooter' in self.perks else 0)
            self.derived['sight_b']=17+self.special['p']*2 +(6 if 'Sharpshooter' in self.perks else 0)
            self.derived['sight_c']=9+self.special['p'] +(6 if 'Sharpshooter' in self.perks else 0)
            self.derived['sight_d']=6+self.special['p'] +(6 if 'Sharpshooter' in self.perks else 0)
            self.derived['sequence']=2+self.special['p']*2
            self.derived['ac']=3*self.special['a']*(2 if 'Livewire' in self.perks else 1)
            self.derived['ap']=5+self.special['a']//2+(1 if 'Action Boy 1' in self.perks else 0)+(1 if 'Action Boy 2' in self.perks else 0)+(-2 if 'Bruiser' in self.traits else 0)
            self.derived['carry_weight']=int((20+((25+(self.special['s']*25))/2.2)) *(1.33 if 'Pack Rat' in self.perks else 1.0) +(22 if 'Strong Back' in self.perks else 0))
            self.derived['melee']=max(self.special['s']-5, 1)*(2 if 'Bruiser' in self.traits else 1)+(5 if 'Heavy Handed' in self.traits else 0)+(10 if 'Close Combat Master' in self.perks else 0)
            self.derived['poision_res']=5*self.special['e']+(20 if 'Rad Resistance' in self.perks else 0)+(30 if 'Snakeater' in self.perks else 0)
            self.derived['radiation_res']=2*self.special['e']+(30 if 'Rad Resistance' in self.perks else 0)+(20 if 'Snakeater' in self.perks else 0)
            self.derived['healing_rate']= (7+self.special['e']//2)*(2 if 'Fast Metabolism' in self.traits else 1)+(5 if 'Faster Healing' in self.perks else 0)
            self.derived['crit_chance']=self.special['l']+(5 if 'More Critical' in self.perks else 0)+(10 if 'Even More Criticals' in self.perks else 0) +(10 if 'Finesse' in self.traits else 0)
            self.derived['crit_chance_cc']=self.derived['crit_chance']+(15 if 'Close Combat Master' in self.perks else 0)
            self.derived['crit_power']= (20 if 'Better Critical' in self.perks else 0)+ (-20 if 'Heavy Handed' in self.traits else 0)
            self.derived['crit_power_cc'] = self.derived['crit_power'] +(5 if 'Better Critical' in self.perks else 0)
            self.derived['crit_res'] = (10 if 'Man of Steel' in self.perks else 0)
            self.derived['crit_res_head']= self.derived['crit_res'] + (10 if 'Bonehead' in self.traits else 0)
            self.derived['normal_dt']= (1 if 'Toughness' in self.perks else 0)+(3 if 'Even Tougher' in self.perks else 0)
            self.derived['normal_dr']= (5 if 'Toughness' in self.perks else 0)+(10 if 'Even Tougher' in self.perks else 0)-(10 if 'Kamikaze' in self.traits else 0)
            self.derived['laser_dt']= (1 if 'Toughness' in self.perks else 0)
            self.derived['laser_dr']= (5 if 'Toughness' in self.perks else 0)-(10 if 'Kamikaze' in self.traits else 0)
            self.derived['fire_dt']= (1 if 'Toughness' in self.perks else 0)
            self.derived['fire_dr']= (5 if 'Toughness' in self.perks else 0)+-(10 if 'Kamikaze' in self.traits else 0)
            self.derived['plasma_dt']= (1 if 'Toughness' in self.perks else 0)
            self.derived['plasma_dr']= (5 if 'Toughness' in self.perks else 0)-(10 if 'Kamikaze' in self.traits else 0)
            self.derived['explode_dt']= (1 if 'Toughness' in self.perks else 0)
            self.derived['explode_dr']= (5 if 'Toughness' in self.perks else 0)-(10 if 'Kamikaze' in self.traits else 0)
            self.derived['electrical_dt']= (1 if 'Toughness' in self.perks else 0)
            self.derived['electrical_dr']= (5 if 'Toughness' in self.perks else 0)-(10 if 'Kamikaze' in self.traits else 0)
            self.derived['bonus_dmg']=(10 if 'Kamikaze' in self.traits else 0)
            self.derived['bonus_fire_dmg']=(25 if 'Pyromaniac' in self.perks else 0)
            self.derived['target_dr']=(30 if 'Finesse' in self.traits else 0)
            self.derived['bonus_xp']=(10 if 'Loner' in self.traits else 0)+(10 if 'Swift Learner' in self.perks else 0)
            self.derived['drug_heal']=(66 if 'Chem Reliant' in self.traits else 100)
            self.derived['drug_duration']=int(100*(2 if 'Chem Reliant' in self.traits else 1)*(0.5 if 'Fast Metabolism' in self.traits else 1))
            self.derived['fa_healed']= int(0.7*self.skills['First Aid'])+(30 if 'Field Medic' in self.perks else 0)+(22 if 'Medic' in self.perks else 0)
            self.derived['fa_cooldown']=min(180, 180-(self.skills['First Aid']//25 -2)*15)
            self.derived['doc_cooldown']=min(180, 180-(self.skills['Doctor']//25 -2)*15)
            self.derived['lvl']=self.level
            self.derived['sg_range']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Small Guns'])/4+2*(self.special['p']-2))
            self.derived['bg_range']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Big Guns'])/4+2*(self.special['p']-2))
            self.derived['ew_range']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Energy Guns'])/4+2*(self.special['p']-2))
            self.derived['sg_longrange']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Small Guns'])/4+4*(self.special['p']-2))
            self.derived['bg_longrange']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Big Guns'])/4+4*(self.special['p']-2))
            self.derived['ew_longrange']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Energy Guns'])/4+4*(self.special['p']-2))
            self.derived['sg_range_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Small Guns'])/4+2*(self.special['p']-2))
            self.derived['bg_range_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Big Guns'])/4+2*(self.special['p']-2))
            self.derived['ew_range_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Energy Guns'])/4+2*(self.special['p']-2))
            self.derived['sg_longrange_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Small Guns'])/4+4*(self.special['p']-2))
            self.derived['bg_longrange_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Big Guns'])/4+4*(self.special['p']-2))
            self.derived['ew_longrange_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Energy Guns'])/4+4*(self.special['p']-2))
            self.derived['tw_range']=int(-(95+50-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Throwing'])/4+2*(self.special['p']-2))
            self.derived['tw_range_aim']=int(-(95+50+60-(8 if 'Sharpshooter' in self.perks else 0)-self.skills['Throwing'])/4+2*(self.special['p']-2))
            self.derived['min_dmg']=0
            self.derived['max_dmg']=0
            self.derived['accuracy']=0
            self.derived['range']=0
            #apply bonus from drugs, armors and weapons
            for bonus in self.bonuses.values():
                for name, value in bonus.items():
                    if name in self.derived:
                        self.derived[name]+=value


    def bonus(self, source, values):
        '''Adds a temporary bonus to any statistic.
        source is a unique name to identify the source of the bonus (eg. drug name)
        values is a dict of name:value for the stats (can be special, or derived)
        '''
        button_name='bonus_frame_button_'+source.lower().replace(' ', '')
        if source in self.bonuses:
            del self.bonuses[source]
            game.gui.highlight(on=False, name=button_name)
        else:
            self.bonuses[source]=values
            game.gui.highlight(on=True, name=button_name)
        self.update_ui()

    @contextmanager
    def _special_bonus(self, *args):
        '''Context manager for applying temporary bonuses
        '''
        missing_special={}
        if self.bonuses:
            for source, bonus in self.bonuses.items():
                for bonus_name, value in bonus.items():
                    if bonus_name in 'special':
                        self.special[bonus_name]+=value
                        if self.special[bonus_name]>10:
                            self.bonuses[source][bonus_name]-=self.special[bonus_name]-10
                            self.special[bonus_name]=10
            for special_name, value in self.special.items():
                if value<1 and special_name !='none':
                    self.special[special_name]=1
                    missing_special[special_name]=value
        try:
            yield
        finally:
            if self.bonuses:
                for special_name, value in missing_special.items():
                    self.special[special_name]=value
                for bonus in self.bonuses.values():
                    for bonus_name, value in bonus.items():
                        if bonus_name in 'special':
                            self.special[bonus_name]-=value

    def get_txt(self):
        '''Returns a string with the summary of the stats
        '''
        preview='Level: '+str(self.level)+'\n'
        preview+='S: {s}\nP: {p}\nE: {e}\nC: {c}\nI: {i}\nA: {a}\nL: {l}\n'.format(**self.special)
        preview+='Traits:\n'
        for trait in self.traits:
            preview+=' -'+trait+'\n'
        preview+='Perks:\n'
        for perk, level in self.perks.items():
            preview+=' -'+perk+' ('+str(level)+')\n'
        preview+='Skills:\n'
        for skill, level in self.skills.items():
            if skill in self.tags:
                preview+=' +'
            else:
                preview+=' -'
            preview+=str(skill+':').ljust(13)+str(level)+'\n'
        return preview

    def dump(self):
        '''Saves the character to a text file
        '''
        name_of_file=game.gui['filename_input'].get()
        if name_of_file =='':
            name_of_file=datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S_')
            name_of_file+=''.join([random.choice(string.ascii_letters+string.digits) for ch in range(8)])
            name_of_file+='.txt'
            while os.path.exists(name_of_file):
                name_of_file=datetime.datetime.now().strftime('%Y_%m_%d_%H%M%S_')
                name_of_file+=''.join([random.choice(string.ascii_letters+string.digits) for ch in range(8)])
                name_of_file+='.txt'
            game.gui['filename_input'].enterText(name_of_file)

        with open(name_of_file, 'w') as the_file:
            the_file.write('FOnline:Reloaded Season 3 Character:\n')
            the_file.write('S: {s}\nP: {p}\nE: {e}\nC: {c}\nI: {i}\nA: {a}\nL: {l}\n'.format(**self.special))
            the_file.write('\nLevel: '+str(self.level)+'\n')
            the_file.write('\nTraits:\n')
            for trait in self.traits:
                the_file.write(' -'+trait+'\n')
            the_file.write('\nPerks:\n')
            for perk, level in self.perks.items():
                the_file.write(' -'+perk+' ('+str(level)+')\n')
            the_file.write('\nSkills:\n')
            for skill, level in self.skills.items():
                if skill in self.tags:
                    the_file.write(' +')
                else:
                    the_file.write(' -')
                the_file.write(str(skill+':').ljust(13)+str(level)+'\n')

            the_file.write('\nStats:\n')
            the_file.write('Armor Class:     {ac:>3}\nAction Points:   {ap:>3}\nCarry Weight:    {carry_weight:>3}\nMelee Damage:    {melee:>3}\nPoison Res.:     {poision_res:>3}\nRadiation Res.:  {radiation_res:>3}\nHealing Rate:    {healing_rate:>3}\nCrit. Chance:    {crit_chance:>3}\nCC. Crit. Chance:{crit_chance_cc:>3}\nHit Points:       {max_hp:>3}\nHP/Level:         {hp_per_level:>3}\nSP/Level:        {sp_per_level:>3}\nParty Points:    {pp:>3}\nSight:            {sight_a}\nFA healed:       {fa_healed:>3}\nDoc cooldown:    {doc_cooldown:>3}\n'.format(**self.derived))

        #game.gui['save']['text']='SAVED !'
        game.gui['feedback'].set_text('Exported to: '+name_of_file)
        game.gui['feedback_node'].show()
        game.toggle_database()


    def level_up(self):
        '''Level up, adds skills, hp, sp, perks etc
        '''
        if self.special['none']!=0:
            game.gui['feedback'].set_text('You need to use all S.P.E.C.I.A.L. points!')
            return
        if len(self.tags)!=3:
            game.gui['feedback'].set_text('You need to TAG 3 Skills!')
            return
        if self.level==1:
            for char in 'special':
                game.gui['special_'+char+'_minus'].hide()
                game.gui['special_'+char+'_plus'].hide()

        self.last_level_skills= {k:v for k,v in self.skills.items()} #deepcopy
        self.memory.append({'special':{k:v for k,v in self.special.items()},
                            'skills':{k:v for k,v in self.skills.items()},
                            'last_level_skills':{k:v for k,v in self.last_level_skills.items()},
                            'sp':int(self.derived['sp']),
                            'free_perks':int(self.derived['free_perks'])})
        self.level+=1
        self.derived['lvl']=self.level
        self.derived['sp']+=self.derived['sp_per_level']
        if self.level <25:
            perks_level=3
            if 'Skilled' in self.traits:
                perks_level+=1
            if self.level%perks_level ==0:
                self.derived['free_perks']+=1

        self.update_ui()

    def level_down(self):
        '''Same as level_up only in reverse.
        '''
        if self.level==1:
            return
        elif self.level==2:
            for char in 'special':
                game.gui['special_'+char+'_minus'].show()
                game.gui['special_'+char+'_plus'].show()
            #undo bonuses
            for source, value in self.bonuses.items():
                button_name='bonus_frame_button_'+source.lower().replace(' ', '')
                game.gui.highlight(on=False, name=button_name)
                self.bonuses={}
            if game.gui['trait_frame'].is_hidden():
                game.gui.show_hide(['trait_frame', 'perk_frame','skill_frame'],
                                ['bonus_frame','weapon_frame', 'target_frame','hit_frame'])
                game.gui['items']['text']='INVENTORY'


        self.level-=1
        last_level=self.memory.pop()
        self.special=last_level['special']
        self.skills=last_level['skills']
        self.derived['sp']=last_level['sp']
        self.derived['free_perks']=last_level['free_perks']
        self.last_level_skills =last_level['last_level_skills']

        for name, level in {k:v for k,v in self.perks.items()}.items():
            if level > self.level:
                del self.perks[name]
                button_name='perk_frame_button_'+name.lower().replace(' ', '')
                game.gui.highlight(on=False, name=button_name)

        self.update_ui()

    def set_special(self, name, value):
        '''Function for setting S.P.E.CI.A.L. values at level 1
        '''
        if self.level == 1:
            if self.special['none'] < value:
                return
            if 0 < self.special[name]+value <=10:
                self.special['none']-=value
                self.special[name]+=value
                self.update_ui()

    def set_trait(self, name):
        ''' Function for picking traits at level 1
        '''
        if self.level == 1:
            button_name='trait_frame_button_'+name.lower().replace(' ', '')

            if name in self.traits: #remove
                if name in self.trait_special:
                    for special, value in self.trait_special[name].items():
                        if self.special[special]-value >10 or self.special[special]-value <1:
                            return
                    for special, value in self.trait_special[name].items():
                        self.special[special]-=value

                del self.traits[name]
                game.gui.highlight(on=False, name=button_name)

            elif len(self.traits)<2: #add
                if name in self.trait_special:
                    for special, value in self.trait_special[name].items():
                        if self.special[special]+value >10 or self.special[special]+value <1:
                            return
                    for special, value in self.trait_special[name].items():
                        self.special[special]+=value
                self.traits[name]=0
                game.gui.highlight(on=True, name=button_name)

            self.update_ui()

    def _check_perk_req(self, name):
        '''Returns True if the character fulfils all the requirements for a given perk, else returns False
        name - name of the perk to check
        '''
        if name.startswith('Boneyard Guard'):
            if self.skills['Small Guns'] >=65 or self.skills['Big Guns'] >=65 or self.skills['Energy Guns'] >=65:
                return False
            for perk_name in self.perks:
                if perk_name.startswith('Boneyard Guard'):
                    return False

        #check if double
        if name in self.perks:
            return False
        #check level
        if self.level< self.perk_req[name]['level']:
            return False
        #check free perk points
        if self.perk_req[name]['perk_point'] > self.derived['free_perks']:
            return False
        #check skill
        if self.perk_req[name]['skill']:
            skill_pass=False
            for skill, value in self.perk_req[name]['skill'].items():
                if self.skills[skill]>= value:
                    skill_pass=True
            if not skill_pass:
                return False
        #check special
        for special, value in self.perk_req[name]['min_special'].items():
            if self.special[special]<value:
                return False
        for special, value in self.perk_req[name]['max_special'].items():
            if self.special[special]>value:
                return False
        #check perks
        for perk in self.perk_req[name]['perks']:
            if perk not in self.perks:
                return False
        return True

    def set_perk(self, name):
        '''Function for picking perks, checks requirements before actually giving the perk
        '''
        if self._check_perk_req(name):
            self.perks[name]=self.level
            self.derived['free_perks']-= self.perk_req[name]['perk_point']

            if name in self.perk_skill_bonus:
                for skill, value in self.perk_skill_bonus[name].items():
                    self.upgrade_skill(skill, value)
            if name in self.perk_special_bonus:
                for special, value in self.perk_special_bonus[name].items():
                    self.special[special]+=value
                    if self.special[special]>10:
                        self.special[special]=10
            button_name='perk_frame_button_'+name.lower().replace(' ', '')
            game.gui.highlight(on=True, name=button_name)
            self.update_ui()
        else:
            req_txt ='"'+name+'" perk requires: level:'+str(self.perk_req[name]['level'])+', '
            for skill, value in self.perk_req[name]['skill'].items():
                req_txt+=skill+': '+str(value)+', '
            for special, value in self.perk_req[name]['min_special'].items():
                req_txt+=special.upper()+'.>='+str(value)+', '
            for special, value in self.perk_req[name]['max_special'].items():
                req_txt+=special.upper()+'.<'+str(value)+', '
            for perk in self.perk_req[name]['perks']:
                req_txt+=perk+', '
            game.gui['feedback'].set_text(req_txt.strip(' ').strip(','))

    def tag_skill(self, name):
        '''Function for tagging skills at level 1,
        if not on level 1 dumps all availible point into name skill
        name - name of the skill
        '''
        if self.level==1:
            button_name='skill_frame_button_'+name.lower().replace(' ', '')
            if name in self.tags:
                del self.tags[name]
                game.gui.highlight(on=False, name=button_name)
            elif len(self.tags)<3:
                self.tags[name]=0
                game.gui.highlight(on=True, name=button_name)
            self.update_ui()
        else:
            self.set_skill(name, self.derived['sp'])

    def _get_skill_cost(self, name, sign=1):
        '''Returns the cost of raising a skill by 1 point or lowering it by 1
        name - name of the skill
        sign - if sign ==-1 returns skill points gained for lowering a skill
        '''
        v=0 if sign>0 else 1
        cost=1
        if self.skills[name] >=100+v:
            cost+=1
        if self.skills[name] >=125+v:
            cost+=1
        if self.skills[name] >=150+v:
            cost+=1
        if self.skills[name] >=175+v:
            cost+=1
        if self.skills[name] >=200+v:
            cost+=1
        return cost

    def upgrade_skill(self, name, value):
        ''' Raises the name skill by value skill points without using SP!
        name - name of the skill
        value - number of skill points used
        '''
        cost=self._get_skill_cost(name)
        while value>=cost:
            self.skills[name]+=1
            if name in self.tags:
                self.skills[name]+=1
            value-=cost
            cost=self._get_skill_cost(name)
        if (self.skills[name] >= self.skill_limits[name]):
            self.skills[name] = self.skill_limits[name]
        self.update_ui()

    def set_skill(self, name, value=1):
        ''' Raises the name skill by value skill points USING SP!
        name - name of the skill
        value - number of skill points used
        '''
        if self.level!=1:
            i=0
            sign=(1 if value>0 else -1)
            cost=self._get_skill_cost(name, sign)
            #print (cost, '<=', self.derived['sp']*sign, ':', cost <= self.derived['sp']*sign)
            while cost*sign <= self.derived['sp'] and i <abs(value):
                if self.skills[name]+sign<self.last_level_skills[name]:
                    return
                if (self.skills[name] >= self.skill_limits[name]) and sign==1:
                    self.skills[name] = self.skill_limits[name]
                    self.update_ui()
                    return
                self.derived['sp']-=cost*sign
                self.skills[name]+=sign
                if name in self.tags:
                    self.skills[name]+=sign
                    if (self.skills[name] >= self.skill_limits[name]):
                        self.skills[name] = self.skill_limits[name]
                cost=self._get_skill_cost(name, sign)
                i+=1
            self.update_ui()

    def gun(self, name):
        '''Sets the current used gun to name
        name - the name of the gun (per self.guns)
        '''
        self.current_gun=name
        button_name='weapon_frame_button_'+name.lower().replace(' ', '')
        for name, element in game.gui.elements.items():
            if name.startswith('weapon_frame_button'):
                game.gui.highlight(on=False, name=name)
        game.gui.highlight(on=True, name=button_name)
        self.fire_mode(None, False)
        self.update_ui()


    def target_stat(self, name, value):
        '''Changes the target_stats name by value
        name - name of the stats
        value - value added to self.target_stats[name]
        '''
        self.target_stats[name]+=value
        game.gui['target_txt'].set_text(target_template.format(**self.target_stats))
        self.update_ui()


    def target_preset(self, name):
        '''Sets the target_stats to a pre-defined values
        name - name of the preset (armor)
        '''
        for stat_name, value in self.armor_stats[name].items():
            self.target_stats[stat_name]=value
        button_name='target_frame_button_'+name.lower().replace(' ', '')
        for name, element in game.gui.elements.items():
            if name.startswith('target_frame_button'):
                game.gui.highlight(on=False, name=name)
        game.gui.highlight(on=True, name=button_name)
        game.gui['target_txt'].set_text(target_template.format(**self.target_stats))
        self.update_ui()

    def fire_mode(self, name=None, update_ui=True):
        '''Changes the current aim mode
        name - name of the aim mode
        update_ui - wheter or not to update the gui (when used inside self.update_ui())
        '''
        if name is None:
            name=self.aim_mode
        if self.current_gun:
            if name=='BURST' and self.guns[self.current_gun]['min_burst']==0:
                name='UNAIMED'
            if  self.guns[self.current_gun]['dmg_type']=='explode':
                name='UNAIMED'
            if self.current_gun in ('Avenger', 'Gatling Laser'):
                name='BURST'
        self.aim_mode=name
        button_name='hit_frame_button_'+name.lower().replace(' ', '')
        for name, element in game.gui.elements.items():
            if name.startswith('hit_frame_button'):
                game.gui.highlight(on=False, name=name)
        game.gui.highlight(on=True, name=button_name)
        if update_ui:
            self.update_ui()

    def roll_special(self, special, mod):
        '''Returns the chance a S.P.E.C.I.A.L. roll for the target will FAIL
        '''
        return  1.0-float(min(10.0,max(1.0,self.target_stats[special]+mod)))/10.0

    def update_ui(self):
        '''Updates all the gui with changed values
        '''
        self._calc_derived()
        if self.current_gun:
            with self._special_bonus():
                sharpshooter=8 if 'Sharpshooter' in self.perks else 0
                skill=self.skills[self.guns[self.current_gun]['skill']]
                pe_bonus=2*(self.special['p']-2)
                if 'Long Range' in self.guns[self.current_gun]['perks']:
                    pe_bonus*=2
                ac=self.target_stats['ac']
                aim=self.aim_bonus[self.aim_mode]
                missing_st=max(0,(self.guns[self.current_gun]['min_st']-self.special['s'])*20)
                max_hex=int(-(95+ac+aim+missing_st-sharpshooter-skill)/4+pe_bonus)


                base_dmg=float(self.guns[self.current_gun]['min_dmg']+
                               +self.derived['min_dmg']*self.guns[self.current_gun]['min_dmg']+
                               +self.guns[self.current_gun]['max_dmg']+
                               +self.derived['max_dmg']*self.guns[self.current_gun]['max_dmg']
                               )/2.0

                dmg_type=self.guns[self.current_gun]['dmg_type']
                #melee and bonus 'per-bullet' damage
                if self.guns[self.current_gun]['skill'] in ('Small Guns','Big Guns','Energy Guns'):
                    if 'Bonus Ranged Dmg.' in self.perks:
                        base_dmg+=3
                    if 'More Ranged Dmg.' in self.perks:
                        base_dmg+=4
                if self.guns[self.current_gun]['skill'] =='Close Combat':
                    base_dmg+=self.derived['melee']
                #critical hit damage
                crit_power=int(self.derived['crit_power'])
                crit_chance=int(self.derived['crit_chance'])
                if self.guns[self.current_gun]['skill'] == 'Close Combat':
                    crit_chance=self.derived['crit_chance_cc']
                    crit_power=self.derived['crit_power_cc']
                #aim
                crit_chance+=aim*(60+4*self.special['l'])//100
                #hidden bonus
                crit_chance+=4

                #target armor
                if 'Sharpshooter' in self.perks  and self.aim_mode not in ('UNAIMED', 'BURST'):
                    if 'Finesse' in self.traits:
                        crit_chance+=3*self.target_stats['crit_c']//8
                    else:
                        crit_chance+=self.target_stats['crit_c']//2
                else:
                    if 'Finesse' in self.traits:
                        crit_chance+=3*self.target_stats['crit_c']//4
                    else:
                        crit_chance+=self.target_stats['crit_c']
                crit_power+=self.target_stats['crit_pow']
                #% to float
                crit_chance=float(crit_chance)/100.0
                crit_hit_dmg=copy.deepcopy(self.critical_hit_dmg[self.aim_mode])
                if crit_power !=0:
                    crit_hit_dmg[0][0]-=crit_power
                    if crit_hit_dmg[0][0]<0:
                        crit_hit_dmg[1][0]+=crit_hit_dmg[0][0]
                        crit_hit_dmg[0][0]=0
                    crit_hit_dmg[-1][0]+=crit_power
                    if crit_hit_dmg[-1][0]<0:
                        crit_hit_dmg[-2][0]+=crit_hit_dmg[-1][0]
                        crit_hit_dmg[-1][0]=0
                    if crit_hit_dmg[-2][0]<0:
                        crit_hit_dmg[-3][0]+=crit_hit_dmg[-2][0]
                        crit_hit_dmg[-2][0]=0
                    if crit_hit_dmg[-3][0]<0:
                        crit_hit_dmg[-4][0]+=crit_hit_dmg[-3][0]
                        crit_hit_dmg[-3][0]=0
                crit_dmg=0
                for chance, multi in crit_hit_dmg:
                    crit_dmg+=base_dmg*multi*chance/100.0
                dmg=(crit_dmg*crit_chance)+((1.0-crit_chance)*base_dmg)

                #critical hit effects
                crit_hit_effect=copy.deepcopy(self.critical_hit_effect[self.aim_mode])
                if crit_power !=0:
                    crit_hit_effect[0][0]-=crit_power
                    if crit_hit_effect[0][0]<0:
                        crit_hit_effect[1][0]+=crit_hit_effect[0][0]
                        crit_hit_effect[0][0]=0
                    crit_hit_effect[-1][0]+=crit_power
                    if crit_hit_effect[-1][0]<0:
                        crit_hit_effect[-2][0]+=crit_hit_effect[-1][0]
                        crit_hit_effect[-1][0]=0
                    if crit_hit_effect[-2][0]<0:
                        crit_hit_effect[-3][0]+=crit_hit_effect[-2][0]
                        crit_hit_effect[-2][0]=0
                    if crit_hit_effect[-3][0]<0:
                        crit_hit_effect[-4][0]+=crit_hit_effect[-3][0]
                        crit_hit_effect[-3][0]=0
                crit_effect={}
                for chance, result in crit_hit_effect:
                    if result is not None:
                        for roll, effects in result.items():
                            if roll is None:
                                for effect in effects:
                                    if effect in crit_effect:
                                        crit_effect[effect]+=chance*crit_chance
                                    else:
                                        crit_effect[effect]=chance*crit_chance
                            else:
                                for effect in effects:
                                    if effect in crit_effect:
                                            crit_effect[effect]+=chance*crit_chance*self.roll_special(*roll)
                                    else:
                                        crit_effect[effect]=chance*crit_chance*self.roll_special(*roll)
                if 'Knockout' in self.guns[self.current_gun]['perks']:
                    if 'Knockout' in crit_effect:
                        crit_effect['Knockout']+=100*crit_chance
                    else:
                        crit_effect['Knockout']=100*crit_chance
                #heavy handed
                if self.guns[self.current_gun]['skill'] == 'Close Combat' and 'Heavy Handed' in self.traits:
                    if self.current_gun == 'Mega Power Fist':
                        if 'Knockdown' in crit_effect:
                            crit_effect['Knockdown']+=min(10.0,max(1.0,self.special['s']))*10.0
                            if crit_effect['Knockdown'] >100.0:
                                crit_effect['Knockdown']=100.0
                        else:
                            crit_effect['Knockdown']=min(10.0,max(1.0,self.special['s']))*10.0

                #armor DT
                if 'Penetrate' in self.guns[self.current_gun]['perks']:
                    dmg-=self.target_stats[dmg_type+'_dt']//3
                else:
                    dmg-=self.target_stats[dmg_type+'_dt']
                #armor DR
                dr=max(0, min(95, self.target_stats[dmg_type+'_dr']+self.guns[self.current_gun]['ammo_dr']+self.derived['target_dr']))/100.0
                #factor in critical hit armor bypass
                if self.aim_mode not in ('UNAIMED', 'BURST'):
                    bypass = (50.0*min(100, max(0, 51+crit_power - self.target_stats['l'])))/10000.0
                    dr=((1.0-crit_chance)*dr)+(crit_chance*dr*(1.0-bypass))
                dmg*=1.0-float(dr)

                #kamikaze or other final dmg bonus
                dmg+=dmg*float(self.derived['bonus_dmg'])/100.0
                if dmg_type == 'fire':
                    dmg+=dmg*float(self.derived['bonus_fire_dmg'])/100.0
                hit_text=''
                if self.aim_mode == 'BURST':
                    min_base_dmg=base_dmg*self.guns[self.current_gun]['min_burst']
                    max_base_dmg=base_dmg*self.guns[self.current_gun]['max_burst']
                    min_dmg=dmg*self.guns[self.current_gun]['min_burst']
                    max_dmg=dmg*self.guns[self.current_gun]['max_burst']
                    hit_text="95% range: {max_hex}\nBase Damage:\n  {min_base_dmg:3.1f}-{max_base_dmg:3.1f}\nDamage:\n  {min_dmg:3.1f}-{max_dmg:3.1f}\n\n".format(max_hex=max_hex, min_base_dmg=min_base_dmg, max_base_dmg=max_base_dmg, min_dmg=min_dmg, max_dmg=max_dmg)
                else:
                    hit_text="95% range: {max_hex}\nBase Damage:  {base_dmg:3.1f}\nDamage:  {dmg:3.1f}\n\n".format(max_hex=max_hex, base_dmg=base_dmg, dmg=dmg)

                for effect, chance in crit_effect.items():
                    if chance >0.0:
                        hit_text+='{chance:>4.1f}% {effect}\n'.format(chance=chance, effect=effect)

                if 'Knockback' in self.guns[self.current_gun]['perks']:
                    hit_text+=' Knockback\n'
                if dmg_type == 'explode':
                    hit_text+=' Explode Knockback\n'
                game.gui['hiteffect'].set_text(hit_text)

        if game.gui['save']['text']=='SAVED !':
            game.gui['save']['text']='SAVE AS .TXT'
        with self._special_bonus():
            special_formated='{s}\n\n{p}\n\n{e}\n\n{c}\n\n{i}\n\n{a}\n\n{l}\n\n{none}'.format(**self.special)
        stats_formated=stat_template.format(**self.derived)
        game.gui['specialtxt'].set_text(special_formated)
        game.gui['statstxt'].set_text(stats_formated)
        game.gui['level'].set_text('LEVEL:'+str(self.level))

        for name, value in self.skills.items():
            button_name='skill_frame_button_'+name.lower().replace(' ', '')
            game.gui[button_name]['text']='{name:<13}{value:>4}%'.format(name=name, value=value)
