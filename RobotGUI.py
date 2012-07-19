import wx
import wx.grid as gridlib
from wxPython.wx import *
from wxPython.lib.dialogs import *
import threading

import shared
import GUI_helpers as gui_h
import sys, time, traceback
from basestation_stream import BasestationStream
from asynch_dispatch import *
from optitrak_stream import OptitrakStream
from or_helpers_stream import HelpersStream

from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg
from matplotlib.backends.backend_wx import NavigationToolbar2Wx

from matplotlib.figure import Figure

class GUIStream(threading.Thread):
	def __init__(self, frameClass=None, title='SkyNet', callbacks=None, sinks=None, autoStart=True):
		threading.Thread.__init__(self)
		self.daemon = True
    
		self.frameClass = wx.Frame

		self.title = title
		global dispatcher
		dispatcher = AsynchDispatch(sinks=sinks, callbacks = callbacks)
 
		self.start()

	def run(self):
		self.app = wx.App()
		self.frame = ThreadedFrame(self.title, self.frameClass)
		self.frame.Show(True)
		self.app.MainLoop()

	def put(self, data):
		self.dispatcher.put(message)
  
	def add_sinks(self,sinks):
		self.dispatcher.add_sinks(sinks)

class threadedRunCommands(threading.Thread):
	def __init__(self, move, addr):
		threading.Thread.__init__(self)
		self.daemon = True
		self.move = move
		self.addr = addr

		self.start()

	def run(self):
		steeringGains = [0,0,0,0,0,0] # Disables steering controller
		dispatcher.dispatch(Message('imu_samples', self.move))
		dispatcher.dispatch(Message('steer_rate', [self.addr,0]))
		dispatcher.dispatch(Message('steer_gains',[self.addr, steeringGains]))
		dispatcher.dispatch(Message('erase_flash',self.addr))
		dispatcher.dispatch(Message('save_telem', self.addr))
#		dispatcher.dispatch(Message('stream_telem', self.addr ))
		dispatcher.dispatch(Message('move', [self.addr, self.move]))
		dispatcher.dispatch(Message('read_telem', self.addr))

