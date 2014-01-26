#!/usr/bin/env python
# *-* coding:UTF-8 *-*
#
#  ShuffleX.py
#
#       Young Geng, Rahul Verma and Angela Lin
#       based on pymusic by Stephen Smally
#
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 3 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.
#       


'''Simple Music Player with machine learning shuffle written in pygtk using gstreamer'''

import gtk
import gst
import os
import shelve
from time import localtime, mktime
from random import randint

def clock():
    return mktime(localtime())

global userhome
userhome = os.getenv("HOME")

global theme
theme = '''
style "notebook"
{
    bg[NORMAL] = @bg_color
    bg[ACTIVE] = @bg_color
    engine "murrine"
    {
        roundness = 0
    }
}
style "separator"
{
    engine "murrine"
    {
        separatorstyle = 0
    }
}
class "GtkNotebook" style "notebook"
class "GtkSeparator" style "separator"
'''


class PyMusicView(gtk.Window):
    def __init__(self):
        '''Setting up the view'''
        super(PyMusicView, self).__init__()
        self.set_title("PyMusic")
        gtk.rc_parse_string(theme)
        try:
            self.set_icon_from_file("/usr/share/pixmaps/pymusic.png")
        except: pass
        self.set_position(gtk.WIN_POS_CENTER)
        self.set_default_size(800, 500)
        self.realize()
        self.window_style = self.get_style()
        self.add_widgets()
        self.show_all()
        self.separator.set_visible(False)
        self.previous.set_sensitive(False)
        self.next.set_sensitive(False)
        self.play_pause.set_sensitive(False)
        self.active_song.set_sensitive(False)
        self.search_tool.set_sensitive(False)
        self.bookmarks_workaround.set_visible(False)


    def create_toolbar(self):
        self.refresh = gtk.ToolButton(gtk.STOCK_REFRESH)
        self.refresh.set_tooltip_text("Refresh Songs/Artists lists")
        self.add_fold = gtk.ToolButton(gtk.STOCK_ADD)
        self.add_fold.set_tooltip_text("Add a folder containg music")
        self.previous = gtk.ToolButton(gtk.STOCK_MEDIA_PREVIOUS)
        self.previous.set_tooltip_text("Previous song")
        self.play_pause = gtk.ToolButton(gtk.STOCK_MEDIA_PLAY)
        self.play_pause.set_tooltip_text("Play or stop the song")
        self.next = gtk.ToolButton(gtk.STOCK_MEDIA_NEXT)
        self.next.set_tooltip_text("Next song")
        self.search_entry = gtk.Entry()
        self.search_entry.set_icon_from_stock(1, gtk.STOCK_CLEAR)
        self.search_entry.set_tooltip_text("Search a song")
        self.search_tool = gtk.ToolItem()
        self.search_entry.set_size_request(170, 27)
        self.search_tool.add(self.search_entry)
        self.active_song = gtk.Label("Title - Artist - Album")
        self.active_song.set_tooltip_text("Current song (Title - Artist - Album)")
        self.active_song_cont = gtk.ToolItem()
        self.active_song_cont.add(self.active_song)
        self.active_song_cont.set_expand(True)
        self.main_toolbar = gtk.Toolbar()
        self.main_toolbar.insert(self.search_tool, 0)
        self.main_toolbar.insert(self.active_song_cont, 0)
        self.main_toolbar.insert(self.next, 0)
        self.main_toolbar.insert(self.play_pause, 0)
        self.main_toolbar.insert(self.previous, 0)
        self.main_toolbar.insert(self.add_fold, 0)
        self.main_toolbar.insert(self.refresh, 0)
        return self.main_toolbar
    
    def create_song_list(self):
        self.song_store = gtk.ListStore(str, str, str)
        self.song_list = gtk.TreeView(self.song_store)
        self.title_renderer = gtk.CellRendererText()
        self.title_column = gtk.TreeViewColumn("Title", self.title_renderer)
        self.title_column.add_attribute(self.title_renderer, "text", 0)
        self.title_column.set_resizable(True)
        self.title_column.set_expand(True)
        self.song_list.append_column(self.title_column)
        self.artist_renderer = gtk.CellRendererText()
        self.artist_column = gtk.TreeViewColumn("Artist", self.artist_renderer)
        self.artist_column.add_attribute(self.artist_renderer, "text", 1)
        self.artist_column.set_resizable(True)
        self.artist_column.set_expand(True)
        self.song_list.append_column(self.artist_column)
        self.album_renderer = gtk.CellRendererText()
        self.album_column = gtk.TreeViewColumn("Album", self.album_renderer)
        self.album_column.add_attribute(self.album_renderer, "text", 2)
        self.album_column.set_resizable(True)
        self.album_column.set_expand(True)
        self.song_list.append_column(self.album_column)
        self.song_list.set_search_entry(self.search_entry)
        self.song_list.set_rules_hint(True)
        self.song_list.set_expander_column(self.title_column)
        self.song_cont = gtk.ScrolledWindow()
        self.song_cont.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.song_cont.add(self.song_list)
        return self.song_cont
    
    def create_artist_list(self):
        self.artist_store = gtk.TreeStore(str)
        self.artist_list = gtk.TreeView(self.artist_store)
        self.artist_list_renderer = gtk.CellRendererText()
        self.artist_list_column = gtk.TreeViewColumn("Artist", self.artist_list_renderer)
        self.artist_list_column.add_attribute(self.artist_list_renderer, "text", 0)
        self.artist_list.append_column(self.artist_list_column)
        self.artist_list.set_rules_hint(True)
        self.artist_cont = gtk.ScrolledWindow()
        self.artist_cont.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        self.artist_cont.add(self.artist_list)
        return self.artist_cont
    
    def create_start_diag(self):
        self.start_diag = gtk.Fixed()
        self.start_label = gtk.Label("Your Music folder")
        self.start_entry = gtk.combo_box_entry_new_text()
        self.start_entry.set_size_request(220, 27)
        self.start_button = gtk.Button("Import Music")
        self.start_diag.put(self.start_label, 350, 150)
        self.start_diag.put(self.start_entry, 290, 175)
        self.start_diag.put(self.start_button, 355, 208)
        return self.start_diag
    
    def create_misc(self):
        self.songs_count = gtk.Label("Songs")
        self.separator = gtk.VSeparator()
    
    def create_bookmarks(self):
        self.bookmarks_store = gtk.ListStore(str, str, gtk.gdk.Color)
        self.bookmarks_list = gtk.TreeView(self.bookmarks_store)
        self.bookmarks_renderer = gtk.CellRendererPixbuf()
        self.bookmarks_text = gtk.CellRendererText()
        self.bookmarks_column = gtk.TreeViewColumn()
        self.bookmarks_column.pack_start(self.bookmarks_renderer, False)
        self.bookmarks_column.pack_start(self.bookmarks_text, False)
        self.bookmarks_column.add_attribute(self.bookmarks_renderer, "icon-name", 0)
        self.bookmarks_column.add_attribute(self.bookmarks_renderer, "cell-background-gdk", 2)
        self.bookmarks_column.add_attribute(self.bookmarks_text, "text", 1)
        self.bookmarks_column.add_attribute(self.bookmarks_text, "cell-background-gdk", 2)
        for items in [["folder-music", "Songs"], ["stock_person", "Artists"]]:
            self.bookmarks_store.append([items[0], items[1], self.window_style.lookup_color("bg_color")])
        self.bookmarks_list.set_headers_visible(False)
        self.bookmarks_list.append_column(self.bookmarks_column)
        self.bookmarks_workaround = gtk.VBox()
        self.bookmarks_workaround.pack_start(self.bookmarks_list, False)
        self.bookmarks_workaround.set_border_width(5)
        return self.bookmarks_workaround
    
    def add_widgets(self):
        self.create_misc()
        self.main_vbox = gtk.VBox()
        self.main_hbox = gtk.HBox()
        self.main_vbox.pack_start(self.create_toolbar(), False)
        self.var_cont = gtk.Notebook()
        self.var_cont.set_show_tabs(False)
        self.var_cont.set_show_border(False)
        self.main_vbox.pack_start(self.main_hbox)
        self.main_hbox.pack_start(self.create_bookmarks(), False)
        self.main_hbox.pack_start(self.separator, False)
        self.main_hbox.pack_start(self.var_cont)
        self.var_cont.append_page(self.create_start_diag())
        self.var_cont.append_page(self.create_song_list())
        self.var_cont.append_page(self.create_artist_list())
        self.main_vbox.pack_start(gtk.HSeparator(), False)
        self.main_vbox.pack_start(self.songs_count, False)
        self.add(self.main_vbox)

