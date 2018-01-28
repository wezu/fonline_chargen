#!/usr/bin/env python3
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
#import python stuff
from __future__ import print_function
import random
import string
import datetime
import operator
import os
import sys
if sys.version_info >= (3, 0):
    import builtins
else:
    import __builtin__ as builtins
import math
import json
import ast
import copy
import types
import itertools
from importlib import import_module
from collections import deque
from contextlib import contextmanager
import traceback
import webbrowser
import sqlite3

#import panda3d stuff
from panda3d.core import *
from direct.showbase.DirectObject import DirectObject
from direct.interval import IntervalManager
from direct.gui.OnscreenImage import OnscreenImage
from direct.gui.OnscreenText import OnscreenText
from direct.showbase.PythonUtil import fitSrcAngle2Dest
#we need to read the config before we go on
if sys.version_info >= (3, 0):
    import configparser
else:
    import ConfigParser as configparser
Config = configparser.ConfigParser()
Config.read('config.ini')
builtins.Config = Config
#read all options as prc_file_data in case they have p3d meaning
for section in Config.sections():
    for option in Config.options(section):
        loadPrcFileData("", option +' '+Config.get(section, option))
#if this is set to something else things will break, so we overide here!
loadPrcFileData("", "show-buffers 0")
loadPrcFileData("", "threading-model")
loadPrcFileData("", "audio-library-name null")
#loadPrcFileData("", "buffer-viewer-position urcorner")
loadPrcFileData('','textures-power-2 None')

from direct.showbase import ShowBase

##Data loading:##
#add 'code' and 'plugins' dirs to sys.path
#add anything else to modelpath
plugins={}
builtins.plugins=plugins
for mod in reversed(Config.get('datafiles', 'loadorder').split(', ')):
    if os.path.isdir('data/'+mod) and os.path.exists('data/'+mod):
        for directory in os.listdir('data/'+mod):
            if directory in ('code', 'plugins'):
                sys.path.append('data/'+mod+'/'+directory)
            if directory == 'plugins':
                for file_name in os.listdir('data/'+mod+'/'+directory):
                    if file_name[-3:]=='.py':
                        try:
                            plugins[file_name[:-3]]=import_module(file_name[:-3]).Plugin()
                        except:
                            print('Error loading plugin:'+'data/'+mod+'/'+directory+'/'+file_name)
            getModelPath().appendDirectory('data/'+mod)

wp = WindowProperties.getDefault()
wp.set_title("FOnline:Reloaded Chargen by player314")
wp.set_icon_filename('ui/icon.ico')
wp.set_cursor_hidden(True)
WindowProperties.setDefault(wp)

from game import Game


screen_text=None
builtins.screen_text = screen_text

def print_to_screen(*args):
    sep=' '
    end=None
    file=None
    flush=False
    if builtins.screen_text is not None:
        builtins.screen_text.destroy()
        builtins.screen_text=None
    if args:
        txt=sep.join((str(i) for i in args))+'\nPress [F10] to hide this message'
        builtins.screen_text = OnscreenText(text = txt,
                                        pos = (8,-48),
                                        scale =16,
                                        fg=(1,0,0,1),
                                        shadow=(0,0,0,1),
                                        wordwrap=64,
                                        align=TextNode.ALeft,
                                        parent=pixel2d)

builtins.print = print_to_screen

#Start the game
class App(DirectObject):
    def __init__(self):
        #init panda3d showbase
        base = ShowBase.ShowBase()

        builtins.print_to_screen=print_to_screen

        base.setBackgroundColor(0, 0, 0)
        base.disableMouse()
        base.win.set_close_request_event('exit-event')
        self.accept('exit-event', self.on_exit)
        self.accept('f10', print_to_screen)

        #hacking the event menager
        eventMgr.doEvents=self.doEvents
        #hasking interval manager
        IntervalManager.ivalMgr._step=IntervalManager.ivalMgr.step
        IntervalManager.ivalMgr.step=self.ivalMgr_step
        #hacking task manager
        taskMgr._step=taskMgr.step
        taskMgr.step=self.tsk_step


        try:
            #init game
            self.game=Game(self)
            #start plugins
            for plugin in plugins.values():
                try:
                    plugin.start()
                except:
                    pass
        except Exception as err:
            trbck=traceback.format_exc(limit=1)
            txt='Oops, something went wrong!\n\n'+trbck+'\nPlease report this error to the game developers.'
            print_to_screen(txt)


    def tsk_step(self):
        try:
            taskMgr._step()
        except:
            trbck=traceback.format_exc(limit=1)
            txt='Oops, something went wrong!\n\n'+trbck+'\nPlease report this error to the game developers.'
            print_to_screen(txt)

    def ivalMgr_step(self):
        try:
            IntervalManager.ivalMgr._step()
        except:
            trbck=traceback.format_exc(limit=2)
            txt='Oops, something went wrong!\n\n'+trbck+'\nPlease report this error to the game developers.'
            print_to_screen(txt)

    def doEvents(self):
        """
        Process all the events on the C++ event queue
        """
        while (not eventMgr.eventQueue.isQueueEmpty()):
            try:
                eventMgr.processEvent(eventMgr.eventQueue.dequeueEvent())
            except:
                trbck=traceback.format_exc(limit=1)
                txt='Oops, something went wrong!\n\n'+trbck+'\nPlease report this error to the game developers.'
                print_to_screen(txt)


    def final_exit(self):
        base.destroy()
        os._exit(1)

    def on_exit(self):
        try:
            self.game.exit_game()
        except:
            self.final_exit()

##Run the show!##
app=App()
base.run()