#The main page of the program
class PageOne(wx.Panel):
	def __init__(self,parent): 
		wx.Panel.__init__(self,parent)
		
		self.left_throt = 0
		self.right_throt = 0
		
		#defining all the sizers
		sizer = wx.GridBagSizer()
		tbs1 = wx.BoxSizer(wx.HORIZONTAL)		
		tbs3 = wx.BoxSizer(wx.VERTICAL)
		tbsGridSize = wx.GridBagSizer()
		mbs = wx.BoxSizer(wx.HORIZONTAL)
		bbs1 = wx.BoxSizer(wx.HORIZONTAL)
		cbs = wx.BoxSizer(wx.VERTICAL)
		bbs2 = wx.BoxSizer(wx.HORIZONTAL)
	
		#label for robot selector
		self.roboSelectLabel = wx.StaticText(self,label = "Select Robot:")
		tbs1.Add(self.roboSelectLabel, 1, wx.EXPAND, 5)
	
		#selector for arbitrary number of robots
		self.roboSelect=wx.ListBox(self,style=wx.LB_SINGLE,size=(-1,-1), name = 'Robot Selector')
		self.roboSelect.Append("x3002")
		self.roboSelect.Append("2")
		self.roboSelect.Append("3")
		self.roboSelect.Append("4")
		self.robotSelect.Append("xffff")
		tbs1.Add(self.roboSelect,2, wx.GROW|wx.ALL,5)
		self.Bind(wx.EVT_LISTBOX, self.OnSelect, self.roboSelect)

		#emergency stop button
		self.eStop = wx.Button(self,-1,label="E STOP!")
		self.eStop.SetBackgroundColour("red")
		tbsGridSize.Add(self.eStop,(1,0))
		self.Bind(wx.EVT_BUTTON, self.emergencyStopButtonClick, self.eStop)

		#Forward Button
		self.sB = wx.Button(self, -1, label = "Forward")
		tbsGridSize.Add(self.sB, (1,1))
		self.Bind(wx.EVT_BUTTON, self.forwardButtonClick, self.sB)
		
		self.straightB = wx.Button(self, -1, label = "Straight")
		tbsGridSize.Add(self.straightB, (1,2))
		self.Bind(wx.EVT_BUTTON, self.straightButtonClick, self.straightB)

		#Left Button
		self.lB = wx.Button(self, -1, label = "Left")
		tbsGridSize.Add(self.lB, (2,0))
		self.Bind(wx.EVT_BUTTON, self.leftButtonClick, self.lB)
		
		#Right Button
		self.rB = wx.Button(self, -1, label="Right")
		tbsGridSize.Add(self.rB, (2,2))
		self.Bind(wx.EVT_BUTTON, self.rightButtonClick, self.rB)

		#Slow Button
		self.slowB = wx.Button(self, -1, label="Slow")
		tbsGridSize.Add(self.slowB, (2,1))
		self.Bind(wx.EVT_BUTTON, self.slowButtonClick, self.slowB)

		#text area for output data
		self.outputData = wx.TextCtrl(self, size=(300,100),style = wx.TE_MULTILINE|wx.TE_READONLY
									  |wx.HSCROLL|wx.TE_RICH2)
		self.outputData.WriteText("This Displays ouput data...\n")
		tbs3.Add(self.outputData,1,wx.GROW|wx.ALL,5)
		tbs1.Add(tbs3,6,wx.EXPAND,5)

		#Redirecting sys.out to text field
		redir=RedirectText(self.outputData)
		sys.stdout=redir
		sys.sterr=redir

		#excel cloned grid table
		self.inputGrid = simpleGrid(self)
		bbs1.Add(self.inputGrid, 1, wx.EXPAND,1)
		
		#key for commands
		self.commandKey = wx.StaticText(self, label = "")
		self.commandKey.SetLabel("MOVE_SEG_CONSTANT = 0 \n" +
								 "MOVE_SEG_RAMP = 1 \n" +
								 "MOVE_SEG_SIN = 2 \n" +
								 "MOVE_SEG_TRI = 3 \n" +
								 "MOVE_SEG_SAW = 4 \n" +
								 "MOVE_SEG_IDLE = 5")
		bbs1.Add(self.commandKey, 2, wx.EXPAND, 1)

		#visual indication of commands
		self.reset_status = wx.StaticText(self, label = "RESET")
		cbs.Add(self.reset_status, 1, wx.EXPAND,1)
		
		self.steer_rate_status = wx.StaticText(self, label = "Steering Rate")
		cbs.Add(self.steer_rate_status, 2, wx.EXPAND,1)

		self.motor_gains_status = wx.StaticText(self, label = "Motor Gains")
		cbs.Add(self.motor_gains_status,3,wx.EXPAND,1)

		self.steer_gains_status = wx.StaticText(self,label="Steering Gains")
		cbs.Add(self.steer_gains_status,4,wx.EXPAND,1)

		#Run Button
		self.runCom = wx.Button(self,-1,label="Run Commands")
		self.Bind(wx.EVT_BUTTON,self.runComButtonClick,self.runCom)
		bbs2.Add(self.runCom,1,wx.ALL,5)
		
		#Presets Button
		self.loadPre = wx.Button(self, -1, label="Load Presets")
		self.Bind(wx.EVT_BUTTON, self.loadPreButtonClick, self.loadPre)
		bbs2.Add(self.loadPre,2,wx.ALL,5)
	
		#Save Data Button
		self.saveData = wx.CheckBox(self, -1, label = "Save Data")
		self.Bind(wx.EVT_CHECKBOX, self.saveDataButtonClick, self.saveData)
		bbs2.Add(self.saveData,3,wx.ALL,5)
		
		#add a row button
		self.addRow = wx.Button(self,-1,label="Add Row")
		self.Bind(wx.EVT_BUTTON,self.addButtonClick,self.addRow)
		mbs.Add(self.addRow,1,wx.ALL,5)
	
		#delete a row button
		self.delRow = wx.Button(self,-1,label='Delete Row')
		self.Bind(wx.EVT_BUTTON,self.delButtonClick,self.delRow)
		mbs.Add(self.delRow,2,wx.ALL,5)

		#reset grid button
		self.resGrid = wx.Button(self,-1,label="Reset Grid")
		self.Bind(wx.EVT_BUTTON,self.resRowButtonClick,self.resGrid)
		mbs.Add(self.resGrid,3,wx.ALL,1)

		tbs1.Add(tbsGridSize,3,wx.EXPAND,5)
		bbs2.Add(cbs,4,wx.EXPAND,1)

		#adding all the sizers to the panel; layout of the panel
		sizer.Add(tbs1,(0,0))
		sizer.Add(mbs,(2,0))
		sizer.Add(bbs1,(3,0))
		sizer.Add(bbs2,(4,0))

		#Formats sizers to resize when resizing the window
		sizer.AddGrowableCol(0)
		self.SetSizerAndFit(sizer)
		self.SetSizeHints(-1,self.GetSize().y,-1,self.GetSize().y);
		self.Show(True)

	#defining what the buttons actually do, can possibly put as a sink to another stream
	def forwardButtonClick(self,e):
		self.right_throt = self.right_throt + 20
		self.left_throt = self.left_throt + 20
		dispatcher.dispatch(Message('throt_speed', [self.addr, self.left_throt, self.right_throt]))

	def straightButtonClick(self,e):
		self.right_throt = 20
		self.left_throt = 20
		dispatcher.dispatch(Message('throt_speed', [self.addr, self.left_throt, self.right_throt]))

	def slowButtonClick(self,e):
		self.right_throt = self.right_throt - 20
		self.left_throt = self.left_throt - 20
		dispatcher.dispatch(Message('throt_speed', [self.addr, self.left_throt, self.right_throt]))

	def emergencyStopButtonClick(self,event):
		self.right_throt = 0
		self.left_throt = 0
		dispatcher.dispatch(Message('throt_speed', [self.addr, self.left_throt, self.right_throt]))

	def rightButtonClick(self,e):
		self.left_throt = self.right_throt + 20
		dispatcher.dispatch(Message('throt_speed', [self.addr, self.left_throt, self.right_throt]))

	def leftButtonClick(self,e):
		self.right_throt = self.left_throt + 20
		dispatcher.dispatch(Message('throt_speed', [self.addr, self.left_throt, self.right_throt]))

	def addButtonClick(self,event):
		# add a new row
		self.inputGrid.AppendRows(1)
	
	def resRowButtonClick(self, event):
		self.inputGrid.ClearGrid()
	
	#Determines which destination address to send commands to
	def OnSelect(self, event):
		select=event.GetSelection()
		if select == 0:
			self.addr = '\x30\x02'
			print "You chose number: " + str(repr(self.addr)) + " robot"
	
	def delButtonClick(self, event):
		numRows = self.inputGrid.GetNumberRows()
		self.inputGrid.DeleteRows(numRows-1,1)
		
	def runComButtonClick(self, e):
		move = gui_h.setupMoveq(self.inputGrid)
		threadedRunCommands(move, self.addr)
		
	def loadPreButtonClick(self, e):
		lst = ["Constant", "Ramp", "Sine"]
		dlg = wx.SingleChoiceDialog( self, "Pick a Preset", "Load Presets", lst)
	
		if (dlg.ShowModal() == wx.ID_OK):
			select = dlg.GetSelection()
			gui_h.gridPreset(self.inputGrid, select)
		dlg.Destroy()
	
	def saveDataButtonClick(self,e):
		if self.saveData.GetValue():
			dlg = wx.MessageDialog(self, "Please Choose a Save FilePath", "Save Prompt", wx.OK)
			dlg.ShowModal()
			dlg.Destroy()
			
	def on_text(self, text):
		self.outputData.AppendText(text)

	def status_command(self, val):
		if val == 'steering_rate':
			self.steer_rate_status.SetBackgroundColour('green')
		elif val == 'motor_gains':
			self.motor_gains_status.SetBackgroundColour('green')
		elif val == 'steering_gains':
			self.steer_gains_status.SetBackgroundColour('green')

