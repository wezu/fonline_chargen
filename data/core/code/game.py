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
#import panda3d stuff
from panda3d.core import *
from direct.showbase.DirectObject import DirectObject

#load the main components
from ui import UI
from loading_screen import loading
from stats import Stats
from database import Database

def get_local_file(path):
    return getModelPath().findFile(path).toOsSpecific()


class Game(DirectObject):
    def __init__(self, app):
        self.app=app
        builtins.get_local_file = get_local_file

        #insert the game into buildins for easy gui callback
        builtins.game=self

        #stats
        self.stats=Stats()
        builtins.stats=self.stats

        with loading():
            #database
            self.db=Database('save.db')
            #init the gui system
            self.gui=UI()
            self.gui.software_cursor()
            #make the main menu
            self.gui.load_from_file(get_local_file('ui/layout.json'))
            self.gui.show_hide(['special_frame','trait_frame','perk_frame',
                                'skill_frame','stats_frame','level_up',
                                'level_down','level_node','items','paypal',
                                'shader','save','exit'])
            self.stats.update_ui()

    def toggle_shader(self):
        if getattr(self, "shader_quad", None) is None:
            winprops = WindowProperties()
            winprops.set_size(1024,600)
            props = FrameBufferProperties()
            props.set_rgb_color(True)
            props.set_rgba_bits(8, 8, 8, 8)
            props.set_depth_bits(0)
            props.set_aux_rgba(False)
            props.set_srgb_color(False)
            self.fbo= base.graphicsEngine.make_output(base.pipe, 'fbo', -2,
                                                    props, winprops,
                                                    GraphicsPipe.BFSizeTrackHost |
                                                    GraphicsPipe.BFCanBindEvery |
                                                    GraphicsPipe.BFRttCumulative |
                                                    GraphicsPipe.BFRefuseWindow,
                                                    base.win.get_gsg(), base.win)

            self.fbo.set_clear_color((0, 0, 0, 0))
            self.color = Texture()
            self.color.set_wrap_u(Texture.WM_clamp)
            self.color.set_wrap_v(Texture.WM_clamp)
            self.fbo.add_render_texture(tex=self.color,
                                        mode=GraphicsOutput.RTMBindOrCopy,
                                        bitplane=GraphicsOutput.RTPColor)
            self.fbo_cam = base.makeCamera2d(self.fbo)
            cm = CardMaker("quad")
            cm.set_frame_fullscreen_quad()

            self.shader_quad = NodePath(cm.generate())
            self.shader_quad.set_shader(Shader.load(Shader.SLGLSL, "shaders/crt_v.glsl","shaders/crt_f.glsl"),1)
            self.shader_quad.set_shader_input('color_tex', self.color)
            self.shader_quad.reparent_to(render2dp)
        else:
            if self.shader_quad.is_hidden():
                self.shader_quad.show()
                self.fbo.set_active(True)
            else:
                self.shader_quad.hide()
                self.fbo.set_active(False)

    def show_preview(self, name):
        txt=self.db.get_preview(name)
        self.gui['load_preview'].set_text(txt)
        self.gui.show_hide('preview_frame')
        self.last_name=name

    def load_from_db(self):
        self.db.load(self.last_name, self.stats)
        self.toggle_database()
        self.gui['feedback'].set_text('Character loaded!')
        self.gui['feedback_node'].show()

    def save_to_db(self):
        name=self.gui['name_input'].get()
        keys=self.gui['tag_input'].get()
        self.db.save(name, keys, self.stats)
        self.search(True)

    def search(self, show_all=False):
        #remove old buttons
        names_to_remove=[]
        for name, element in self.gui.elements.items():
            if name.startswith('charater_load_'):
                names_to_remove.append(name)
        for name in  names_to_remove:
            self.gui.remove_button(name)
        #find characters
        if show_all:
            records=self.db.search()
        else:
            records=self.db.search(self.gui['search_input'].get())

        #create buttons
        for name, keys, s,p,e,c,i,a,l in records:

            txt='{name:<38}{keys:<59}{s:<8}{p:<8}{e:<8}{c:<8}{i:<8}{a:<8}{l:<8}'.format(name=name, keys=keys, s=s,p=p,e=e,c=c,i=i,a=a,l=l)
            self.gui.button(txt=txt, sort_dict={"name":name, "tag":keys, "s":s, "p":p,"e":e, "c":c,"i":i, "a":a,"l":l},
                            cmd="game.show_preview('"+name+"')", parent="database_frame_canvas",
                            width=1000, pos=[3,i*32], mono_font=1, center=0,
                            name='charater_load_'+name.lower().replace(' ', '_'))
        self.gui.sort_buttons('database_frame_canvas', 'name')

    def toggle_database(self):
        if self.gui['trait_frame'].is_hidden():
            self.toggle_inventory()
        popup=['database_frame', 'save_frame']
        editor=['special_frame','trait_frame','perk_frame','skill_frame',
                 'stats_frame','level_up','level_down','items','paypal','shader',
                 'save','exit', 'level_node']
        if self.gui['database_frame'].is_hidden():
            self.gui.show_hide(popup, editor)
            self.search(True)
        else:
            self.gui.show_hide(editor, popup)
        self.gui.show_hide(None, 'preview_frame')


    def toggle_inventory(self):
        if self.gui['trait_frame'].is_hidden():
            self.gui.show_hide(['trait_frame', 'perk_frame','skill_frame'],
                                ['bonus_frame','weapon_frame', 'target_frame','hit_frame'])
            self.gui['items']['text']='INVENTORY'
        else:
            if self.stats.level==1:
                self.gui['feedback'].set_text('Level up first!')
            return
            self.gui.show_hide(['bonus_frame', 'weapon_frame','target_frame','hit_frame'],
                                ['trait_frame', 'perk_frame','skill_frame'])
            self.gui['items']['text']='CHARACTER'


    def support(self, hide=False):
        popup='support_frame'
        editor=['special_frame','trait_frame','perk_frame','skill_frame',
                 'stats_frame','level_up','level_down','items','paypal','shader',
                 'save','exit', 'level_node']
        if hide:
            self.gui.show_hide(editor, popup)
            self.gui['items']['text']='INVENTORY'
        else:
            self.gui.show_hide(popup, editor)
            self.gui.show_hide([],['bonus_frame', 'weapon_frame','target_frame','hit_frame'])

    def do_nill(self):
        pass

    def save_screen(self):
        base.screenshot('character')

    def exit_game(self):
        with open('config.ini', 'w') as config_filename:
            Config.write(config_filename)
        self.app.final_exit()



