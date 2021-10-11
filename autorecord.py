#!/usr/bin/env python3
# coding: utf-8

# # Code for long term recording of sounds for Raspberry

# # Not complete
# * Have option to turn off Wifi after recording starts
# * Have option to turn it back on when recording is finished
# * command to use is 'sudo ifconfig wlan0 down' - this was tested
# * note that the above is deprecated - so may need to switch to:
# ip link set dev <interface> up
# ip link set dev <interface> down

#Can launch using
#   /home/pi/code/autorecord7.py &


# ## Library for ALSA
# Can use amixer on command line to get everything
#
#
## Library for Audio
# https://pypi.org/project/PyAudio/

#
#
#
#
# ## Raspberry Pi specifics
# https://makersportal.com/blog/2018/8/23/recording-audio-on-the-raspberry-pi-with-python-and-a-usb-microphone
#
#
# ##Need Opus converter
#  conda install -c conda-forge opus-tools
#  OR
#  sudo apt install opus-tools
# sudo apt install vorbis-tools
# sudo apt-get install flac
#
# https://opus-codec.org/release/dev/2018/09/18/opus-tools-0_2.html
#
#
# ## Mutagen edits file metadata
# pip install mutagen
#
#

# ALSA lib error messages like are generated with pyaudio:
#ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.front
#ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.rear
#ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.center_lfe
#ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.side
#ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.surround21
#ALSA lib pcm.c:2565:(snd_pcm_open_noupdate) Unknown PCM cards.pcm.surround21

# remove them by editing your
# /usr/share/alsa/alsa.conf   <---BAD IDEA
# to comment out relevant lines

#OR see https://stackoverflow.com/questions/36956083/how-can-the-terminal-output-of-executables-run-by-python-functions-be-silenced-i/36966379#36966379
#for a better approach.

# also look at ~/.asoundrc and /etc/asound.conf


import tempfile
import sys
from math import ceil


import pyaudio
import numpy  # Make sure NumPy is loaded before it is used in the callback
assert numpy  # avoid "imported but unused" message (W0611)

import subprocess as sp
import time
import configparser
import mutagen

import os
import psutil


# ## Recording and conversion on the fly
#
# ### additions
# * Allow selection of compression technique or format: ogg, flac, opus - done
# * store the A to D details like gain settings, mic description - partial
# * Create a function that reads addresses and textually describes the channel input path and processing
# * On A to D board, use mic bias to calibrate the inputs?
# * allow swapping of usb drives while recording
# * adjust gain based on time of day or cyclical averages
# * record at two gains
# * adjust gain in real time and capture gain adjustment as a separate channel to decompress later
# * Understand how the VLC app works and how it might be useful
# * Look at omxplayer, command line app on rpi for audio streaming
# * change recording resolution to 32 bit for lossless.
# * try using 4 channel i2s with octo driver snippets
# * have recording start on the hour?  track indicates hour??

# Big new features
# * GPS location and time
# * Battery monitoring
# * Listen via bluetooth


# Improve Reliability
# * ignore dropouts - done
# * catch dropouts and log info like 'top' - solved - changed to sounddevice callback
# * use pyaudio in non locking mode (callback)?? - done - sounce device
# * drop Opus and try using SoundFile which supports FLAC and Ogg/Vorbis - done - without soundfile 
# * run some automated experiments that try different settings and test for dropout freq 

# * Fixes
# * Fix samplerate inconsistency - a variable and fixed to 48000 in code
# * Make bitrate a configurable item

#debug
import TLV320ADC




#Define a dummy ADC for testing without the TLV320ADC
# Just returns a stubbed total gain
class DUMMYADC:
    def __init__(self,i2c_address=0x4c, input_dbm_per_dbv=[0,0,0,0]): # default i2c address
        self.power_status = {"ADC":0, 1:0, 2:0, 3:0, 4:0}
        self.samplerate_status = 0
        self.pre_input_gain_db = input_dbm_per_dbv
        self.a_gain_db = [1.0,2.0,0.0,0.0]
        self.d_gain_db = [3.0,4.0,0.0,0.0]
        


        
        self.adc_i2c_address = i2c_address 


    
    def total_gain(self):
        
        total_db = []
        for i in range(len(self.a_gain_db)):
            total_db.append(self.pre_input_gain_db[i] + self.a_gain_db[i] + self.d_gain_db[i])
            
        return total_db