#This class redirects the text from sysout/systerr to the text field
class RedirectText(object):
	def __init__(self,aWxTextCtrl):
		self.out=aWxTextCtrl

	def write(self, string):
		wx.CallAfter(self.out.WriteText, string)

#The interface to defining a save directory for data files
class PageTwo(wx.Panel):
	def __init__(self, parent): 
		wx.Panel.__init__(self, parent)
	
		self.openFile = wx.Button(self, -1, label = 'Save Path')
		self.Bind(EVT_BUTTON, self.onOpen, self.openFile)
	
		self.pathway = wx.TextCtrl(self,-1, name = 'Save Path')
	
		self.saveLabel = wx.StaticText(self, -1, label = "Choose a directory to save data files in")
	
		sizer = wx.GridBagSizer()
		saveSizer = wx.BoxSizer(wx.HORIZONTAL)
		saveSizer.Add(self.openFile,1,wx.ALL)
		saveSizer.Add(self.pathway,2,wx.EXPAND)
	
		sizer.Add(self.saveLabel, (2,0))
		sizer.Add(saveSizer, (3,0))
		self.SetSizer(sizer)
	
	def onOpen(self, event):
		self.dirname = ''
		dlg = wx.FileDialog(self, "Choose a file", self.dirname, "", "*.*", wx.OPEN)
		if dlg.ShowModal() == wx.ID_OK:
			self.dirname = dlg.GetDirectory()   
		dlg.Destroy()
		self.pathway.WriteText(self.dirname)