#-------------------------------------------------------------
#
#-------------------------------------------------------------

class PyMusicControl:
    def __init__(self):
        '''Setting up the Player'''
        self.view = PyMusicView()
        self.settings = shelve.open("/".join([userhome, "pymusic.conf"]), writeback=True)
        for items in self.settings.keys():
            self.view.start_entry.append_text(items)
        #-----------------------------------------------------
        self.player = gst.element_factory_make("playbin2", "PyMusic player")
        self.sink = gst.element_factory_make("autoaudiosink", "PyMusic Output")
        self.videosink= gst.element_factory_make("fakesink", "PyMusic fake Output")
        self.player.set_property("video-sink", self.videosink)
        self.player.set_property("audio-sink", self.sink)
        self.player_bus = self.player.get_bus()
        self.player_bus.add_signal_watch()
        #-----------------------------------------------------
        self.player_bus.connect("message", self.On_messages)
        self.view.start_button.connect("clicked", self.startup_collection)
        self.view.refresh.connect("clicked", lambda w: self.work_library())
        self.view.add_fold.connect("clicked", self.On_add_music)
        self.view.song_list.connect("row-activated", self.On_activated)
        self.view.play_pause.connect("clicked", self.On_media_button)
        self.view.next.connect("clicked", self.On_next)
        self.view.previous.connect("clicked", self.On_previous)
        self.view.search_entry.connect("icon-press", lambda w, p, o: self.view.search_entry.set_text(""))
        self.view.bookmarks_list.connect("cursor-changed", lambda widget: self.select(widget.get_selection().get_selected_rows()[1][0][0]))
        self.view.connect("size-allocate", self.On_refresh)
        self.view.connect("destroy", self.On_exit)
        #-----------------------------------------------------
        #FIXME: Initialize the last song mark
        self.last_song = None
    
    def startup_collection(self, widget):
        self.folder = self.view.start_entry.child.get_text()
        self.view.song_store.clear()
        self.view.artist_store.clear()
        if os.path.exists(self.folder):
            if not os.path.exists("/".join([self.folder, "/.library.db"])):
                print("Creating a new library...")
                self.create_lib()
            print("using the library...")
            self.work_library()
        else:
            self.view.songs_count.set_text("Can't find the folder!")
    
    def work_library(self):
        self.settings[self.folder] = "/".join([self.folder, ".library.db"])
        self.file_lib = shelve.open("/".join([self.folder, ".library.db"]), writeback=True)
        self.file_lib_keys = sorted(self.file_lib.keys())
        for items in self.file_lib_keys:
            self.view.song_store.append([
            self.file_lib[items][0],
            self.file_lib[items][1],
            self.file_lib[items][2]
            ])
        self.artist_dict = []
        self.album_dict = []
        for items in self.file_lib_keys:
            if not self.file_lib[items][1] in self.artist_dict:
                self.artist_dict.append(self.file_lib[items][1])
        for items in self.artist_dict:
            self.parent = self.view.artist_store.append(None, [items])
            for item in self.file_lib_keys:
                if self.file_lib[item][1] == items:
                    if not self.file_lib[item][2] in self.album_dict:
                        self.view.artist_store.append(self.parent, [self.file_lib[item][2]])
                        self.album_dict.append(self.file_lib[item][2])
        self.view.songs_count.set_text(" ".join([str(len(self.file_lib_keys)), "songs"]))
        self.view.bookmarks_workaround.set_visible(True)
        self.view.var_cont.set_page(1)
        self.view.separator.set_visible(True)
        self.view.previous.set_sensitive(True)
        self.view.next.set_sensitive(True)
        self.view.play_pause.set_sensitive(True)
        self.view.active_song.set_sensitive(True)
        self.view.search_tool.set_sensitive(True)
        self.select(0)
        #FIXME
        #Initialize the graph size
        self.graph = SongGrid(len(self.view.song_store)) 
        
    def create_lib(self):
        '''set up the collection'''
        import mutagen.mp3
        self.files = []
        self.file_lib = shelve.open("/".join([self.folder, ".library.db"]), writeback=True)
        for files in os.walk(self.folder):
            for item in files[2]:
                self.file = "/".join([files[0], item])
                if os.path.exists(self.file):
                    if item.split(".")[-1] in ["mp3", "ogg"]:
                        self.files.append(self.file)
        #-----------------------------------------------------
        for items in self.files:
            self.media = mutagen.mp3.Open(items)
            try:
                self.file_lib[items] = [
                str(self.media["TIT2"]),
                str(self.media["TPE1"]),
                str(self.media["TALB"])
                ]
            except KeyError:
                self.file_lib[items] = [
                items.split("/")[-1],
                "Unknown Artist",
                "Unknown Album"
                ]
        #-----------------------------------------------------
        self.file_lib.close()

    def On_messages(self, bus, message):
        if message.type == gst.MESSAGE_EOS:
            #FIXME: Update graph
            self.graph.update(self.to_play, self.last_song, -1)
            self.last_song = self.to_play

            #FIXME: Add shuffle
            """
            self.to_play += 1
            """
            self.to_play = shuffle(self.graph.get_shortest_path(self.to_play), self.to_play)
            self.On_play()
        elif message.type == gst.MESSAGE_ERROR:
            print(message)
        else:
            pass

    def On_media_button(self, widget):
        if widget.get_stock_id() == gtk.STOCK_MEDIA_PLAY:
            widget.set_stock_id(gtk.STOCK_MEDIA_STOP)
            self.On_play()
        #-----------------------------------------------------
        elif widget.get_stock_id() == gtk.STOCK_MEDIA_STOP:
            widget.set_stock_id(gtk.STOCK_MEDIA_PLAY)
            self.player.set_state(gst.STATE_READY)

    def On_play(self):
        '''Play or stop the song'''
        self.player.set_state(gst.STATE_READY)
        self.song_start_time = clock()
        try:
            self.file = self.file_lib_keys[self.to_play]
        except AttributeError:
            self.file = self.file_lib_keys[0]
        self.view.active_song.set_text(" - ".join([self.file_lib[self.file][0], self.file_lib[self.file][1], self.file_lib[self.file][2]]))
        self.player.set_property("uri", "file://"+self.file)
        self.player.set_state(gst.STATE_PLAYING)
        self.view.play_pause.set_stock_id(gtk.STOCK_MEDIA_STOP)
        
    def On_activated(self, widget, path, view):
        self.to_play = path[0]
        self.On_play()

    def On_next(self, widget):
        #FIXME: Update the graph
        if clock() - self.song_start_time > 30:
            self.graph.update(self.last_song, self.to_play, -1)
        else:
            self.graph.update(self.last_song, self.to_play, 1)
        self.last_song = self.to_play

        #FIXME: Add shuffle
        """
        if self.to_play != len(self.view.song_store)-1:
            self.to_play += 1
        """
        self.to_play = shuffle(self.graph.get_shortest_path(self.to_play), self.to_play)
        self.On_play()
        
    def On_previous(self, widget):
        if self.to_play != 0:
            self.to_play -= 1
        self.On_play()

    def On_new_search(self, widget):
        self.view.song_list.set_search_column(widget.get_active())

    def On_refresh(self, widget, rec):
        self.size = widget.get_size()[0]/3
        self.view.title_column.set_max_width(self.size)
        self.view.artist_column.set_max_width(self.size)
        self.view.album_column.set_max_width(self.size)

    def select(self, selection):
        if selection == 0:
            self.view.var_cont.set_page(1)
        elif selection == 1:
            self.view.var_cont.set_page(2)
        elif selection == 2:
            self.view.var_cont.set_page(3)

    def On_add_music(self, widget):
        self.view.var_cont.set_page(0)
        self.view.separator.set_visible(False)
        self.view.bookmarks_workaround.set_visible(False)
    
    def On_exit(self, root):
        print("The window %s is going to quit" % root)
        self.player.set_state(gst.STATE_NULL)
        try:
            self.file_lib.close()
        except: pass
        self.settings.close()
        gtk.main_quit()


