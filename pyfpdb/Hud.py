#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Hud.py

Create and manage the hud overlays.
"""
#    Copyright 2008-2011  Ray E. Barker

#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA 02111-1307 USA

########################################################################
# todo
 
import L10n
_ = L10n.get_translation()

#    Standard Library modules
import os
import sys
import string

import logging
# logging has been set up in fpdb.py or HUD_main.py, use their settings:
log = logging.getLogger("hud")

#    FreePokerTools modules
import Configuration
import Mucked
import Database


def importName(module_name, name):
    """Import a named object 'name' from module 'module_name'."""
#    Recipe 16.3 in the Python Cookbook, 2nd ed.  Thanks!!!!

    try:
        module = __import__(module_name, globals(), locals(), [name])
    except:
        return None
    return(getattr(module, name))


class Hud:
    def __init__(self, parent, table, max, poker_game, game_type, config, db_connection):
#    __init__ is (now) intended to be called from the stdin thread, so it
#    cannot touch the gui
        if parent is None:  # running from cli ..
            self.parent = self
        else:
            self.parent    = parent
        self.table         = table
        self.config        = config
        self.poker_game    = poker_game
        self.game_type     = game_type # (ring|tour)
        self.max           = max
        self.db_connection = db_connection
        self.deleted       = False
        self.stacked       = True
        self.site          = table.site
        self.mw_created    = False
        self.hud_params    = parent.hud_params
        self.repositioningwindows = False # used to keep reposition_windows from re-entering

        self.stat_windows  = {}  #?is this still used?
        self.popup_windows = {}
        self.aux_windows   = []
        
        self.site_parameters = config.get_site_parameters(self.table.site)
        self.supported_games_parameters = config.get_supported_games_parameters(self.poker_game, self.game_type)
        self.layout_set = config.get_layout(self.table.site, self.game_type)
        
        if self.layout_set == None:
            log.error(_("No layout found for %s games for site %s."+"\n") % (self.game_type, self.table.site))
            return
            
        if self.max not in self.layout_set.layout:
            log.error(_("No layout found for %d-max %s games for site %s."+"\n") % (self.max, self.game_type, self.table.site))
            return
        else:
            self.layout = self.layout_set.layout[self.max]
                    
        # if there are AUX windows configured, set them up
        if not self.supported_games_parameters['aux'] == [""]:
            for aux in self.supported_games_parameters['aux'].split(","):
                aux=string.strip(aux) # remove leading/trailing spaces
                aux_params = config.get_aux_parameters(aux)
                my_import = importName(aux_params['module'], aux_params['class'])
                if my_import == None:
                    continue
                #The main action happening below !!!
                # the module/class is instantiated and is fed the config
                # and aux_params.  Normally this is ultimately inherited
                # at Mucked.Aux_seats() for a hud aux
                #
                #The instatiated aux object is recorded in the
                # self.aux_windows list in this module
                self.aux_windows.append(my_import(self, config, aux_params))

        self.creation_attrs = None
        

    def up_update_table_position(self):
#    callback for table moved

##    move the stat windows
#        adj = self.adj_seats(self.hand, self.config)
#        loc = self.config.get_locations(self.table.site, self.max)
#        for i, w in enumerate(self.stat_windows.itervalues()):
#            (x, y) = loc[adj[i+1]]
#            w.relocate(x, y)
##    move the main window
#        self.main_window.move(self.table.x + self.site_params['xshift'], self.table.y + self.site_params['yshift'])
#    and move any auxs
        for aux in self.aux_windows:
            aux.update_card_positions()
        return True

#    def on_button_press(self, widget, event):
#        if event.button == 1: # if primary button, start movement
#            self.main_window.begin_move_drag(event.button, int(event.x_root), int(event.y_root), event.time)
#            return True
#        if event.button == 3: # if secondary button, popup our main popup window
#            widget.popup(None, None, None, event.button, event.time)
#            return True
#        return False

    def kill(self, *args):
#    kill all stat_windows, popups and aux_windows in this HUD
#    heap dead, burnt bodies, blood 'n guts, veins between my teeth
        for s in self.stat_windows.itervalues():
            s.kill_popups()
            try:
                # throws "invalid window handle" in WinXP (sometimes?)
                s.window.destroy()
            except: # TODO: what exception?
                pass
        self.stat_windows = {}
#    also kill any aux windows
        for aux in self.aux_windows:
            aux.destroy()
        self.aux_windows = []

#    def resize_windows(self, *args):
#        for w in self.stat_windows.itervalues():
#            if type(w) == int:
#                continue
#            rel_x = (w.x - self.table.x) * self.table.width  / self.table.oldwidth
#            rel_y = (w.y - self.table.y) * self.table.height / self.table.oldheight
#            w.x = self.table.x + rel_x
#            w.y = self.table.y + rel_y
#            w.window.move(w.x, w.y) 
#
#    def reposition_windows(self, *args):
#        self.update_table_position()
#        for w in self.stat_windows.itervalues():
#            if type(w) == int:
##                print "in reposition, w =", w
#                continue
##            print "in reposition, w =", w, w.x, w.y
#            w.window.move(w.x, w.y)
#        return True

#    def debug_stat_windows(self, *args):
##        print self.table, "\n", self.main_window.window.get_transient_for()
#        for w in self.stat_windows:
#            try:
#                print self.stat_windows[w].window.window.get_transient_for()
#            except AttributeError:
#                print "this window doesnt have get_transient_for"
#
#    def save_layout(self, *args):
#        new_layout = [(0, 0)] * self.max
#        for sw in self.stat_windows:
#            loc = self.stat_windows[sw].window.get_position()
#            new_loc = (loc[0] - self.table.x, loc[1] - self.table.y)
#            new_layout[self.stat_windows[sw].adj - 1] = new_loc
#        self.config.edit_layout(self.table.site, self.max, locations=new_layout)
##    ask each aux to save its layout back to the config object
#        [aux.save_layout() for aux in self.aux_windows]
##    save the config object back to the file
#        print _("Updating config file")
#        self.config.save()


    def save_layout(self, *args):
#    ask each aux to save its layout back to the config object
        [aux.save_layout() for aux in self.aux_windows]
        self.config.save()

    def adj_seats(self, hand, config):
    # determine how to adjust seating arrangements, if a "preferred seat" is set in the hud layout configuration
#        Need range here, not xrange -> need the actual list
        adj = range(0, self.max + 1) # default seat adjustments = no adjustment
#    does the user have a fav_seat?
        if self.site_parameters["fav_seat"][self.max] > 0:
            try:
                fav_seat = self.site_parameters["fav_seat"][self.max]
                actual_seat = self.get_actual_seat(config.supported_sites[self.table.site].screen_name)
                if not actual_seat:
                    log.error(_("Error finding hero seat."))
                    return adj
                for i in xrange(0, self.max + 1):
                    j = actual_seat + i
                    if j > self.max:
                        j = j - self.max
                    adj[j] = fav_seat + i
                    if adj[j] > self.max:
                        adj[j] = adj[j] - self.max
            except Exception, inst:
                log.error(_("Exception in %s") % "Hud.adj_seats")
                log.error("Error:" + (" %s") % inst)           # __str__ allows args to printed directly
        return adj

    def get_actual_seat(self, heroname):
        for key in self.stat_dict:
            if self.stat_dict[key]['screen_name'] == heroname:
                return self.stat_dict[key]['seat']

    def create(self, hand, config, stat_dict, cards):
#    update this hud, to the stats and players as of "hand"
#    hand is the hand id of the most recent hand played at this table
#
#    this method also manages the creating and destruction of stat
#    windows via calls to the Stat_Window class
        self.creation_attrs = hand, config, stat_dict, cards

        self.hand = hand
#        if not self.mw_created:
#            self.create_mw()

        self.stat_dict = stat_dict
        self.cards = cards
        log.info(_('Creating hud from hand ')+str(hand))

    def update(self, hand, config):
        self.hand = hand   # this is the last hand, so it is available later

