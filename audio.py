import glob
from audioplayer import AudioPlayer
import math
import os
import tkinter as tk
import time
from functools import partial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import soundfile as sf
import matplotlib.pyplot as plt

def getAudioFileCanvas(path,x, text=''):
    print(text)
    """1. Prints information about an audio singal, 2. plots the waveform, and 3. Creates player
    
    Notebook: C1/B_PythonAudio.ipynb
    
    Args: 
        x: Input signal
        Fs: Sampling rate of x    
        text: Text to print
    """
    
    fig,ax = plt.subplots(figsize=(5,0.8))
    ax.set_title(text,loc='left',fontdict={"size":8})
    ax.plot(x, color='gray')
    ax.set_xlim(0,x.shape[0])
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_xlabel(text)
    fig.tight_layout()
    return fig

def clearTerminal():
    os.system("cls")
    
def validatedNumericalInput(prompt:str , minimum:int , maximum:int) -> int:
    while True:
        clearTerminal()
        testInput = input(prompt)
        try:
            intInput = int(testInput)
            if minimum <= intInput and intInput <= maximum:
                return intInput
        except ValueError:
            continue

def pickFromOptions(options:list[str|int] , returnType="Option",displayPrefix="") -> str|int:
    if returnType not in ["Index","Option","Both"]: raise ValueError('returnType must be one of the following: "Index","Option","Both"')
    
    numberOfOptions = len(options)
    maxNumberOfSpaces = math.floor(math.log10(numberOfOptions)) + 1
    
    optionsDisplay = displayPrefix + "\n"
    for option , index in zip( options , range(numberOfOptions) ):
        prefix = " "*(maxNumberOfSpaces-len(str(index)))
        optionsDisplay += f"{prefix}{index} : {option}\n"
        
    optionsDisplay +="----- Enter Selection -----\n"
    
    index = validatedNumericalInput(prompt=optionsDisplay , minimum=0 , maximum=numberOfOptions-1)
    clearTerminal()
    match returnType:
        case "Index":
            return index
        case "Option":
            return options[index]
        case "Both":
            return [index,options[index]]

def findCommonLeftStr(*args):
    for i in range(max([len(s) for s in args])):
        if not all(args[0][:i] == args[argIndex][:i] for argIndex in range(1,len(args))):
            return args[0][:i-1]

def sign(a):
    if a == 0:
        return 0
    else:
        return a/abs(a)

def findVolume(currentVolume,desiredVolume,volumeDecayRate,dTime) -> float:
    return sign(desiredVolume-currentVolume) * volumeDecayRate * dTime

def processVolume(trackIndex,volume):
    if currentPrefix in tunes.keys():
        tunes[currentPrefix][trackIndex]["player"].volume = int(volume)

def on_mousewheel(event):
    scale = event.widget
    resolution = float(scale.cget("resolution"))

    # Windows / macOS
    if event.delta:
        direction = 1 if event.delta > 0 else -1
    else:
        # Linux
        direction = 1 if event.num == 4 else -1

    scale.set(scale.get() + direction * resolution * 5)


def playTune(prefix):
    global canvasWidgets
    global currentPrefix
    
    for canvasWidget in canvasWidgets:
        canvasWidget.destroy()
    
    canvasWidgets = []
    
    if currentPrefix != None:
        for strand in tunes[currentPrefix]:
            strand["player"].stop()

    for slider in volumeSliderList:
        slider['state'] = 'disabled'
        slider.config(bg="black")
    
    for strand,i in zip(tunes[prefix],range(len(tunes[prefix]))):
        strand["player"].play(loop=True)
        volumeSliderList[i]['state'] = 'normal'
        volumeSliderList[i].config(bg="#f0f0f0")
        canvas = FigureCanvasTkAgg(getAudioFileCanvas(strand["player"].fullfilename,strand["waveform"],strand["name"]), master=master)
        canvas.draw()
        canvasWidget = canvas.get_tk_widget()
        canvasWidgets.append(canvasWidget)
        canvasWidget.grid(row=4+i,column=0,columnspan=20,pady=2)
    
    currentPrefix = prefix

def onClosing():
    for prefix in tunes:
        for strand in tunes[prefix]:
            strand["player"].stop()
    
    master.destroy()
    master.quit()
    os._exit(0)

absolutePath = "D:\\tmp"

audioFiles = [file for file in glob.glob(absolutePath + '/**', recursive=True) if (file[-4:]==".wav" and "DefaultMix" not in file)]
prefixes = set()
for file in audioFiles:
    prefixes.add("\\".join(file.split("\\")[2:3]))
prefixes = sorted(list(prefixes))
global tunes
tunes = {}

global currentPrefix
currentPrefix = None

for prefix in prefixes:
    theseFiles = [file for file in audioFiles if prefix in file]
    commonStr = findCommonLeftStr(*theseFiles)
    tunes.update({prefix:[{"player":AudioPlayer(file),"waveform":sf.read(file,dtype='int16')[0][::1000],"name":file.replace(commonStr,"")[:-4]} for file in theseFiles]})

master = tk.Tk()
master.protocol("WM_DELETE_WINDOW", onClosing)

setVolume = tk.Button(master,text="Temp")
setVolume.grid(row=0,column=0,sticky="EW")
fadeToSilence = tk.Button(master,text="Temp")
fadeToSilence.grid(row=1,column=0,padx=2,sticky="EW")
tempButton = tk.Button(master,text="Temp")
tempButton.grid(row=2,column=0,padx=2,sticky="EW")

global volumeDataList
global volumeSliderList
global sliderLabelVarList

volumeDataList = []
volumeSliderList = []
sliderLabelVarList = []
for i in range(10):
    tempVar = tk.IntVar(master,100)
    volumeDataList.append(tempVar)
    
    tempScale = tk.Scale(master,from_=100,to=0,orient='vertical',variable=tempVar,command=partial(processVolume,i),showvalue=0)
    volumeSliderList.append(tempScale)
    tempScale.bind("<Enter>", lambda e: e.widget.focus_set())
    tempScale.bind("<MouseWheel>", on_mousewheel)
    tempScale.grid(row=0,column=2*i+1,padx=2,rowspan=3)
    
    
    
    # tempStrVar = tk.StringVar(master,"None")
    # sliderLabelVarList.append(tempStrVar)
    # tempLabel = tk.Label(master,font=("Helvetica",8),textvariable=tempStrVar,wraplength=1,anchor="n")
    # tempLabel.grid(row=0,column=2*i+2,padx=2,rowspan=3,sticky="ns")

global canvasWidgets
canvasWidgets = []

for prefix in prefixes:
    tempButton = tk.Button(master,text=prefix,command=partial(playTune,prefix))
    tempButton.grid(row=20+prefixes.index(prefix),column=0,columnspan=20,pady=2,sticky="EW")


tk.mainloop()