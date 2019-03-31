from common import event
import threading
import queue
import enum
import time
import os

import gi
import OpenGL
import OpenGL.GL

import wx
import wx.stc


class Interface(object):

    class CNCWindow(wx.Frame):

        def __reset(self, arg):
            self.reset_clicked()

        def __start(self, arg):
            self.start_clicked()

        def __pause(self, arg):
            self.pause_clicked()

        def __continue(self, arg):
            self.continue_clicked()

        def __stop(self, arg):
            self.stop_clicked()

        def __home(self, arg):
            self.home_clicked()

        def __probe(self, arg):
            self.probe_clicked()

        def __execute(self, arg):
            cmd = self.command.GetValue()
            self.command_entered(cmd)
            self.command.SetValue("")
            self.command.SetFocus()

        def __kd(self, arg):
            keycode = arg.GetKeyCode()
            if keycode == wx.WXK_RETURN or keycode == wx.WXK_NUMPAD_ENTER:
                self.__execute(None)
            arg.Skip()

        def __init__(self, parent):
            self.loaded = event.EventEmitter()
            self.reset_clicked = event.EventEmitter()
            self.start_clicked = event.EventEmitter()
            self.continue_clicked = event.EventEmitter()
            self.pause_clicked = event.EventEmitter()
            self.stop_clicked = event.EventEmitter()
            self.home_clicked = event.EventEmitter()
            self.probe_clicked = event.EventEmitter()
            self.command_entered = event.EventEmitter()

            wx.Frame.__init__(self, parent, title="CNC Control", size=(800,600))
            menubar = wx.MenuBar()
            fileMenu = wx.Menu()
            openItem = fileMenu.Append(wx.ID_OPEN, 'Open', 'Open G-Code')
            quitItem = fileMenu.Append(wx.ID_EXIT, 'Quit', 'Quit application')
            menubar.Append(fileMenu, '&File')
            self.SetMenuBar(menubar)
            self.Bind(wx.EVT_MENU, self.OnQuit, quitItem)
            self.Bind(wx.EVT_MENU, self.OnOpen, openItem)

            panel = wx.Panel(self)
            hbox = wx.BoxSizer(wx.HORIZONTAL)
            panel.SetSizer(hbox)

            #region code area

            code_panel = wx.Panel(panel)
            hbox.Add(code_panel, wx.ID_ANY, wx.EXPAND, 0)
            code_sizer = wx.BoxSizer(wx.VERTICAL)
            code_panel.SetSizer(code_sizer)

            #region code
            self.code = wx.ListCtrl(code_panel, style=wx.LC_REPORT|wx.BORDER_SUNKEN)
            self.code.InsertColumn(0, "", width=32)
            self.code.InsertColumn(1, "", width=500)
            self.font = wx.Font(13, wx.MODERN, wx.NORMAL, wx.NORMAL, False, u'Monospace')
            self.old_hl = None
            code_sizer.Add(self.code, wx.ID_ANY, flag=wx.EXPAND)
            #endregion

            code_sizer.Add((-1, 5))

            #region command
            cmdpanel = wx.Panel(code_panel)
            cmdpanel_sizer = wx.BoxSizer(wx.HORIZONTAL)
            cmdpanel.SetSizer(cmdpanel_sizer)
            code_sizer.Add(cmdpanel, flag=wx.EXPAND)

            self.command = wx.TextCtrl(cmdpanel)
            self.command.Bind(wx.EVT_KEY_DOWN, self.__kd)
            cmdpanel_sizer.Add(self.command, wx.ID_ANY, flag=wx.EXPAND)

            self.send_command = wx.Button(cmdpanel, label='>', size=(32, -1))
            self.send_command.Bind(wx.EVT_BUTTON, self.__execute)
            cmdpanel_sizer.Add(self.send_command)
            #endregion

            #endregion

            #region control area
            control_panel = wx.Panel(panel)
            control_sizer = wx.BoxSizer(wx.VERTICAL)
            control_panel.SetSizer(control_sizer)

            hbox.Add(control_panel, flag=wx.LEFT|wx.RIGHT, border=15)

            #region buttons
            button_panel = wx.Panel(control_panel)
            btnsizer = wx.BoxSizer(wx.VERTICAL)
            control_sizer.Add(button_panel)
            button_panel.SetSizer(btnsizer)

            self.start_btn = wx.Button(button_panel, label='Start')
            btnsizer.Add(self.start_btn)
            self.start_btn.Bind(wx.EVT_BUTTON, self.__start)

            btnsizer.Add((-1, 5))

            self.pause_btn = wx.Button(button_panel, label='Pause')
            btnsizer.Add(self.pause_btn)
            self.pause_btn.Bind(wx.EVT_BUTTON, self.__pause)

            btnsizer.Add((-1, 5))

            self.continue_btn = wx.Button(button_panel, label='Continue')
            btnsizer.Add(self.continue_btn)
            self.continue_btn.Bind(wx.EVT_BUTTON, self.__continue)

            btnsizer.Add((-1, 5))

            self.stop_btn = wx.Button(button_panel, label='Stop')
            btnsizer.Add(self.stop_btn)
            self.stop_btn.Bind(wx.EVT_BUTTON, self.__stop)

            btnsizer.Add((-1, 20))

            self.reset_btn = wx.Button(button_panel, label='Reset')
            self.reset_btn.SetBackgroundColour(wx.Colour(255, 0, 0))
            self.reset_btn.SetForegroundColour(wx.Colour(255, 255, 255))
            self.reset_btn.SetFont(wx.Font(18, wx.DEFAULT, wx.NORMAL, wx.BOLD))
            btnsizer.Add(self.reset_btn)
            self.reset_btn.Bind(wx.EVT_BUTTON, self.__reset)

            btnsizer.Add((-1, 20))


            self.home_btn = wx.Button(button_panel, label='Home XYZ')
            btnsizer.Add(self.home_btn)
            self.home_btn.Bind(wx.EVT_BUTTON, self.__home)

            btnsizer.Add((-1, 5))

            self.probe_btn = wx.Button(button_panel, label='Probe Z')
            btnsizer.Add(self.probe_btn)
            self.probe_btn.Bind(wx.EVT_BUTTON, self.__probe)
            #endregion

            control_sizer.Add((-1, 15))

            #region status region
            status_panel = wx.Panel(control_panel)
            status_sizer = wx.BoxSizer(wx.VERTICAL)
            control_sizer.Add(status_panel)
            status_panel.SetSizer(status_sizer)
            #endregion

            #endregion

        def ClearCode(self):
            self.code.DeleteAllItems()

        def AddCode(self, line):
            id = self.code.GetItemCount()
            self.code.InsertItem(id, str(id+1))
            self.code.SetItem(id, 1, line)
            self.code.SetItemFont(id, self.font)
            return id

        def HighLightLine(self, id):
            if self.old_hl != None and self.old_hl < self.code.GetItemCount():
                self.code.SetItemBackgroundColour(self.old_hl, wx.WHITE)
            self.code.SetItemBackgroundColour(id, wx.LIGHT_GREY)
            self.old_hl = id


        def OnOpen(self, e):
            with wx.FileDialog(self, "Open G-Code", wildcard="GCODE files (*.gcode)|*.gcode|All files|*", \
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as ofd:
                if ofd.ShowModal() == wx.ID_CANCEL:
                    return
                file = ofd.Paths[0]
                self.loaded(file)

        def OnQuit(self, e):
            self.Close()


    def __init__(self):
        self.app = wx.App()
        self.window = self.CNCWindow(None)

        self.load_file = self.window.loaded
        self.reset_clicked = self.window.reset_clicked
        self.start_clicked = self.window.start_clicked
        self.continue_clicked = self.window.continue_clicked
        self.pause_clicked = self.window.pause_clicked
        self.stop_clicked = self.window.stop_clicked
        self.home_clicked = self.window.home_clicked
        self.probe_clicked = self.window.probe_clicked
        self.command_entered = self.window.command_entered

        self.window.Show(True)
        self.clear_commands()

    def clear_commands(self):
        self.id = 0
        self.window.ClearCode()

    def add_command(self, line):
        self.id = self.window.AddCode(line)

    def show_ok(self, text):
        wx.MessageBox(text, 'Message', wx.OK | wx.ICON_INFORMATION)

    def select_line(self, line):
        self.window.HighLightLine(line)

    def switch_to_initial_mode(self):
        self.window.start_btn.Enable()
        self.window.continue_btn.Disable()
        self.window.stop_btn.Disable()
        self.window.pause_btn.Disable()
        self.window.home_btn.Enable()
        self.window.probe_btn.Enable()
        self.window.command.Enable()
        self.window.send_command.Enable()
        self.window.command.SetFocus()

    def switch_to_paused_mode(self):
        self.window.start_btn.Disable()
        self.window.continue_btn.Enable()
        self.window.stop_btn.Enable()
        self.window.pause_btn.Disable()
        self.window.home_btn.Disable()
        self.window.probe_btn.Disable()
        self.window.command.Disable()
        self.window.send_command.Disable()
        self.window.command.SetFocus()

    def switch_to_running_mode(self):
        self.window.start_btn.Disable()
        self.window.continue_btn.Disable()
        self.window.stop_btn.Disable()
        self.window.pause_btn.Disable()
        self.window.home_btn.Disable()
        self.window.probe_btn.Disable()
        self.window.command.Disable()
        self.window.send_command.Disable()

    def run(self):
        self.app.MainLoop()
