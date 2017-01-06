import visa
import time

TRIES_BEFORE_FAILURE = 10
RETRY_SLEEP_TIME = 0.010  # in seconds

class ThorlabsPM100D(object):
    """
    Thorlabs PM100D power meter
    
    uses the PyVISA 1.5 library to communicate over USB.
    """

    
    def __init__(self, port="USB0::0x1313::0x8078::P0005750::INSTR", debug=False):
    
        self.port = port
        self.debug = debug

        self.visa_resource_manager = visa.ResourceManager()
    
        if debug: self.visa_resource_manager.list_resources()
    
        self.pm = self.visa_resource_manager.get_instrument(port)
    
        self.idn = self.ask("*IDN?")
        
        self.sensor_idn = self.ask("SYST:SENS:IDN?")
        
        self.write("CONF:POW") # set to power meaurement

        self.wavelength_min = float(self.ask("SENS:CORR:WAV? MIN"))
        self.wavelength_max = float(self.ask("SENS:CORR:WAV? MAX"))
        self.get_wavelength()
        
        self.get_attenuation_dB()
        
        self.write("SENS:POW:UNIT W") # set to Watts
        self.power_unit = self.ask("SENS:POW:UNIT?")


        self.get_auto_range()
                
        self.get_average_count()
        
        self.get_power_range()        
        self.measure_power()
        self.measure_frequency()
        
        
    
    def ask(self, cmd):
        if self.debug: print "PM100D ask ", repr(cmd)
        resp = self.pm.ask(cmd)
        if self.debug: print "PM100D resp --->", repr(resp)
        return resp
    
    def write(self, cmd):
        if self.debug: print "PM100D write", repr(cmd)
        resp = self.pm.write(cmd)
        if self.debug: print "PM100D written --->", repr(resp)
        
    def get_wavelength(self):
        try_count = 0
        while True:
            try:
                self.wl = float(self.ask("SENS:CORR:WAV?"))
                if self.debug: print "wl:", repr(self.wl)
                break
            except:
                if try_count > 9:
                    print "Failed to get wavelength."
                    break
                else:
                    time.sleep(RETRY_SLEEP_TIME)  #take a rest..
                    try_count = try_count + 1
                    print "trying to get the wavelength again.."
        return self.wl
    
    def set_wavelength(self, wl):
        try_count = 0
        while True:
            try:
                self.write("SENS:CORR:WAV %f" % wl)
                time.sleep(0.005) # Sleep for 5 ms before rereading the wl.
                break
            except:
                if try_count > 9:
                    print "Failed to set wavelength."
                    time.sleep(0.005) # Sleep for 5 ms before rereading the wl.
                    break
                else:
                    time.sleep(RETRY_SLEEP_TIME)  #take a rest..
                    try_count = try_count + 1
                    print "trying to set wavelength again.."

        return self.get_wavelength()
    
    def get_attenuation_dB(self):
        # in dB (range for 60db to -60db) gain or attenuation, default 0 dB
        self.attenuation_dB = float( self.ask("SENS:CORR:LOSS:INP:MAGN?") )
        if self.debug: print "attenuation_dB", self.attenuation_dB
        return self.attenuation_dB

    
    def get_average_count(self):
        """each measurement is approximately 3 ms.
        returns the number of measurements
        the result is averaged over"""
        self.average_count = int( self.ask("SENS:AVER:COUNt?") )
        if self.debug: print "average count:", self.average_count
        return self.average_count
    
    def set_average_count(self, cnt):
        """each measurement is approximately 3 ms.
        sets the number of measurements
        the result is averaged over"""
        self.write("SENS:AVER:COUNT %i" % cnt)
        return self.get_average_count()
            
    
    def measure_power(self):
        self.power = float(self.ask("MEAS:POW?"))
        if self.debug: print "power:", self.power
        return self.power
        
    def get_power_range(self):
        #un tested
        self.power_range = self.ask("SENS:POW:RANG:UPP?") # CHECK RANGE
        if self.debug: print "power_range", self.power_range
        return self.power_range


    def set_power_range(self, range):
        #un tested
        self.write("SENS:POW:RANG:UPP {}".format(range))


    
    def get_auto_range(self):
        resp = self.ask("SENS:POW:RANG:AUTO?")
        if True:
            print repr(resp)
        self.auto_range = bool(int(resp))
        return self.auto_range
    
    def set_auto_range(self, auto = True):
        print "set_auto_range", auto
        if auto:
            self.write("SENS:POW:RANG:AUTO ON") # turn on auto range
        else:
            self.write("SENS:POW:RANG:AUTO OFF") # turn off auto range
    
    
    def measure_frequency(self):
        self.frequency = self.ask("MEAS:FREQ?")
        if self.debug: print "frequency", self.frequency
        return self.frequency


    def get_zero_magnitude(self):
        resp = self.ask("SENS:CORR:COLL:ZERO:MAGN?")
        if self.debug:
            print "zero_magnitude", repr(resp)
        self.zero_magnitude = float(resp)
        return self.zero_magnitude
        
    def get_zero_state(self): 
        resp = self.ask("SENS:CORR:COLL:ZERO:STAT?")
        if self.debug:
            print "zero_state", repr(resp)
        self.zero_state = bool(int(resp))
        if self.debug:
            print "zero_state", repr(resp), '-->', self.zero_state
        return self.zero_state
    
    def run_zero(self):
        resp = self.ask("SENS:CORR:COLL:ZERO:INIT")
        return resp
    
    def get_photodiode_response(self):
        resp = self.ask("SENS:CORR:POW:PDIOde:RESP?")
        #resp = self.ask("SENS:CORR:VOLT:RANG?")
        #resp = self.ask("SENS:CURR:RANG?")
        if self.debug:
            print "photodiode_response (A/W)", repr(resp)
        
        self.photodiode_response = float(resp) # A/W
        return self.photodiode_response 
    
    def measure_current(self):
        resp = self.ask("MEAS:CURR?")
        if self.debug:
            print "measure_current", repr(resp)
        self.current = float(resp)
        return self.current
    
    def get_current_range(self):
        resp = self.ask("SENS:CURR:RANG:UPP?")
        if self.debug:
            print "current_range (A)", repr(resp)
        self.current_range = float(resp)
        return self.current_range
        
    def close(self):
        return self.pm.close()

if __name__ == '__main__':
    
    power_meter = ThorlabsPM100D(debug=True)
    power_meter.get_wavelength()
    power_meter.get_average_count()
    power_meter.measure_power()