def setup_adc(adc, again,dgain):



    # Startup and wakeup sequence
    adc.shutdown()

    adc.startup()
    adc.set_wake()
    adc.set_power_config()

    #Set communication
    adc.set_communication(samplerate=48)
    adc.set_output_type(protocol="I2S", word_length=32, compatibility= True)
    adc.set_output_slot(channel=1, slot_side="LEFT", slot_num=0)
    adc.set_output_slot(channel=2, slot_side="RIGHT", slot_num=0)

    #Set analog gains before ADC powerup
    adc.set_analog_gain(1, analog_gain_db=again)
    adc.set_analog_gain(2, analog_gain_db=again)

    #Set any coefficients and mixer settings here
    adc.set_summer(sum_type = "NONE")
    adc.set_dynamic_range_enhancer( trigger_threshold_db = -54, max_gain_db=24, enable_dre=True )

    # Configure inputs

    adc.set_input(channel=1, in_type="MIC", config="DIFF", coupling="AC", impedance=2.5, dynamic_range_processing="ON")
    adc.set_input(channel=2, in_type="MIC", config="DIFF", coupling="AC", impedance=2.5, dynamic_range_processing="ON")

    #Turn on ADC
    adc.set_input_power([1,2], power="ON", enable = True)
    adc.set_output_enable(channel_list=[1,2],enable=True)
    adc.set_adc_power( mic_bias="ON", vref_volt=2.75, mic_bias_volt="1.096VREF", change_input_pwr_while_recording=False)

    # Below items can be changed while running


    adc.set_digital_gain_calibration(1, calibration_db = 0.0)
    adc.set_digital_gain_calibration(2, calibration_db = 0.0)

    adc.set_phase_calibration(1, calibration_cycles = 0.0)
    adc.set_phase_calibration(2, calibration_cycles = 0.0)

    adc.set_digital_gain(channel=1, digital_gain_db = dgain, muted=False, soft_step=True, ganged=False)
    adc.set_digital_gain(channel=2, digital_gain_db = dgain, muted=False, soft_step=True, ganged=False)

    #print("ADC is ready")


    return



def cputemp():
    with open("/sys/class/thermal/thermal_zone0/temp", 'r') as f:
        return float(f.read().strip()) / 1000


def encoding_command(filename,enc, date_string,title_string,artist_string,album_string,genre_string, channels = 2, bitrate=96):
    
    if enc == 'flac':
        outfile = filename+'.flac'
        command = ['flac',
                   '--silent',
                   '--force',
                   '--compression-level-5',
                   '--endian','little',
                   '--channels',str(channels),
                   '--bps','24',
                   '--sample-rate','48000',
                   '--sign',"signed",
                   '-T','date='+date_string,
                   '-T','title='+title_string,
                   '-T','artist='+artist_string,
                   '-T','album='+album_string,
                   '-T','genre='+genre_string,
                   '-',
                   '-o', str(outfile)]

    elif enc == 'opus':
        outfile = filename+'.opus'
        command = ['opusenc',
                   '--bitrate', str(bitrate),
                   '--comp', '10',
                   '--framesize', '20',
                   '--date', date_string,
                   '--title', title_string,
                   '--artist', artist_string,
                   '--album',album_string,
                   '--genre',genre_string,
                   '--raw',
                   '--raw-bits', '24',
                   '--raw-rate', '48000',
                   '--raw-chan', str(channels),
                   '--raw-endianness', '0',
                   '--quiet',
                   '-',str(outfile) ]
    elif enc == 'ogg':
        outfile = filename+'.ogg'
        command = ['oggenc',
                   '--quiet',
                   '--raw',
                   '--raw-bits', '24',
                   '--raw-chan', str(channels),
                   '--raw-rate', '48000',
                   '--raw-endianness', '0',
                   '--bitrate', str(bitrate),
                   '--date',date_string,
                   '--title',title_string,
                   '--album',album_string,
                   '--artist',artist_string,
                   '--genre',genre_string,
                   '--output', str(outfile),
                   '-']

    return command,outfile
    
def editmeta(outfile,tracknumber,tracktotal,comment, location):
    #Edit the audio metadata
    ##This needs to be updated for the different formats, opus, flac, ogg
    meta = mutagen.File(outfile)
    meta["tracknumber"] = str(tracknumber)
    meta["tracktotal"] = str(tracktotal)
    meta["location"] = location
    meta["comment"] = comment
    #print(meta.pprint())
    meta.save()
    
    
