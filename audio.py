#region imports

import glob
import os
import tkinter as tk
from tkinter import ttk
import time
from functools import partial
import soundfile as sf
import matplotlib.pyplot as plt
from just_playback import Playback

#endregion imports

#region define global var 

global currentPrefix
currentPrefix = None

global isPlaying
isPlaying = False

global startTime
startTime = None

global fadeID
fadeID = None

global tunes
tunes = {}

global volumeDataList
volumeDataList = []

global volumeSliderList
volumeSliderList = []

global canvasWidgets
canvasWidgets = []

global canvasImgs
canvasImgs = []


#endregion define global var

#region general Funcs

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

def saveAudioFileFigure(x,savePath, text=''):
    fig,ax = plt.subplots(figsize=(5,0.8))
    ax.set_title(text,loc='left',fontdict={"size":8})
    ax.plot(x, color='gray',linewidth=0.2)
    ax.set_xlim(0,x.shape[0])
    ax.set_ylim(-7500,7500)
    ax.get_xaxis().set_visible(False)
    ax.get_yaxis().set_visible(False)
    ax.set_xlabel(text)
    fig.tight_layout()
    fig.savefig(savePath,bbox_inches='tight')
    plt.close(fig)

def onMousewheel(event):
    scale = event.widget
    resolution = float(scale.cget("resolution"))

    if event.delta:
        direction = 1 if event.delta > 0 else -1
    else:
        direction = 1 if event.num == 4 else -1

    scale.set(scale.get() + direction * resolution * 5)

def tickTime():
    global currentPrefix
    global startTime
    if currentPrefix != None and startTime != None:
        timeProp = (tunes[currentPrefix]["files"][0]["player"].curr_pos % tunes[currentPrefix]["files"][0]["player"].duration) / tunes[currentPrefix]["files"][0]["player"].duration
        progressBar["value"] = 1000 * timeProp
        
        if timeProp > 1:
            playTune(currentPrefix)
    
    master.after(50,tickTime)

def onClosing():
    for prefix in tunes:
        for strand in tunes[prefix]["files"]:
            strand["player"].stop()

    master.destroy()
    master.quit()
    os._exit(0)

#endregion general Funcs

#region volume Funcs

def processVolume(prefix,trackIndex,volume):
    tunes[prefix]["files"][trackIndex]["toFadeVolume"] = int(volume) / 100

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

def fadeVolumeLoop(prefix,initialVolumes,targetVolumes,totalTime,currentTime):
    if prefix != None:
        global fadeID
        if currentTime < totalTime:
            for strand,oldVolume,desiredVolume in zip(tunes[prefix]["files"],initialVolumes,targetVolumes):
                strand["player"].set_volume((currentTime/totalTime) * (desiredVolume-oldVolume) + oldVolume)
            fadeID = master.after(50,partial(fadeVolumeLoop,prefix,initialVolumes,targetVolumes,totalTime,currentTime+50))
        else:
            for strand,volume in zip(tunes[prefix]["files"],targetVolumes):
                strand["player"].set_volume(volume)
            fadeID = None

def silencePlaying(prefix = None):
    if prefix == None: prefix = currentPrefix
    maserVolumeData.set(0)
    onVolumeFade(prefix)

#endregion volume Funcs

#region startStop Funcs

def playTune(prefix):
    global currentPrefix
    if currentPrefix != None:
        stopPlaying(currentPrefix)

    progressBar["value"] = 0
    
    currentPrefix = prefix
    
    titleLabelData.set(currentPrefix)
    
    for strand,i in zip(tunes[currentPrefix]["files"],range(len(tunes[currentPrefix]["files"]))):
        tempVar = tk.IntVar(master,100)
        volumeDataList.append(tempVar)
        processVolume(currentPrefix,i,100)
        tempScale = tk.Scale(master,length=70,from_=100,to=0,orient='vertical',variable=tempVar,command=partial(processVolume,currentPrefix,i),showvalue=0)
        volumeSliderList.append(tempScale)
        tempScale.bind("<Enter>", lambda e: e.widget.focus_set())
        tempScale.bind("<MouseWheel>", onMousewheel)
        tempScale.grid(row=4+i,column=0,padx=2)
        
        img = tk.PhotoImage(file=strand["waveformPath"])
        canvasImgs.append(img)
        canvasWidget = tk.Label(master,image=img)
        canvasWidgets.append(canvasWidget)
        canvasWidget.grid(row=4+i,column=1,columnspan=20,sticky="NSEW")
        
        strand["onVolumeFade"] = 100
        maserVolumeData.set(100)
    
    master.after(2000,partial(startPlayers,currentPrefix))

