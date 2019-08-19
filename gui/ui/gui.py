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
import wx.grid


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

        def __xp(self, arg):
            self.xp_clicked()
        def __xm(self, arg):
            self.xm_clicked()

        def __yp(self, arg):
            self.yp_clicked()
        def __ym(self, arg):
            self.ym_clicked()

        def __zp(self, arg):
            self.zp_clicked()
        def __zm(self, arg):
            self.zm_clicked()

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

            self.xp_clicked = event.EventEmitter()
            self.xm_clicked = event.EventEmitter()

            self.yp_clicked = event.EventEmitter()
            self.ym_clicked = event.EventEmitter()

            self.zp_clicked = event.EventEmitter()
            self.zm_clicked = event.EventEmitter()

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

            #region code
            self.cmdhist = wx.TextCtrl(code_panel, style=wx.TE_MULTILINE | wx.TE_READONLY | wx.HSCROLL | wx.TE_RICH)
            code_sizer.Add(self.cmdhist, wx.ID_ANY, flag=wx.EXPAND)
            #endregion

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

            vcmdpanel = wx.Panel(control_panel)
            control_sizer.Add(vcmdpanel)
            vcmdsizer = wx.BoxSizer(wx.HORIZONTAL)
            vcmdpanel.SetSizer(vcmdsizer)

            #region move control

            movegrid = wx.Panel(vcmdpanel)
            vcmdsizer.Add(movegrid)
            
            movegridsizer = wx.GridBagSizer(vgap=5, hgap=5)
            movegrid.SetSizer(movegridsizer)

            self.xp = wx.Button(movegrid, label=">")
            movegridsizer.Add(self.xp, (1, 2))
            self.xp.Bind(wx.EVT_BUTTON, self.__xp)
            
            self.xm = wx.Button(movegrid, label="<")
            movegridsizer.Add(self.xm, (1, 0))
            self.xm.Bind(wx.EVT_BUTTON, self.__xm)
            
            self.yp = wx.Button(movegrid, label="^")
            movegridsizer.Add(self.yp, (0, 1))
            self.yp.Bind(wx.EVT_BUTTON, self.__yp)

            self.ym = wx.Button(movegrid, label="v")
            movegridsizer.Add(self.ym, (2, 1))
            self.ym.Bind(wx.EVT_BUTTON, self.__ym)
                        
            self.zp = wx.Button(movegrid, label="Up")
            movegridsizer.Add(self.zp, (3, 1))
            self.zp.Bind(wx.EVT_BUTTON, self.__zp)

            self.zm = wx.Button(movegrid, label="Down")
            movegridsizer.Add(self.zm, (4, 1))
            self.zm.Bind(wx.EVT_BUTTON, self.__zm)
            #endregion move control

            vcmdsizer.Add((10, -1))

            #region buttons
            button_panel = wx.Panel(vcmdpanel)
            btnsizer = wx.BoxSizer(wx.VERTICAL)
            vcmdsizer.Add(button_panel)
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

            lb = wx.StaticText(status_panel, label="Coordinates")
            status_sizer.Add(lb)
            
            self.crds = wx.grid.Grid(status_panel)
            status_sizer.Add(self.crds)
            self.crds.CreateGrid(4, 3)
            for i in range(3):
                for j in range(3):
                    self.crds.SetReadOnly(i, j, True)

            self.crds.SetColLabelValue(0, "HW")
            self.crds.SetColLabelValue(1, "Global")
            self.crds.SetColLabelValue(2, "Current")
            
            self.crds.SetRowLabelValue(0, "CS")
            self.crds.SetRowLabelValue(1, "X")
            self.crds.SetRowLabelValue(2, "Y")
            self.crds.SetRowLabelValue(3, "Z")

            self.crds.DisableRowResize(0)
            self.crds.DisableRowResize(1)
            self.crds.DisableRowResize(2)
            self.crds.DisableRowResize(3)
            
            self.crds.DisableColResize(0)
            self.crds.DisableColResize(1)
            self.crds.DisableColResize(2)

            self.crds.SetCellBackgroundColour(0, 0, wx.Colour("lightgrey"))
            self.crds.SetCellBackgroundColour(0, 1, wx.Colour("lightgrey"))
            #endregion

            #endregion

        def SetCrds(self, hw, glob, loc, cs):
            self.crds.SetCellValue(0, 2, str(cs))
            for i in range(3):
                self.crds.SetCellValue(i+1, 0, "%0.4f" % hw[i])
                self.crds.SetCellValue(i+1, 1, "%0.4f" % glob[i])
                self.crds.SetCellValue(i+1, 2, "%0.4f" % loc[i])

        def ClearCode(self):
            self.code.DeleteAllItems()

        def AddCode(self, line):
            id = self.code.GetItemCount()
            self.code.InsertItem(id, str(id+1))
            self.code.SetItem(id, 1, line)
            self.code.SetItemFont(id, self.font)
            return id

        def HighLightLine(self, id):
            print("select line", id)
            try:
                if self.old_hl != None and self.old_hl < self.code.GetItemCount():
                    self.code.SetItemBackgroundColour(self.old_hl, wx.WHITE)
                self.code.SetItemBackgroundColour(id, wx.LIGHT_GREY)
                self.old_hl = id
            except:
                pass

        def OnOpen(self, e):
            with wx.FileDialog(self, "Open G-Code", wildcard="GCODE files (*.gcode)|*.gcode|All files|*", \
                       style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST) as ofd:
                if ofd.ShowModal() == wx.ID_CANCEL:
                    return
                file = ofd.Paths[0]
                self.loaded(file)

        def OnQuit(self, e):
            self.Close()
        
        def AddHistory(self, cmd):
            self.cmdhist.AppendText(cmd)

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

        self.xp_clicked = self.window.xp_clicked
        self.xm_clicked = self.window.xm_clicked
        self.yp_clicked = self.window.yp_clicked
        self.ym_clicked = self.window.ym_clicked
        self.zp_clicked = self.window.zp_clicked
        self.zm_clicked = self.window.zm_clicked

        self.window.Show(True)
        self.clear_commands()

        self.command_entered += self.__on_command_entered

    def __on_command_entered(self, cmd):
        self.window.AddHistory(cmd + "\n")

    def clear_commands(self):
        self.id = 0
        self.window.ClearCode()

    def add_command(self, line):
        self.id = self.window.AddCode(line)

    def show_ok(self, text):
        wx.MessageBox(text, 'Message', wx.OK | wx.ICON_INFORMATION)

    def select_line(self, line):
        self.window.HighLightLine(line)

    def set_coordinates(self, hw, glob, loc, cs):
        self.window.SetCrds(hw, glob, loc, cs)

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
        self.window.xp.Enable()
        self.window.xm.Enable()
        self.window.yp.Enable()
        self.window.ym.Enable()
        self.window.zp.Enable()
        self.window.zm.Enable()

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
        self.window.xp.Enable()
        self.window.xm.Enable()
        self.window.yp.Enable()
        self.window.ym.Enable()
        self.window.zp.Enable()
        self.window.zm.Enable()

    def switch_to_running_mode(self):
        self.window.start_btn.Disable()
        self.window.continue_btn.Disable()
        self.window.stop_btn.Disable()
        self.window.pause_btn.Disable()
        self.window.home_btn.Disable()
        self.window.probe_btn.Disable()
        self.window.command.Disable()
        self.window.send_command.Disable()
        self.window.xp.Disable()
        self.window.xm.Disable()
        self.window.yp.Disable()
        self.window.ym.Disable()
        self.window.zp.Disable()
        self.window.zm.Disable()
        

    def run(self):
        self.app.MainLoop()