def editmeta_command(outfile,tracknumber,tracktotal,comment, location):
    command = ['./editmeta.py',
               '--tracknumber', str(tracknumber),
               '--tracktotal', str(tracktotal),
               '--location', location,
               '--comment', comment,
               outfile]
    return command
    





def record_sounds(adc, enc,file_path, file_count, title="Sound Recording",
                  location = "Test", artist_string="Me",
                  genre_string = "Nature", file_size_minutes = 15,
                  overflow_exception=True, logfile=None) :
    errorfile =  None
    res_bits = 24
    res_format = pyaudio.paInt24 # 24-bit resolution
    channels = 2 # 2 channel
    samplerate = 48000 # 48kHz sampling rate
    chunk = 9600 # Even multiple for buffer
    record_secs = file_size_minutes * 60 # seconds to record

    bitrate = 256 #kbits per second encoding

    #debug
    soundcard = "ADCX140"
    #soundcard = "VIA"

    audio = pyaudio.PyAudio()
        
    dev_index=None
    
    logfile.write("Audio Cards/n")
    for ii in range(audio.get_device_count()):
        device_name = audio.get_device_info_by_index(ii).get('name')
        logfile.write(str(ii)+"->"+device_name+"\n")
        if soundcard in device_name:
            dev_index = ii

    if dev_index is None:
        logfile.write("Audio card "+soundcard+" is not found!"+"\n")
        return 0
    
    logfile.write("Full Device Info:"+str(audio.get_device_info_by_index(dev_index))+"\n")
    
    afs = audio.is_format_supported(rate=samplerate, input_device=dev_index, input_channels=channels,
                             input_format=res_format)
    logfile.write("is format supported? "+str(afs)+"\n")
    

    date_string = time.strftime("%Y-%m-%d")
    album_string = title + " at " + location
    logfile.write("Creating Album: "+ album_string+" on " +
          time.strftime("%Y-%m-%d")+time.strftime(" %I:%M:%S %p")+"\n")

    logfile.flush()
    print("Creating Album: "+ album_string+" on " +
          time.strftime("%Y-%m-%d")+time.strftime(" %I:%M:%S %p")+"\n")
    

    # ping-pong between two processes for continuous processing
    ping = 0
    
    p = [0,0]
    
    # create pyaudio stream
    stream = audio.open(format = res_format,rate = samplerate,channels = channels,
                        input_device_index = dev_index,input = True,
                        frames_per_buffer=chunk)
    
    for file_num in range(1,1+file_count):




        date_time_string = time.strftime("%Y-%m-%d--%H-%M-%S")

        title_string = title + "-" + date_time_string

        filename = file_path + title_string + "-" + str(file_num)

        date_string = time.strftime("%Y-%m-%d")

        #debug
        #comment_string = "Test Comment"
        comment_string = "Total Gain: "+str(adc.total_gain())+" dB"


        command,outfile = encoding_command(filename,enc, date_string,title_string,artist_string,
                                           album_string,genre_string, channels, bitrate)

        logfile.write("CPU Temp="+str(cputemp())+"\n")
        
        p[ping] = sp.Popen(command, bufsize = 48000*2, stdin=sp.PIPE)
        
        logfile.write("recording file:"+outfile+"\n")
        logfile.flush()
        
        

    


        # loop through stream and append audio chunks to frame array
        for ii in range(0, ceil((samplerate/chunk)*record_secs)):
            data = stream.read(chunk, exception_on_overflow=overflow_exception)
            p[ping].stdin.write(data)

        p[ping].stdin.close()
        
        
        metadata_command = editmeta_command(outfile,tracknumber=file_num,tracktotal=file_count,
                                            comment=comment_string, location=location)
        p_meta = sp.Popen(metadata_command)
        
        #editmeta(outfile,tracknumber,tracktotal,comment, location)


        ping = (ping + 1) & 1  # return zero or one
        if p[ping] != 0:
            p[ping].wait()
            
            
            

    logfile.write("finished recording"+"\n")


    # stop the stream, close it, and terminate the pyaudio instantiation
    stream.stop_stream()
    stream.close()
    audio.terminate()
    
    # clean up
    ping = (ping + 1) & 1  # return zero or one
    p[ping].wait()
    
        
    success_flag = 1
    
    return success_flag


def init_arecord():
    command = "arecord -L"
    sp.run(command.split())
    return



