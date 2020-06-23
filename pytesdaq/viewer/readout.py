import numpy as np
import pytesdaq.daq as daq
import pytesdaq.config.settings as settings
from pytesdaq.utils import  arg_utils
import numpy as np
from PyQt5.QtCore import QCoreApplication
import time
from matplotlib import pyplot as plt


class Readout:
    
    def __init__(self,data_source='redis'):
            
        
        #self._web_scope = web_scope

        # data source: 
        self._data_source = data_source


        # initialize db/adc
        self._daq = None
        self._redis = None
        self._hdf5 = None

        # Initialize 
        self._is_running = False
        self._first_draw = True
        self._plot_ref = None

        # data configuration
        self._data_config = dict()

        # qt UI
        self._is_qt = False
        self._axes=[]
        self._canvas = []
        self._colors = dict()
        #self._colors = ['k','r','b','g','m','c','y','r']
        


    def register_ui(self,axes,canvas,colors):
        self._is_qt = True
        self._axes = axes
        self._canvas = canvas

        # need to divide by 255
        for key,value in colors.items():
            color = (value[0]/255, value[1]/255,value[2]/255)
            self._colors[key] = color
  
        


    def configure(self,adc_name = str(), channel_list=[],
                  sample_rate=[], trace_length=[],
                  voltage_min=[], voltage_max=[],
                  trigger_type=[]):
        
        
        # check if running
        if self._is_running:
            print('WARNING: Need to stop display first')
            return False




        # check
        if not channel_list or not adc_name:
            error_msg = 'ERROR: Missing channel list or adc name!'
            return error_msg
            


        # read configuration file
        self._config = settings.Config()
                       

        # NI ADC source
        if self._data_source == 'niadc':

            # instantiate daq
            self._daq  = daq.DAQ(driver_name = 'pydaqmx',verbose = False)
            self._daq.lock_daq = True
            
            # configuration
            adc_list = self._config.get_adc_list()
            if adc_name not in adc_list:
                self._daq.clear()
                error_msg = 'ERROR: ADC name "' + adc_name + '" unrecognized!'
                return error_msg
                
                
            self._data_config = self._config.get_adc_setup(adc_name)
            self._data_config['channel_list'] = channel_list
            if sample_rate:
                self._data_config['sample_rate'] = int(sample_rate)
            if trace_length:
                nb_samples = round(config_dict['sample_rate']*trace_length/1000)
                self._data_config['nb_samples'] = int(nb_samples)
            if voltage_min:
                self._data_config['voltage_min'] = float(voltage_min)
            if voltage_max:
                self._data_config['voltage_max'] = float(voltage_max)
            
            self._data_config['trigger_type'] = 3

            adc_config = dict()
            adc_config[adc_name] =  self._data_config
            self._daq.set_adc_config_from_dict(adc_config)


    



        # Redis
        elif self._data_source == 'redis':

            self._redis = redis.RedisCore()
            self._redis.connect()
        
        
        # hdf5
        elif self._data_source == 'hdf5':
            print('HDF5...')
            pass

    
        return True



    def stop_run(self):
        self._do_stop_run = True


    def is_running(self):
        return self._is_running


    def run(self,save_redis=False,do_plot=False):
        

        # =========================
        # Initialize data container
        # =========================\
        self._data_array = []
        self._data_array_avg  = []
        if self._data_source == 'niadc':
            nb_channels = len(self._data_config['channel_list'])
            nb_samples =  self._data_config['nb_samples']
            self._data_array = np.zeros((nb_channels,nb_samples), dtype=np.int16)
            self._data_array_avg = np.zeros((nb_channels,nb_samples), dtype=np.int16)
            

        # =========================
        # LOOP Events
        # =========================
        self._do_stop_run = False
        self._is_running = True
        self._first_draw = True
        
        while (not self._do_stop_run):
            
            # event QT process
            if self._is_qt:
                QCoreApplication.processEvents()
                

            # get traces
            if self._data_source == 'niadc':
                self._daq.read_single_event(self._data_array, do_clear_task=False)
            else:
                print('Not implemented')
                
            if do_plot:
                self._plot_data()
         
       
        # clear
        if self._data_source == 'niadc':
            self._daq.clear()    








    def _plot_data(self):


        # chan/bins
        nchan =  np.size(self._data_array,0)
        nbins =  np.size(self._data_array,1)
                
        if self._first_draw:
            channels = self._data_config['channel_list']
            dt = 1/self._data_config['sample_rate']
            self._axes.clear()
            self._axes.set_xlabel('ms')
            self._axes.set_ylabel('ADC bins')
            self._axes.set_title('Pulse')
            x_axis=np.arange(0, (nbins*dt)*1e3, 1e3*dt)
            self._plot_ref = [None]*nchan
            for ichan in range(nchan):
                self._plot_ref[ichan], = self._axes.plot(x_axis,self._data_array[ichan],
                                                         color = self._colors[ichan])  
            self._canvas.draw()
            self._first_draw = False
        else:
            for ichan in range(nchan):
                self._plot_ref[ichan].set_ydata(self._data_array[ichan])
                        
        self._axes.relim()
        self._axes.autoscale_view()
        self._canvas.draw()
        self._canvas.flush_events()
            