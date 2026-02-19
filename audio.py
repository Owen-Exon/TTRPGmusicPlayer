import glob
from audioplayer import AudioPlayer
import math
import os
import tkinter as tk
from tkinter import ttk
import time
from functools import partial
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import soundfile as sf
import matplotlib.pyplot as plt

global currentPrefix
currentPrefix = None
global isPlaying
isPlaying = False

global startTime
startTime = None

def tickTime():
    global currentPrefix
    global startTime
    if currentPrefix != None and startTime != None:
        timeProp = ((time.time()-startTime) / tunes[currentPrefix]["duration"])
        progressBar["value"] = 1000 * timeProp
        
        if timeProp > 1:
            playTune(currentPrefix)

        
    master.after(50,tickTime)
        
        

def getAudioFileCanvas(x, text=''):
    fig,ax = plt.subplots(figsize=(5,0.8))
    ax.set_title(text,loc='left',fontdict={"size":8})
    ax.plot(x, color='gray',linewidth=0.2)
    ax.set_xlim(0,x.shape[0])
    ax.set_ylim(-7500,7500)
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
    if len(args) == 1:
        return ""
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

def processVolume(prefix,trackIndex,volume):
    tunes[prefix]["files"][trackIndex]["toFadeVolume"] = int(volume)

global fadeID
fadeID = None

def fadeVolumeLoop(prefix,initialVolumes,targetVolumes,totalTime,currentTime):
    if prefix != None:
        global fadeID
        if currentTime < totalTime:
            for strand,oldVolume,desiredVolume in zip(tunes[prefix]["files"],initialVolumes,targetVolumes):
                strand["player"].volume = (currentTime/totalTime) * (desiredVolume-oldVolume) + oldVolume
            fadeID = master.after(50,partial(fadeVolumeLoop,prefix,initialVolumes,targetVolumes,totalTime,currentTime+50))
        else:
            for strand,volume in zip(tunes[prefix]["files"],targetVolumes):
                strand["player"].volume = volume
            fadeID = None

def onVolumeFade(prefix=None):
    global fadeID
    if fadeID != None: master.after_cancel(fadeID)
    if prefix == None: prefix = currentPrefix
    initialVolumes = []
    targetVolumes = []
    for strand in tunes[prefix]["files"]:
        initialVolumes.append(strand["player"].volume)
        targetVolumes.append(strand["toFadeVolume"] * (maserVolumeData.get() / 100))
    
    fadeID = master.after(50,partial(fadeVolumeLoop,prefix,initialVolumes,targetVolumes,2000,50))
        
        


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

def stopPlayers(prefix):
    startTime = None
    for strand in tunes[prefix]["files"]:
        strand["player"].stop()


def stopPlaying(prefix=None): 
    if prefix == None: prefix = currentPrefix       
    global canvasWidgets
    global volumeDataList
    global volumeSliderList
    
    silencePlaying(prefix)
    
    for canvasWidget in canvasWidgets:
        canvasWidget.destroy()
    
    for volumeSlider in volumeSliderList:
        volumeSlider.destroy()
    
    canvasWidgets = []
    volumeDataList = []
    volumeSliderList = []
    
    master.after(2000,partial(stopPlayers,prefix))

        
    
def silencePlaying(prefix = None):
    if prefix == None: prefix = currentPrefix
    maserVolumeData.set(0)
    onVolumeFade(prefix)

def startPlayers(prefix):
    global startTime
    startTime = time.time()
    for strand in tunes[prefix]["files"]: # Seperated to ensure audio matches up
        strand["player"].play()
    
    onVolumeFade(prefix)

def playTune(prefix):
    global currentPrefix
    if currentPrefix != None:
        stopPlaying(currentPrefix)
    
    
    
    progressBar["value"] = 0
    
    currentPrefix = prefix
    
    for strand,i in zip(tunes[currentPrefix]["files"],range(len(tunes[currentPrefix]["files"]))):
        tempVar = tk.IntVar(master,100)
        volumeDataList.append(tempVar)
        processVolume(currentPrefix,i,100)
        tempScale = tk.Scale(master,length=80,from_=100,to=0,orient='vertical',variable=tempVar,command=partial(processVolume,currentPrefix,i),showvalue=0)
        volumeSliderList.append(tempScale)
        tempScale.bind("<Enter>", lambda e: e.widget.focus_set())
        tempScale.bind("<MouseWheel>", on_mousewheel)
        tempScale.grid(row=4+i,column=0,padx=2)
        fig = getAudioFileCanvas(strand["waveform"],strand["name"])
        canvas = FigureCanvasTkAgg(fig, master=master)
        
        canvas.draw()
        canvasWidget = canvas.get_tk_widget()
        canvasWidgets.append(canvasWidget)
        canvasWidget.grid(row=4+i,column=1)
        
        strand["onVolumeFade"] = 100
        maserVolumeData.set(100)
    
    master.after(2000,partial(startPlayers,currentPrefix))
    
def onClosing():
    for prefix in tunes:
        for strand in tunes[prefix]["files"]:
            strand["player"].stop()
            strand["player"].close()
    
    master.destroy()
    master.quit()
    os._exit(0)

absolutePath = "D:\\tmp"

audioFiles = [file for file in glob.glob(absolutePath + '/**', recursive=True) if (file[-4:] in [".wav",".mp3"] and "DefaultMix" not in file)]
prefixes = set()
for file in audioFiles:
    prefixes.add("\\".join(file.split("\\")[2:3]))
prefixes = sorted(list(prefixes))
global tunes
tunes = {}

for prefix in prefixes:
    theseFiles = [file for file in audioFiles if prefix in file]
    commonStr = findCommonLeftStr(*theseFiles)
    info = sf.info(theseFiles[0])

    tunes.update({prefix:{
        "files":[
        {
            "player":AudioPlayer(file),
            "waveform":sf.read(file,dtype='int16')[0][::500],
            "name":file.replace(commonStr,"")[:-4],
            "toFadeVolume":100
        } for file in theseFiles],
        "duration":info.frames/info.samplerate
    }})


master = tk.Tk()
master.protocol("WM_DELETE_WINDOW", onClosing)

maserVolumeData = tk.IntVar(master,value=100)
masterVolume = tk.Scale(master,length=80,from_=100,to=0,orient='vertical',variable=maserVolumeData,showvalue=0)
masterVolume.grid(row=0,column=0,rowspan=3)

masterVolume.bind("<Enter>", lambda e: e.widget.focus_set())
masterVolume.bind("<MouseWheel>", on_mousewheel)

progressBar = ttk.Progressbar(master,maximum=1000,orient='horizontal',mode='determinate')
progressBar.grid(row=3,column=1,columnspan=20,padx=12,sticky="ew")
progressBar['value'] = 0

setVolume = tk.Button(master,text="Fade",command=onVolumeFade)
setVolume.grid(row=0,column=1,padx=2,sticky="EW")
fadeToSilence = tk.Button(master,text="Silence",command=silencePlaying)
fadeToSilence.grid(row=1,column=1,padx=2,sticky="EW")
tempButton = tk.Button(master,text="Stop",command=stopPlaying)
tempButton.grid(row=2,column=1,padx=2,sticky="EW")

global volumeDataList
global volumeSliderList

volumeDataList = []
volumeSliderList = []

global canvasWidgets
canvasWidgets = []

for prefix in prefixes:
    tempButton = tk.Button(master,text=prefix,command=partial(playTune,prefix))
    tempButton.grid(row=20+prefixes.index(prefix),column=0,columnspan=20,pady=2,sticky="EW")

master.after(50,tickTime)
tk.mainloop()