class SongGrid:
    song_array = []
    shortest_path = []
    count = 0

    def __init__(self, array_size):
        self.array_size = array_size
        self.song_array = [0 for i in range(array_size)]
        self.shortest_path = [0 for i in range(array_size)]
        for i in range(array_size):
            self.song_array[i] = [20 for _ in range(array_size)]
            self.shortest_path[i] = [20 for _ in range(array_size)]

    def set_relationship(self, x, y, new_value=200):
        self.song_array[x][y], self.song_array[y][x] = new_value, new_value

    def update(self, x, y, change_in_affinity):
        if x != None and 5 < self.song_array[x][y] < 35:
            self.song_array[x][y] += change_in_affinity
            self.song_array[y][x] += change_in_affinity

    def calculate_shortest_path(self):
        n = self.array_size
        for i in range(n):
            for j in range(n):
                self.shortest_path[i][j] = self.song_array[i][j]
        for i in range(n):
            for j in range(n):
                for k in range(n):
                        if self.shortest_path[i][k] + self.shortest_path[k][j] < self.shortest_path[i][j]:
                            self.shortest_path[i][j] = self.shortest_path[i][k] + self.shortest_path[k][j]
        



    def get_path_length_between(self, x, y):
        return self.song_array[x][y]



    def get_shortest_path(self, i):
        if self.count >= 5:
            self.calculate_shortest_path()
            self.count = 0
        else:
            self.count += 1
        return [self.shortest_path[i][j] for j in range(len(self.shortest_path[i]))]


def shuffle(shortest_path, cur):
    #FIXME: Implement the shuffle function
    maxi = max(shortest_path)
    mini = min(shortest_path)
    x = [maxi - i + mini for i in shortest_path]
    x[cur] = 0
    s = 0
    r = randint(1, sum(x))
    for i in range(len(x)):
        s = s + x[i]
        if s >= r:
            return i

        
        







if __name__ == "__main__":
    app = PyMusicControl()
    gtk.main()
