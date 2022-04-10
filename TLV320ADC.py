## ADC testing

## Tools
## sudo apt-get install -y i2c-tools
## i2cdetect -y 1

## May not be needed, try without first
##  pip install RPi.GPIO
##  pip install smbus

import RPi.GPIO as GPIO
from smbus import SMBus
import time


class TLV320ADC:
    def __init__(self,i2c_address=0x4c, input_dbm_per_dbv=[0,0,0,0]): # default i2c address
        self.power_status = {"ADC":0, 1:0, 2:0, 3:0, 4:0}
        self.samplerate_status = 0
        self.pre_input_gain_db = input_dbm_per_dbv
        self.a_gain_db = [0.0,0.0,0.0,0.0]
        self.d_gain_db = [0.0,0.0,0.0,0.0]
        
        self.debug=False

        GPIO.setwarnings(False)
        GPIO.setmode(GPIO.BCM)
        self.inv_standby_pin = 4
        GPIO.setup(self.inv_standby_pin, GPIO.OUT)
        
        self.i2c = SMBus(1)


        
        self.adc_i2c_address = i2c_address 

        self.mp = {
            "ADCX140_PAGE_SELECT" : 0x00,
            "ADCX140_SW_RESET" : 0x01,
            "ADCX140_SLEEP_CFG" : 0x02,
            "ADCX140_SHDN_CFG" : 0x05,
            "ADCX140_ASI_CFG0" : 0x07,
            "ADCX140_ASI_CFG1" : 0x08,
            "ADCX140_ASI_CFG2" : 0x09,
            "ADCX140_ASI_CH1" : 0x0b,
            "ADCX140_ASI_CH2" : 0x0c,
            "ADCX140_ASI_CH3" : 0x0d,
            "ADCX140_ASI_CH4" : 0x0e,
            "ADCX140_ASI_CH5" : 0x0f,
            "ADCX140_ASI_CH6" : 0x10,
            "ADCX140_ASI_CH7" : 0x11,
            "ADCX140_ASI_CH8" : 0x12,
            "ADCX140_MST_CFG0" : 0x13,
            "ADCX140_MST_CFG1" : 0x14,
            "ADCX140_ASI_STS" : 0x15,
            "ADCX140_CLK_SRC" : 0x16,
            "ADCX140_PDMCLK_CFG" : 0x1f,
            "ADCX140_PDM_CFG" : 0x20,
            "ADCX140_GPIO_CFG0" : 0x21,
            "ADCX140_GPO_CFG0" : 0x22,
            "ADCX140_GPO_CFG1" : 0x23,
            "ADCX140_GPO_CFG2" : 0x24,
            "ADCX140_GPO_CFG3" : 0x25,
            "ADCX140_GPO_VAL" : 0x29,
            "ADCX140_GPIO_MON" : 0x2a,
            "ADCX140_GPI_CFG0" : 0x2b,
            "ADCX140_GPI_CFG1" : 0x2c,
            "ADCX140_GPI_MON" : 0x2f,
            "ADCX140_INT_CFG" : 0x32,
            "ADCX140_INT_MASK0" : 0x33,
            "ADCX140_INT_LTCH0" : 0x36,
            "ADCX140_BIAS_CFG" : 0x3b,
            "ADCX140_CH1_CFG0" : 0x3c,
            "ADCX140_CH1_CFG1" : 0x3d,
            "ADCX140_CH1_CFG2" : 0x3e,
            "ADCX140_CH1_CFG3" : 0x3f,
            "ADCX140_CH1_CFG4" : 0x40,
            "ADCX140_CH2_CFG0" : 0x41,
            "ADCX140_CH2_CFG1" : 0x42,
            "ADCX140_CH2_CFG2" : 0x43,
            "ADCX140_CH2_CFG3" : 0x44,
            "ADCX140_CH2_CFG4" : 0x45,
            "ADCX140_CH3_CFG0" : 0x46,
            "ADCX140_CH3_CFG1" : 0x47,
            "ADCX140_CH3_CFG2" : 0x48,
            "ADCX140_CH3_CFG3" : 0x49,
            "ADCX140_CH3_CFG4" : 0x4a,
            "ADCX140_CH4_CFG0" : 0x4b,
            "ADCX140_CH4_CFG1" : 0x4c,
            "ADCX140_CH4_CFG2" : 0x4d,
            "ADCX140_CH4_CFG3" : 0x4e,
            "ADCX140_CH4_CFG4" : 0x4f,
            "ADCX140_CH5_CFG2" : 0x52,
            "ADCX140_CH5_CFG3" : 0x53,
            "ADCX140_CH5_CFG4" : 0x54,
            "ADCX140_CH6_CFG2" : 0x57,
            "ADCX140_CH6_CFG3" : 0x58,
            "ADCX140_CH6_CFG4" : 0x59,
            "ADCX140_CH7_CFG2" : 0x5c,
            "ADCX140_CH7_CFG3" : 0x5d,
            "ADCX140_CH7_CFG4" : 0x5e,
            "ADCX140_CH8_CFG2" : 0x61,
            "ADCX140_CH8_CFG3" : 0x62,
            "ADCX140_CH8_CFG4" : 0x63,
            "ADCX140_DSP_CFG0" : 0x6b,
            "ADCX140_DSP_CFG1" : 0x6c,
            "ADCX140_DRE_CFG0" : 0x6d,
            "ADCX140_AGC_CFG0" : 0x70,
            "ADCX140_IN_CH_EN" : 0x73,
            "ADCX140_ASI_OUT_CH_EN" : 0x74,
            "ADCX140_PWR_CFG" : 0x75,
            "ADCX140_DEV_STS0" : 0x76,
            "ADCX140_DEV_STS1" : 0x77
            }

        # reverse the mp dictionary

        self.rmp = {v:k for k, v in self.mp.items()}
        self.i2c_current=dict()
        self.i2c_mod=dict()



    def bin8(self,dec_num):
        return "0b"+f"{dec_num:08b}"

    def addr(self,st):
    
        return(self.mp[st])

    def addr_txt(self,num):
        return(self.rmp[num])
    
    def total_gain(self):
        
        total_db = []
        for i in range(len(self.a_gain_db)):
            total_db.append(self.pre_input_gain_db[i] + self.a_gain_db[i] + self.d_gain_db[i])
            
        return total_db




    def i2cread(self,ad):

        #handle ints or string addresses by turning ints to strings
        if isinstance(ad,int):
            ad=self.addr_txt(ad)
        msg = self.i2c.read_byte_data(self.adc_i2c_address, self.addr(ad))
        if self.debug:
            print("Addr:",ad," is ",self.addr(ad),"(", hex(self.addr(ad)),")","-> read",msg,"<", hex(msg),"> <",self.bin8(msg),">")
        return msg


    def i2cwrite(self,ad, msg):

        #handle ints or string addresses by turning ints to strings
        if isinstance(ad,int):
            ad=self.addr_txt(ad)

        if self.debug:
            print("Addr:",ad," is ",self.addr(ad),"(", hex(self.addr(ad)),")","-> write",msg,"<", hex(msg),"> <",self.bin8(msg),">")

        
        if not self.debug:
            self.i2c.write_byte_data(self.adc_i2c_address, self.addr(ad), msg)
        self.i2c_current[ad]=msg
        if ad in self.i2c_mod:
            del self.i2c_mod[ad]
            
        return


    def i2c_set(self,ad, mask):
        #handle ints or string addresses by turning ints to strings
        if isinstance(ad,int):
            ad=self.addr_txt(ad)    
        
        # check if update exists, and if so, update the update with mask
        if ad in self.i2c_mod:
            self.i2c_mod[ad] = self.i2c_mod[ad] | mask
        else:
            # else check if current exists, and read if not.  Then create update from current and mask
            if ad not in self.i2c_current:
                self.i2c_current[ad] = self.i2cread(ad)
            self.i2c_mod[ad] = self.i2c_current[ad] | mask
        return

    def i2c_clr(self,ad, mask):
        # check if update exists, and if so, update the update with mask
        #handle ints or string addresses by turning ints to strings
        if isinstance(ad,int):
            ad=self.addr_txt(ad)    
        
        if ad in self.i2c_mod:
            self.i2c_mod[ad] = self.i2c_mod[ad] & mask
        else:
            # else check if current exists, and read if not.  Then create update from current and mask
            if ad not in self.i2c_current:
                self.i2c_current[ad] = self.i2cread(ad)
            self.i2c_mod[ad] = self.i2c_current[ad] & mask
        return


    def apply_bits(self,x, start_bit, field_size, val, word_size=8):
        
        # create a mask to zero out the field at start bit
        mask = 2**word_size - 1 - (2**field_size -1) * (2**start_bit)
        
        #ensure that the value is not larger than what can be held in the field size
        val = min(val, 2**(field_size) - 1)
        
        #shift the value to lign up with the start bit
        w = val * 2**start_bit
        
        #clear out the field and overwrite with the shifted value
        y = (x & mask) | w

        return(y)


    def i2c_bits(self,ad, start_bit, field_size, val):
        #handle ints or string addresses by turning ints to strings
        if isinstance(ad,int):
            ad=self.addr_txt(ad)    
        
        # check if update exists, and if so, update the update with mask
        if ad in self.i2c_mod:
            self.i2c_mod[ad] = self.apply_bits(self.i2c_mod[ad], start_bit, field_size, val)
        else:
            # else check if current exists, and read if not.  Then create update from current and mask
            if ad not in self.i2c_current:
                self.i2c_current[ad] = self.i2cread(ad)
            self.i2c_mod[ad] =  self.apply_bits(self.i2c_current[ad], start_bit, field_size, val)
        return



    def i2c_update(self):
        for ad in list(self.i2c_mod):
            self.i2cwrite(ad, self.i2c_mod[ad])

        return



    ## Put ADC in shutdown
    def shutdown(self):
        GPIO.output(self.inv_standby_pin, GPIO.LOW)
        time.sleep(.1)
        self.power_status={"ADC":0, 1:0, 2:0, 3:0, 4:0}
        return

    def startup(self):
        GPIO.output(self.inv_standby_pin, GPIO.HIGH)  # take out of standby
        time.sleep(.1)
        return


    def set_sleep(self):
        
        #4. Transition from active mode to sleep mode (again) as required in the system for low-power operation:

        #a. Enter sleep mode by writing to P0_R2 to enable sleep mode
        self.i2cwrite("ADCX140_SLEEP_CFG",0b10010000)
        
        #b. Wait at least 6 ms (when FSYNC= 48 kHz)for the volume to ramp down and for all blocks to power down
        time.sleep(.006)
        
        #c. ReadP0_R119 to check the device shut down and sleep mode status
        while self.i2cread("ADCX140_DEV_STS1") & 0x80 == 0:
            time.sleep(.01)
        return
        
     
    def set_wake(self):
        
        self.i2cwrite("ADCX140_SLEEP_CFG",0b10010001)
        
        time.sleep(.001)
        
        return



    def set_communication(self,samplerate = 48):
        
        lookup={
            48 : 0x44,
            96 : 0x54,
            192: 0x64,
            384: 0x74
            }


        self.i2cwrite("ADCX140_MST_CFG0",0x87) # Enable Master Mode, MCLK is 24.576 MHz
        self.i2cwrite("ADCX140_MST_CFG1",lookup[samplerate]) #bclk to fsync ratio for clock and sample rate
        self.i2cwrite("ADCX140_GPIO_CFG0",0xa0) #configureGPIO1as MCLK input
        
        self.samplerate_status = samplerate
        return


    def set_power_config(self):
        #set analog supply using internal 1.8v regulator
        #set the quick charge rate for the Vref capacitor to 50msec
        #take device out of sleep mode
        self.i2cwrite("ADCX140_SLEEP_CFG",0b10010001)
        
        #Keep DREG active until device cleanly shuts down
        #Charge AC coupling capacitors for 50msec
        self.i2cwrite("ADCX140_SHDN_CFG",0b00111000)
        #i2cwrite("ADCX140_BIAS_CFG",0b00010000)  #mic bias of 3.014v, full scale 2Vrms
        #i2cwrite("ADCX140_DEV_STS0",0b11000000)  # power up ch1 adn ch2
        return

    def set_adc_power(self, mic_bias="ON", vref_volt=2.75, mic_bias_volt="1.096VREF", change_input_pwr_while_recording=False):
        # vref_volt can be 2.75, 2.5, 1.375
        # mic_bias_volt can be "VREF", "1.096VREF", "AVDD"
        # mic_bias can be "ON", or "OFF"
        
        
        lookup_volt = {2.75: 0, 2.5: 1, 1.375 : 2}
        lookup_mic_bias_volt = {"VREF": 0, "1.096VREF": 1, "AVDD": 6}
        
        self.i2c_bits("ADCX140_BIAS_CFG", 0, 2, lookup_volt[vref_volt])
        self.i2c_bits("ADCX140_BIAS_CFG", 4, 3, lookup_mic_bias_volt[mic_bias_volt])
        self.i2c_bits("ADCX140_PWR_CFG",7,1,(mic_bias == "ON"))
        
        self.i2c_bits("ADCX140_PWR_CFG",4,1,change_input_pwr_while_recording)
        self.i2c_bits("ADCX140_PWR_CFG",2,2,change_input_pwr_while_recording)
        
        self.i2c_update()
        
        #f. Power-up the ADC and PLL by writing to P0_R117
        self.i2c_bits("ADCX140_PWR_CFG",5,2,0b11)
        self.i2c_update()
        self.power_status["ADC"] = 1

        return
                 

    def set_input_power(self,channel_list, power="ON", enable = True):
        
        lookup_power = { 1:7, 2:6, 3:5, 4:4}
        lookup_enable = {1:7, 2:6, 3:5, 4:4}
        
        
        for channel in channel_list:
            self.i2c_bits("ADCX140_DEV_STS0", lookup_power[channel], 1, (power == "ON"))
            self.i2c_bits("ADCX140_IN_CH_EN", lookup_enable[channel], 1, enable)
            self.power_status[channel]= (power == "ON")*1
            
        self.i2c_update()
        return



    def set_input(self,channel, in_type="MIC", config="DIFF", coupling="AC", impedance=2.5, dynamic_range_processing="OFF"):
        
        #in_type can be "MIC" or "LINE"
        #config can be "DIFF", "SINGLE", or "PDM"
        #coupling can be "AC" or "DC"
        #impedance can be 2.5, 10, 20 k ohm
        #dynamic_range_processing can be "ON" or "OFF"  - covers both AGC or DRE
        
        lookup_imp = { 2.5 : 0, 10 : 1, 20 : 2}
        lookup_config = {"DIFF":0, "SINGLE":1, "PDM":2}
        
        
        
        
        
        
        
        base_addr = {1: "ADCX140_CH1_CFG0", 2: "ADCX140_CH2_CFG0",
                     3: "ADCX140_CH3_CFG0", 4: "ADCX140_CH4_CFG0"}

        ad = base_addr[channel]
        
        
        
        
        self.i2c_bits(ad, 2, 2, lookup_imp[impedance])
        self.i2c_bits(ad, 4, 1, (coupling == "DC"))
        self.i2c_bits(ad, 5, 2, lookup_config[config])
        self.i2c_bits(ad, 7, 1, (in_type == "LINE"))
        self.i2c_bits(ad, 0, 1, (dynamic_range_processing == "ON"))
        self.i2c_update()
        
        return


    def set_analog_gain(self,channel, analog_gain_db=20):
        # should be set before adc power on
        # analog_gain_db is int from 0 to 42 dB

        if (self.power_status[channel] == 1) or (self.power_status["ADC"] == 1):
            print("Can not change analog gain with ADC or channel powered")
            return 0
        
        base_addr = {1: "ADCX140_CH1_CFG1", 2: "ADCX140_CH2_CFG1",
                     3: "ADCX140_CH3_CFG1", 4: "ADCX140_CH4_CFG1"}
        
        analog_gain_db = min(max(analog_gain_db,0),42)
        
        val = int(analog_gain_db*4.0)
        
        self.i2cwrite(base_addr[channel],val)
        self.a_gain_db[channel-1] = val/4
        
        return val/4


    def set_digital_gain(self,channel, digital_gain_db = 0.0, muted=False, soft_step=True, ganged=False):
        
        # digital gain from -100dB to 27dB in 0.5dB steps can be changed while recording
        # soft_step can be True or False
        # ganged can be True or False.  when ganged is True, all channels controlled by channel 1
        
        digital_gain_db = min(max(digital_gain_db,-100),27)
        
        base_addr = {1: "ADCX140_CH1_CFG2", 2: "ADCX140_CH2_CFG2",
                     3: "ADCX140_CH3_CFG2", 4: "ADCX140_CH4_CFG2"}
        
        val = int((digital_gain_db+100.0)*2.0 +1.0)
        
        if muted : val = 0
        
        
        self.i2cwrite(base_addr[channel],val)
        self.i2c_bits("ADCX140_DSP_CFG1", 4, 1, (soft_step == False))
        self.i2c_bits("ADCX140_DSP_CFG1", 7, 1, ganged)
        self.i2c_update()
        
        self.d_gain_db[channel-1] = (val-1)/2 - 100
            
        return (val-1)/2 - 100

    def set_pre_input_gain(self,channel,pre_input_gain_db = 0.0):
        self.pre_input_gain_db[channel-1] = pre_input_gain_db 
        return pre_input_gain_db

    def set_digital_gain_calibration(self,channel, calibration_db = 0.0):
        
        # calibration_db can be changed from -0.8dB to +0.7dB in 0.1dB steps
        calibration_db = min(max(calibration_db,-0.8),0.7)
        
        base_addr = {1: "ADCX140_CH1_CFG3", 2: "ADCX140_CH2_CFG3",
                     3: "ADCX140_CH3_CFG3", 4: "ADCX140_CH4_CFG3"}
        
        val = int(calibration_db*10.0 +8.0)
        self.i2cwrite(base_addr[channel],val)
        return (val-8)/10

    def set_phase_calibration(self,channel, calibration_cycles = 0.0):
        
        # calibration_cycles can be changed from 0 to 255 cycles of the modulator clock
        # modulator clock has a frequency of 6.144 MHz (48K mult samples) or 5.6448 (44.1K mult samples)
        
        calibration_cycles = min(max(calibration_cycles,0),255)
        
        base_addr = {1: "ADCX140_CH1_CFG4", 2: "ADCX140_CH2_CFG4",
                     3: "ADCX140_CH3_CFG4", 4: "ADCX140_CH4_CFG4"}
        
        val = int(calibration_cycles)
        self.i2cwrite(base_addr[channel],val)
        return val

     
    def set_filters(self,high_pass_cutoff="LOW", decimation_response="LINEAR PHASE"):
        # high_pass_cutoff can be "PROG", "LOW" (.00025 x Fs), "MEDIUM" (.002 x Fs), or "HIGH" (.008 x Fs) where Fs is sampling frequency
        # "PROG" is used for programmed DSP parameters
        
        # decimation_response can be "LINEAR PHASE", "LOW LATENCY", "ULTRA-LOW LATENCY"
        
        # returns the 3dB low pass cutoff in Hz (except for "PROG")
        
        hp_filter_lookup = {"PROG": 0b00, "LOW": 0b01, "MEDIUM": 0b10, "HIGH": 0b11}
        factor_lookup = {"PROG": 0, "LOW": 0.00025, "MEDIUM": 0.002, "HIGH": 0.008}
        
        dec_lookup = {"LINEAR PHASE":0, "LOW LATENCY":1, "ULTRA-LOW LATENCY":2}
        
        self.i2c_bits("ADCX140_DSP_CFG0", 0, 2, hp_filter_lookup[high_pass_cutoff])
        self.i2c_bits("ADCX140_DSP_CFG0", 4, 2, dec_lookup[decimation_response])
        self.i2c_update()
        
        return self.samplerate_status*factor_lookup[high_pass_cutoff]
        


    def set_summer(self,sum_type = "NONE"):
        
        # sum_type can be "NONE" which is normal operation
        # "SUM-PAIRS" combines 1+2 -> 1, 1+2 -> 2, 3+4 -> 3, 3+4 -> 4
        # "SUM-QUAD" combines 1+2+3+4 -> 1, 1+2+3+4 -> 2, 1+2+3+4 -> 3, 1+2+3+4 -> 4,
        sum_lookup = {
            "NONE": 0b00,
            "SUM-PAIRS": 0b01,
            "SUM-QUAD": 0b10
            }
        self.i2c_bits("ADCX140_DSP_CFG0", 2, 2, sum_lookup[sum_type])
        self.i2c_update()
        
    def set_dynamic_range_enhancer(self, trigger_threshold_db = -54, max_gain_db=24, enable_dre=True ):
        # trigger_threshold between -12 and -66dB in steps of 6dB .  -30dB is upper limit per TI
        # max_gain_db between 2 and 26 dB.
        # enable_dre selects the DRE and turns off the AGC
        
        trigger_threshold_db=min(max(trigger_threshold_db,-66),-12)
        trigger_val = int((12.0-trigger_threshold_db)/6.0)
        
        max_gain_db=min(max(max_gain_db,2),26)
        max_gain_val = int((max_gain_db-2)/2.0)
        
        self.i2c_bits("ADCX140_DRE_CFG0", 4, 4, trigger_val)
        self.i2c_bits("ADCX140_DRE_CFG0", 0, 4, max_gain_val)
        self.i2c_bits("ADCX140_DSP_CFG1", 3, 1, not(enable_dre))
        self.i2c_update()
        return ( 12-(trigger_val*6),(max_gain_val*2)+2)
        
    def set_automatic_gain_control(self):
        return

    def set_mixer(self,out_channel,mixer_coefs):
        return



    def set_output_enable(self,channel_list,enable=True):

        lookup_enable = {1:7, 2:6, 3:5, 4:4}
        
        for channel in channel_list:
            self.i2c_bits("ADCX140_ASI_OUT_CH_EN", lookup_enable[channel], 1, enable)
        self.i2c_update()
        return
    
    
    def set_output_slot(self,channel, slot_side, slot_num=0):
        
        #slot_num can be 0-31.  For simple I2S, slot 0 is used
        #slot_side can be "LEFT" or "RIGHT"
        
        base_addr = {1: "ADCX140_ASI_CH1", 2: "ADCX140_ASI_CH2",
                     3: "ADCX140_ASI_CH3", 4: "ADCX140_ASI_CH4"}
        
        slot_side_lookup = {"LEFT":0, "RIGHT":32}
        
        val = slot_num + slot_side_lookup[slot_side]
        
        self.i2c_bits(base_addr[channel], 0, 6, val)
        self.i2c_update()
        
        return    
        
    
    


    def set_output_type(self,protocol="I2S", word_length=32, compatibility= True):
        # protocol can be "I2", "LJ", or "TDM"
        # word_length can be 32, 24, 20, 16
        # compatibility True means correction to I2S
        # see SBAA382 doc "Configuring and Operating TLV320ADCc140 as Audio Bus Master"
        protocol_lookup = {"TDM": 0, "I2S": 1, "LJ":2}
        word_length_lookup = {16:0, 20:1, 24:2, 32:3}
        
        self.i2c_bits("ADCX140_ASI_CFG0", 6, 2, protocol_lookup[protocol])
        self.i2c_bits("ADCX140_ASI_CFG0", 4, 2, word_length_lookup[word_length])
        if compatibility and protocol == "I2S":
            #I2S CompatibilityWithZeroOffset(I2S only)
            #TLV320AICx140 devices can comply with the I2S bus format with zero offset by modifying
            # the default left justified format to fit the I2S format requirements, as follows:
            # •  BCLK_POL(Page0, ASI_CFG0Register0x07,Bit 2) = 1
            self.i2c_bits("ADCX140_ASI_CFG0", 2, 1,1)
            #•  TX_EDGE(Page0, ASI_CFG0Register0x07,Bit 1) = 1
            self.i2c_bits("ADCX140_ASI_CFG0", 1, 1,1)
            # •  ASI_FORMAT(Page0, ASI_CFG0Register0x07,Bits 7-6) = 2’b10 (LJFformat)
            self.i2c_bits("ADCX140_ASI_CFG0", 6, 2,2)
            #•  FSYNC_POL(Page0, ASI_CFG0Register0x07,Bit 3) = 1
            self.i2c_bits("ADCX140_ASI_CFG0", 3, 1,1)
        
        #i2cwrite("ADCX140_ASI_CFG0",0b10111110)  # 32 bit 2Ch I2S
        
        self.i2c_bits("ADCX140_ASI_CFG0", 4, 2, word_length_lookup[word_length])
            
        self.i2c_update()

        
        
        return





    def get_status(self):
        
        #ASI_STS to get clock error status
        
        return








