import Tkinter

class multiApp_tk(Tkinter.Tk):
#defining the self object
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()     
		
#initializing the labels and buttons
    def initialize(self):
        self.grid()
	
#Robot 1 Button
	self.buttonR1 = Tkinter.Button(self,text=u"Robot #1",
                                command=self.OnButtonClick)
        self.buttonR1.grid(column=0,row=1,columnspan=1,sticky='EW')
        
#Robot 2 Button
	self.buttonR2 = Tkinter.Button(self,text=u"Robot #2",
                                command=self.OnButtonClick)
        self.buttonR2.grid(column=1,row=1,columnspan=1)
        
#Robot 3 Button
	self.buttonR3 = Tkinter.Button(self,text=u"Robot #3",
                                command=self.OnButtonClick)
        self.buttonR3.grid(column=2,row=1,columnspan=1,sticky='EW')
        
#Robot 4 Button
	self.buttonR4 = Tkinter.Button(self,text=u"Robot #4",
                                command=self.OnButtonClick)
        self.buttonR4.grid(column=3,row=1,columnspan=1,sticky='EW')
        
#auto/man button
	self.var=Tkinter.StringVar()
	self.am = Tkinter.Checkbutton(self,text="AUTO/MAN",variable=self.var,onvalue="AUTO",offvalue="MAN",
				      indicatoron=False)
	self.am.grid(column=5,row=1,columnspan=1,sticky='EW')

#The Text Field
        self.entryVariable = Tkinter.StringVar()
        self.entry = Tkinter.Entry(self,textvariable=self.entryVariable)
        self.entry.grid(column=0,row=2,columnspan=4,sticky='EW')
        self.entry.bind("<Return>",self.OnPressEnter)
        self.entryVariable.set(u"Robot #1")

#Up Button
        self.buttonUp = Tkinter.Button(self,text=u"UP",
                                command=self.OnButtonClick)
        self.buttonUp.grid(column=5,row=2,sticky='EW')
 
#Down Button
        self.buttonDown = Tkinter.Button(self,text=u"DOWN",
        	                command=self.OnButtonClick)
        self.buttonDown.grid(column=5,row=3,sticky='EW')

#Left Button
        self.buttonLeft = Tkinter.Button(self,text=u"LEFT",
        	                command=self.OnButtonClick)
        self.buttonLeft.grid(column=4,row=3,sticky='EW')
 
#Right Button
        self.buttonRight = Tkinter.Button(self,text=u"RIGHT",
        	                command=self.OnButtonClick)
        self.buttonRight.grid(column=6,row=3,sticky='EW')

#The 3d space vector canvas
	self.w = Tkinter.Canvas(self,width=400,height=200)
	self.w.grid(column=0,row=5,columnspan=5,sticky='NSEW')
	
	self.w.create_rectangle(0,0,400,200,fill="blue")
	
#Scale Selector
	self.speed = Tkinter.Scale(self,from_=100,to=0,width=30)
	self.speed.grid(column=5,row=5)
	
#Emergency Stop
	self.eStop = Tkinter.Button(self,text=u"E-Stop", command=self.OnButtonClick,
		               bg="red")
	self.eStop.grid(column=6,row=5,columnspan=2,sticky='EW')
	
#info label
        self.labelVariable = Tkinter.StringVar()
        label = Tkinter.Label(self,textvariable=self.labelVariable,
                              anchor="w",fg="white",bg="black")
        label.grid(column=0,row=3,columnspan=4,sticky='EW')
        self.labelVariable.set(u"Information")
        
        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,False)
        self.update()
        self.geometry(self.geometry())       
        self.entry.focus_set()
        self.entry.selection_range(0,Tkinter.END)
        
#behavior on button click of "up" button
    def OnButtonClick(self):
        self.labelVariable.set(self.entryVariable.get()+" (You clicked the up button)" )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

#what happens when you press enter
    def OnPressEnter(self,event):
        self.labelVariable.set( self.entryVariable.get()+" (You pressed ENTER)" )
        self.entry.focus_set()
        self.entry.selection_range(0, Tkinter.END)

if __name__ == "__main__":
    app = multiApp_tk(None)
    app.title('Let\'s send these robots on their way')
    app.mainloop()
