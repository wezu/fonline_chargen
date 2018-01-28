import sqlite3
import os
import sys
if sys.version_info >= (3, 0):
    import pickle
else:
    import cPickle as pickle


char_table='''(name TEXT PRIMARY KEY, keys TEXT,
s INTEGER, p INTEGER, e INTEGER, c INTEGER, i INTEGER, a INTEGER, l INTEGER,
pp  INTEGER, sight  INTEGER, ac  INTEGER, ap  INTEGER, carry_weight  INTEGER,
melee  INTEGER, crit_chance  INTEGER, crit_chance_cc  INTEGER,
crit_power  INTEGER, crit_power_cc INTEGER, lvl  INTEGER,
small_guns INTEGER,big_guns INTEGER,energy_guns INTEGER,
close_combat INTEGER,throwing INTEGER,first_aid INTEGER,
doctor INTEGER,lockpick INTEGER,repair INTEGER,science INTEGER,
outdoorsman INTEGER,scavenging INTEGER,sneak INTEGER,steal INTEGER,
traps INTEGER,speech INTEGER,gambling INTEGER,barter INTEGER)'''

data_table='''(name TEXT PRIMARY KEY, memory PICKLE, perks PICKLE,
traits PICKLE, skills PICKLE, last_level_skills PICKLE, tags PICKLE,
level INTEGER, special PICKLE, preview TEXT)'''

char_table_insert='''INSERT OR REPLACE INTO charaters(name, keys, s, p, e, c,
i, a, l, pp, sight,ac, ap, carry_weight, melee, crit_chance, crit_chance_cc,
 crit_power, crit_power_cc, lvl, small_guns, big_guns, energy_guns,
 close_combat, throwing, first_aid, doctor, lockpick, repair, science,
 outdoorsman, scavenging, sneak, steal, traps, speech, gambling, barter)
VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''


data_table_insert='''INSERT OR REPLACE INTO raw_data(name, memory,
perks, traits, skills, last_level_skills, tags, level, special, preview)
VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

known_keys=('name', 'keys', 's', 'p', 'e', 'c', 'i', 'a', 'l', 'pp',
            'sight','ac', 'ap', 'carry_weight', 'melee', 'crit_chance',
            'crit_chance_cc', 'crit_power', 'crit_power_cc', 'lvl',
            'small_guns', 'big_guns', 'energy_guns', 'close_combat',
            'throwing', 'first_aid', 'doctor', 'lockpick', 'repair',
            'science', 'outdoorsman', 'scavenging', 'sneak', 'steal',
             'traps', 'speech', 'gambling', 'barter')

alias_keys={'party_points':'pp',
            'party_point':'pp',
            'action_point':'ap',
            'action_points':'ap',
            'critical_chance':'crit_chance',
            'critical_power':'crit_power',
            'energy_weapons':'energy_guns',
            'ew':'energy_guns',
            'sg':'small_guns',
            'bg':'big_guns',
            'fa':'first_aid',
            'od':'outdoorsman',
            'doc':'doctor',
            'level':'lvl',
            'lv':'lvl',
            'cc':'close_combat',
            'hth':'close_combat',
            'hit_points':'hp',
            'hit_point':'hp',
            'health':'hp',
            'str':'s',
            'strength':'s',
            'pe':'p',
            'per':'p',
            'perception':'p',
            'en':'e',
            'end':'e',
            'endurance':'e',
            'cha':'c',
            'ch':'c',
            'charisma':'c',
            'int':'i',
            'ag':'a',
            'agi':'a',
            'agility':'a',
            'lc':'l',
            'lck':'l',
            'lk':'l',
            'luck':'l'
             }