def startPlayers(prefix):
    global startTime
    startTime = time.time()
    for strand in tunes[prefix]["files"]: # Seperated to ensure audio matches up
        strand["player"].play()
    
    onVolumeFade(prefix)

def stopPlaying(prefix=None): 
    if prefix == None: prefix = currentPrefix       
    global canvasWidgets
    global canvasImgs
    global volumeDataList
    global volumeSliderList
    
    silencePlaying(prefix)
    
    for canvasWidget in canvasWidgets:
        canvasWidget.destroy()
    
    for volumeSlider in volumeSliderList:
        volumeSlider.destroy()
    
    canvasImgs = []
    canvasWidgets = []
    volumeDataList = []
    volumeSliderList = []
    
    titleLabelData.set("None")
    
    master.after(2000,partial(stopPlayers,prefix))     

def stopPlayers(prefix):
    global startTime
    startTime = None
    for strand in tunes[prefix]["files"]:
        strand["player"].stop()

#endregion startStop Funcs

#region setupAudio

global absolutePath
absolutePath = "D:\\tmp"

audioFiles = [file for file in glob.glob(absolutePath + '/**', recursive=True) if (file[-4:] in [".wav",".mp3"] and "DefaultMix" not in file)]
prefixes = set()
for file in audioFiles:
    prefixes.add("\\".join(file.split("\\")[2:3]))

prefixes = sorted(list(prefixes))

for prefix in prefixes:
    theseFiles = [file for file in audioFiles if prefix in file]
    commonStr = findCommonLeftStr(*theseFiles)
    info = sf.info(theseFiles[0])
    tunes.update({prefix:{
        "files":[
            {
                "player":Playback(file),
                "name":file.replace(commonStr,"")[:-4],
                "toFadeVolume":1
            } for file in theseFiles
        ],
    }})

    for file,strand in zip(theseFiles,tunes[prefix]["files"]):
        cachePath = f'.\\cachedWaveforms\\{file.replace(absolutePath+"\\","").replace("\\","____")[:-4]}.png'
        strand.update({"waveformPath":cachePath})
        if not os.path.exists(cachePath):
            saveAudioFileFigure(sf.read(file,dtype='int16')[0][::500],cachePath,strand["name"])

#endregion setupAudio

#region tkinter

master = tk.Tk()
master.protocol("WM_DELETE_WINDOW", onClosing)

maserVolumeData = tk.IntVar(master,value=100)
masterVolume = tk.Scale(master,length=80,from_=100,to=0,orient='vertical',variable=maserVolumeData,showvalue=0)
masterVolume.grid(row=0,column=0,rowspan=3)

masterVolume.bind("<Enter>", lambda e: e.widget.focus_set())
masterVolume.bind("<MouseWheel>", onMousewheel)

progressBar = ttk.Progressbar(master,maximum=1000,orient='horizontal',mode='determinate')
progressBar.grid(row=3,column=1,columnspan=20,padx=10,sticky="ew")
progressBar['value'] = 0

setVolume = tk.Button(master,text="Fade",command=onVolumeFade)
setVolume.grid(row=0,column=1,padx=2,sticky="EW")
fadeToSilence = tk.Button(master,text="Silence",command=silencePlaying)
fadeToSilence.grid(row=1,column=1,padx=2,sticky="EW")
tempButton = tk.Button(master,text="Stop",command=stopPlaying)
tempButton.grid(row=2,column=1,padx=2,sticky="EW")

titleLabelData = tk.StringVar(master,"None") 
titleLabel = tk.Label(master,textvariable=titleLabelData,font="Helvetica 12 bold")
titleLabel.grid(row=2,column=2,columnspan=20,sticky="W")

for prefix in prefixes:
    tempButton = tk.Button(master,text=prefix,command=partial(playTune,prefix))
    tempButton.grid(row=20+prefixes.index(prefix),column=0,columnspan=20,pady=2,sticky="EW")

master.after(50,tickTime)
tk.mainloop()

#endregion tkinter