#		gui_h.saveData(self.dirname)
#The plots for graphing data
class PageThree(wx.Panel):
	def __init__(self, parent):
		wx.Panel.__init__(self, parent)
	
		self.figure = Figure(dpi=50)
		
		self.canvas = FigureCanvasWxAgg(self, -1, self.figure)
		self.toolbar = NavigationToolbar2Wx(self.canvas)
		self.toolbar.Realize()
		
		self.plotLast = wx.Button(self,-1,label="Plot Last")
		self.Bind(wx.EVT_BUTTON, self.plotLastButtonClick, self.plotLast)

		topSizer = wx.BoxSizer(wx.HORIZONTAL)
		sizer = wx.BoxSizer(wx.VERTICAL)
		topSizer.Add(self.plotLast, 0, wxFIXED_MINSIZE)
		topSizer.Add(self.canvas, 1, wx.LEFT | wx.TOP | wx.GROW)
		sizer.Add(topSizer,1,wx.GROW)
		sizer.Add(self.toolbar, 0, wx.GROW)
		self.SetSizer(sizer)
		self.Fit()
		
	def plotLastButtonClick(self, evt):
		gui_h.plotGraph(self.figure)
		self.canvas.draw()
	
#This class sets up the grid for inputGrid and outputs
class simpleGrid(gridlib.Grid):
	def __init__(self, parent):
		gridlib.Grid.__init__(self, parent)
		self.moveTo = None
	
		self.CreateGrid(5, 7)

		self.SetColLabelValue(0, "1")
		self.SetColLabelValue(1, "2")
		self.SetColLabelValue(2, "3")
		self.SetColLabelValue(3, "ACTION")
		self.SetColLabelValue(4, "4")
		self.SetColLabelValue(5, "5")
		self.SetColLabelValue(6, "6")

		self.SetColLabelAlignment(wx.ALIGN_CENTER, wx.ALIGN_BOTTOM)

		self.SetDefaultCellOverflow(False)
		r = gridlib.GridCellAutoWrapStringRenderer()
		self.SetCellRenderer(9, 1, r)