class Database():
    '''
    This calss handels sqlite data storage
    '''
    def __init__(self, db_file):
        #  register the "loader" to get the data back out.
        sqlite3.register_converter("PICKLE", pickle.loads)

        #conect to the db or create it
        if os.path.exists(db_file):
            self.connection = sqlite3.connect(db_file)
        else:
            self.connection = sqlite3.connect(db_file)
            with self.connection:
                cur = self.connection.cursor()
                cur.execute("CREATE TABLE charaters "+char_table+";")
                cur.execute("CREATE VIRTUAL TABLE keytags USING fts4(name, keys);")
                cur.execute("CREATE TABLE raw_data"+data_table+" ;")

    def search(self, text=None):
        rows=[]
        if text == '' or text is None: #search for all
            with self.connection :
                cur = self.connection.cursor()
                cur.execute("SELECT name, keys, s,p,e,c,i,a,l FROM charaters")
                rows = cur.fetchall()
        else:
            #split the text
            where=''
            keys=''
            tokens=text.split(',')
            tokens=[i.strip() for i in tokens]

            for token in tokens:
                if '<=' in token:
                    t=token.split('<=')
                    t=[i.strip().lower().replace(' ', '_') for i in t]
                    if t[0] in alias_keys:
                        t[0]=alias_keys[t[0]]
                    if t[0] in known_keys:
                        where+=t[0]+'<='+t[1]+' AND '
                elif '>=' in token:
                    t=token.split('>=')
                    t=[i.strip().lower().replace(' ', '_') for i in t]
                    if t[0] in alias_keys:
                        t[0]=alias_keys[t[0]]
                    if t[0] in known_keys:
                        where+=t[0]+'>='+t[1]+' AND '
                elif '=' in token:
                    t=token.split('=')
                    t=[i.strip().lower().replace(' ', '_') for i in t]
                    if t[0] in alias_keys:
                        t[0]=alias_keys[t[0]]
                    if t[0] in known_keys:
                        where+=t[0]+'='+t[1]+' AND '
                elif '<' in token:
                    t=token.split('<')
                    t=[i.strip().lower().replace(' ', '_') for i in t]
                    if t[0] in alias_keys:
                        t[0]=alias_keys[t[0]]
                    if t[0] in known_keys:
                        where+=t[0]+'<'+t[1]+' AND '
                elif '>' in token:
                    t=token.split('>')
                    t=[i.strip().lower().replace(' ', '_') for i in t]
                    if t[0] in alias_keys:
                        t[0]=alias_keys[t[0]]
                    if t[0] in known_keys:
                        where+=t[0]+'>'+t[1]+' AND '
                else:
                    token=token.strip("'")
                    token=token.strip('"')
                    token=token.strip("'")
                    keys+='*'+token.strip('"')+'* '


            if keys!= '':
                fts="name IN( SELECT name FROM keytags WHERE keys MATCH '"+keys+"')"
            else:
                fts=''
                where=where.strip().strip('AND')
            try:
                with self.connection :
                    cur = self.connection.cursor()
                    cur.execute("SELECT name, keys, s,p,e,c,i,a,l FROM charaters WHERE "+where+fts)
                    rows = cur.fetchall()
            except:
                pass
        return rows


    def save(self, name, keys, stats):
        #name
        raw_keys=keys
        s=stats.special['s']
        p=stats.special['p']
        e=stats.special['e']
        c=stats.special['c']
        i=stats.special['i']
        a=stats.special['a']
        l=stats.special['l']
        pp=stats.derived['pp']
        sight=stats.derived['pp']
        ac=stats.derived['pp']
        ap=stats.derived['pp']
        carry_weight=stats.derived['pp']
        melee=stats.derived['pp']
        crit_chance=stats.derived['pp']
        crit_chance_cc=stats.derived['pp']
        crit_power=stats.derived['pp']
        crit_power_cc=stats.derived['pp']
        lvl=stats.level
        small_guns=stats.skills['Small Guns']
        big_guns=stats.skills['Big Guns']
        energy_guns=stats.skills['Energy Guns']
        close_combat=stats.skills['Close Combat']
        throwing=stats.skills['Throwing']
        first_aid=stats.skills['First Aid']
        doctor=stats.skills['Lockpick']
        lockpick=stats.skills['Small Guns']
        repair=stats.skills['Repair']
        science=stats.skills['Science']
        outdoorsman=stats.skills['Outdoorsman']
        scavenging=stats.skills['Scavenging']
        sneak=stats.skills['Sneak']
        steal=stats.skills['Steal']
        traps=stats.skills['Traps']
        speech=stats.skills['Speech']
        gambling=stats.skills['Gambling']
        barter=stats.skills['Barter']

        for trait in stats.traits:
            keys+=' '+trait+' '+trait.lower()+' '+trait.lower().replace(' ', '_')+' '+trait.replace(' ', '_')

        for perk in stats.perks:
            keys+=' '+perk+' '+perk.lower()+' '+perk.lower().replace(' ', '_')+' '+perk.replace(' ', '_')
        keys+=' '+name

        memory=pickle.dumps(stats.memory)
        perks=pickle.dumps(stats.perks)
        traits=pickle.dumps(stats.traits)
        skills=pickle.dumps(stats.skills)
        last_level_skills=pickle.dumps(stats.last_level_skills)
        tags=pickle.dumps(stats.tags)
        level=pickle.dumps(stats.level)
        special=pickle.dumps(stats.special)
        preview=stats.get_txt()

        with self.connection:
            cur = self.connection.cursor()
            cur.execute(char_table_insert, (name,raw_keys, s, p, e, c, i, a, l,
                                            pp, sight,ac, ap, carry_weight,
                                            melee, crit_chance, crit_chance_cc,
                                            crit_power, crit_power_cc, lvl,
                                            small_guns, big_guns, energy_guns,
                                            close_combat, throwing, first_aid,
                                            doctor, lockpick, repair, science,
                                            outdoorsman, scavenging, sneak, steal,
                                            traps, speech, gambling, barter))
            cur.execute("INSERT OR REPLACE INTO keytags(name, keys) VALUES(?, ?)", (name, keys))
            cur.execute(data_table_insert, (name, memory, perks, traits,
                                            skills, last_level_skills,
                                            tags, level, special, preview))


    def get_preview(self, name):
        preview=''
        with self.connection :
            cur = self.connection.cursor()
            cur.execute("SELECT preview FROM raw_data WHERE name=?", [(name)])
            preview=cur.fetchone()[0]
        return preview

    def load(self, name, stats):

        with self.connection :
            cur = self.connection.cursor()
            cur.execute("SELECT memory, perks, traits, skills, last_level_skills, tags, level, special  FROM raw_data WHERE name=?", [(name)])
            data=cur.fetchone()
            if sys.version_info >= (3, 0):
                stats.memory=pickle.loads(data[0])
                stats.perks=pickle.loads(data[1])
                stats.traits=pickle.loads(data[2])
                stats.skills=pickle.loads(data[3])
                stats.last_level_skills=pickle.loads(data[4])
                stats.tags=pickle.loads(data[5])
                stats.level=pickle.loads(data[6])
                stats.special=pickle.loads(data[7])

            else:
                stats.memory=pickle.loads(str(data[0]))
                stats.perks=pickle.loads(str(data[1]))
                stats.traits=pickle.loads(str(data[2]))
                stats.skills=pickle.loads(str(data[3]))
                stats.last_level_skills=pickle.loads(str(data[4]))
                stats.tags=pickle.loads(str(data[5]))
                stats.level=pickle.loads(str(data[6]))
                stats.special=pickle.loads(str(data[7]))
            stats._on_load()

            cur.execute("SELECT keys FROM charaters WHERE name=?", [(name)])
            keys=cur.fetchone()[0]
            game.gui['tag_input'].enterText(keys)
            game.gui['name_input'].enterText(name)