def shutdown():
    command = "/usr/bin/sudo /usr/sbin/shutdown -h now"
    process = sp.Popen(command.split(),stdout=sp.PIPE)
    #output = process.communicate()[0]
    #print(output)
    #return output

def wireless(state):

    if state:
        command = "/usr/bin/sudo /usr/sbin/ifconfig wlan0 up"
    else:
        command = "/usr/bin/echo wifi_going_down_in_120_sec && /usr/bin/sleep 120 && /usr/bin/sudo /usr/sbin/ifconfig wlan0 down"
        #command = "/usr/bin/sudo /usr/sbin/ifconfig wlan0 down"
    process = sp.Popen(command,shell=True) #using shell, but command is fixed


#Main code

init_arecord()

config = configparser.ConfigParser()
configfilename = 'config.ini'

config.read(configfilename)
print(configfilename)

if config.sections() == []:
    # write out a config file
    config['audio_files']={}
    config['state']['run'] = "record complete"
    config['audio_files']['title'] = "Title"
    config['audio_files']['location'] = "Location"
    config['audio_files']['artist'] = "Artist"
    config['audio_files']['genre'] = "Nature"
    config['audio_files']['encoding'] = 'opus'  # 'opus', 'flac', 'ogg'
    config['audio_files']['filePath'] = "/media/pi/LINUXUSB/recordings/"

    config['settings']={}
    config['settings']["hours"] = "12.0"
    config['settings']["analoggain"] = "30"
    config['settings']["digitalgain"] = "20"
    config['settings']["turnoff"] = "No"
    config['settings']["wifi_on_during_recording"] = "Yes"
    config['settings']["fileminutes"] = "30"
    config['settings']["logfile"] = "logfile.txt"
    print("Writing out a new 'config.ini' file")
    with open('configfilename','w') as cfile:
        config.write(cfile)

elif config['state']['run'] == "record":

    config['state']['run'] = 'record started'

    #read config
    title = config['audio_files']['title']
    location = config['audio_files']['location']
    artist = config['audio_files']['artist']
    genre = config['audio_files']['genre']
    enc = config['audio_files']['encoding']
    file_path = config['audio_files']['filepath']

    again =float(config['settings']["analoggain"])
    dgain = float(config['settings']["digitalgain"])
    hours = float(config['settings']["Hours"])
    fileminutes = float(config['settings']["fileminutes"])
    turnoff = config['settings']["turnOff"]
    wifi_on = config['settings']["wifi_on_during_recording"]
    logfile = open(config['settings']['logfile'], "a")
    logfile.write("\n"+"*+*"+"*"*30+"\n")

    logfile.write("Starting Run at"+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")

    file_count = int(hours*60.0/fileminutes)
    logfile.write(" Run will produce "+str(file_count)+" files each of "+str(fileminutes)+" minutes."+"\n")

    #print("Delay until startup completes to load AlSA, etc")

    #for d in range(1,30):
    #    print(d, end=',')
    #    time.sleep(1)

    #print("done.")


    with open(configfilename,'w') as cfile:
        config.write(cfile)

    logfile.write("Path:"+file_path+"\n")

    #debug
    #adc1 = DUMMYADC()
    adc1 = TLV320ADC.TLV320ADC()

    #debug
    setup_adc(adc1,again=again,dgain=dgain)

    print("Wifi flag = ",wifi_on)

    if wifi_on == "No":
        wireless(False)
        logfile.write("Wifi will be shut down during recording"+"\n")
        logfile.flush()

    record_sounds(adc=adc1,enc=enc,file_path=file_path,file_count=file_count,
                  title=title, location = location, artist_string= artist,
                  genre_string = genre, file_size_minutes = fileminutes,
                  overflow_exception = False,
                  logfile=logfile)

    config['state']['run'] = 'record complete'
    with open(configfilename,'w') as cfile:
        config.write(cfile)
    logfile.write("Finished recording at "+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")

    if wifi_on == "No":
        wireless(True)
        logfile.write("Wifi turned back on at "+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")
    
    
    if turnoff == "Yes":
        logfile.write("Shutting down at "+time.strftime("%Y-%m-%d %I:%M:%S %p")+"\n")
        logfile.close()
        shutdown()
else:
    logfile = open(config['settings']['logfile'], "a")
    logfile.write("Config file shows this is already recorded\n")

logfile.close()