class ThreadedFrame(wx.Frame):
	def __init__(self, title, frameClass):
		wx.Frame.__init__(self, None, title=title, size = (950,700))

		# create a panel and a notebook on the panel
		p = wx.Panel(self)
		nb = wx.Notebook(p)

		self.addr = '\x30\x02'

		# create the page windows as children of the notebook
		page1 = PageOne(nb)
		page2 = PageTwo(nb)
		page3 = PageThree(nb)

		# add the pages to the notebook with the label to show on the tab
		nb.AddPage(page1, "Main")
		nb.AddPage(page2, "Utilities")
		nb.AddPage(page3, "Data")

		#packing the notebook into a sizer.
		sizer = wx.BoxSizer()
		sizer.Add(nb, 1, wx.EXPAND)
		p.SetSizer(sizer)
	
		self.status_bar = self.CreateStatusBar() # A StatusBar in the bottom of the window
		self.gauge = wx.Gauge(self.status_bar, -1, 100)#puts a progress bar in status bar

		# Setting up the menus.
		fileMenu= wx.Menu()
		modeMenu = wx.Menu()
		robotMenu = wx.Menu()
		optitraksMenu = wx.Menu()

		# Standard wx menu widgets
		menuAbout = fileMenu.Append(wx.ID_ABOUT, "&About"," Information about this program")
		menuExit = fileMenu.Append(wx.ID_EXIT,"E&xit"," Exit the program")

		#Robot menu widgets
		menu_Octo = robotMenu.Append(1, "&OctoRoach", "load presets for OctoROACH")
		menu_Orni = robotMenu.Append(2, "&Ornithopter", "load presets for Ornithopter")
		menu_CLASH = robotMenu.Append(3, "&CLASH", "load presets for CLASH")
		menu_DASH = robotMenu.Append(4, "&DASH", "load presets for DASH")

		#OPTITRAKS menu
		menu_connect = optitraksMenu.Append(1, "&Connect", "Connect to OPTITRAKS system")
		menu_discon = optitraksMenu.Append(2, "&Disconnect", "Disconnect from OPTITRAKS system")
		
		# Creates the menubar.
		menuBar = wx.MenuBar()
		menuBar.Append(fileMenu,"&File")
		menuBar.Append(robotMenu, "&Robots")
		menuBar.Append(optitraksMenu, "&Optitraks")
		self.SetMenuBar(menuBar)

		self.Bind(wx.EVT_MENU, self.onOcto, menu_Octo)
		self.Bind(wx.EVT_MENU, self.OnAbout, menuAbout)
		self.Bind(wx.EVT_MENU, self.OnExit, menuExit)
	
		# Bind close event here
		self.Bind(wx.EVT_CLOSE, self.OnCloseWindow)	
		self.Show(True)

	def put(self, data):
		self.dispatcher.put(message)
  
	def add_sinks(self,sinks):
		self.dispatcher.add_sinks(sinks)

	def status_command(self, val):
		if val == 'steering_rate':
			self.steer_rate_status.SetBackgroundColour('green')
		elif val == 'motor_gains':
			self.motor_gains_status.SetBackgroundColour('green')
		elif val == 'steering_gains':
			self.steer_gains_status.SetBackgroundColour('green')

	def onOcto(self, e):
		dispatcher.dispatch(Message('file', None))

		dispatcher.dispatch(Message('reset', self.addr))

		#motorgains = [200,2,0,2,0,    200,2,0,2,0]
		motorgains = [5000,100,0,0,0,5000,100,0,0,0] #Hardware PID

#		motor = [self.addr, motorgains]
		dispatcher.dispatch(Message('motor', [self.addr, motorgains]))

	def OnAbout(self,e):
		# Standard dialogue box with an "ok" button
		dlg = wx.MessageDialog( self, "A GUI to operate robots", "About SkyNet", wx.OK)
		dlg.ShowModal() # Show it
		dlg.Destroy() # finally destroy it when finished.
	
	def OnExit(self,e):
		self.Destroy() # Close the frame.
		sys.exit()

	def OnCloseWindow(self,e):
		dispatcher.dispatch(Message('quit', 'quit'))
		self.Destroy()
		sys.exit()