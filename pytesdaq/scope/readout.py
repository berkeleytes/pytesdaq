import time
import numpy as np
from PyQt5.QtCore import QCoreApplication
from matplotlib import pyplot as plt
import pytesdaq.daq as daq
import pytesdaq.config.settings as settings
from pytesdaq.utils import  arg_utils
import pytesdaq.io.redis as redis
import pytesdaq.io.hdf5 as hdf5
from pytesdaq.analyzer import analyzer


class Readout:
    
    def __init__(self):
            
        
        #self._web_scope = web_scope

        # data source: 
        self._data_source = 'niadc'


        # ADC device 
        self._adc_name = 'adc1'


        # initialize db/adc
        self._daq = None
        self._redis = None
        self._hdf5 = None

        # Is running flag
        self._is_running = False

        # data configuration
        self._data_config = dict()

        # qt UI / trace display
        self._is_qt_ui = False
        self._first_draw = True
        self._plot_ref = None
        self._selected_channel_list = list()
        self._axes=[]
        self._canvas = []
        self._status_bar = []
        self._colors = dict()
        self._enable_auto_scale = True
        self._nb_bins = 0
     
        
        
        # initialize analysis config
        self._analysis_config = dict()
        self._analysis_config['unit'] = 'ADC'
        self._analysis_config['norm'] = 'None'
        self._analysis_config['calc_psd'] = False
        self._analysis_config['enable_running_avg'] = False
        self._analysis_config['reset_running_avg'] = False
        self._analysis_config['nb_events_avg'] = 1
        self._analysis_config['calc_didv'] = False
        self._analysis_config['enable_pilup_rejection'] = False
      
        

        # instanciate analyzer
        self._analyzer = analyzer.Analyzer()
        
       


    def register_ui(self,axes,canvas,status_bar,colors):
        self._is_qt_ui = True
        self._axes = axes
        self._canvas = canvas
        self._status_bar = status_bar

        # need to divide by 255
        for key,value in colors.items():
            color = (value[0]/255, value[1]/255,value[2]/255)
            self._colors[key] = color


  
    def select_channels(self, channels):

        self._first_draw = True
        self._analysis_config['reset_running_avg'] = True
        self._selected_channel_list = channels



    def configure(self,data_source, adc_name = 'adc1', channel_list=[],
                  sample_rate=[], trace_length=[],
                  voltage_min=[], voltage_max=[],trigger_type=4,
                  file_list=[]):
        

        
        # check if running
        if self._is_running:
            print('WARNING: Need to stop display first')
            return False
            
        # data source 
        self._data_source = data_source

        # adc name 
        self._adc_name = adc_name


        # read configuration file
        self._config = settings.Config()
        self._data_config = dict()

        # NI ADC source
        if self._data_source == 'niadc':

            # check
            if not channel_list or not adc_name:
                error_msg = 'ERROR: Missing channel list or adc name!'
                return error_msg

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
                nb_samples = round(self._data_config['sample_rate']*trace_length/1000)
                self._data_config['nb_samples'] = int(nb_samples)
            if voltage_min:
                self._data_config['voltage_min'] = float(voltage_min)
            if voltage_max:
                self._data_config['voltage_max'] = float(voltage_max)
            
            self._data_config['trigger_type'] = int(trigger_type)

            adc_config = dict()
            adc_config[adc_name] =  self._data_config
            self._daq.set_adc_config_from_dict(adc_config)

  
        # Redis
        elif self._data_source == 'redis':

            self._redis = redis.RedisCore()
            self._redis.connect()
        
        
        # hdf5
        elif self._data_source == 'hdf5':

            if not file_list:
                error_msg = 'ERROR from readout: No files provided'
                return error_msg

            self._hdf5 = hdf5.H5Core()
            self._hdf5.set_files(file_list)
            
                
    
        return True



    def stop_run(self):
        self._do_stop_run = True


    def clear_daq(self):
        self._do_stop_run = True
        if self._data_source == 'niadc':
            self._daq.clear()    
       

    def is_running(self):
        return self._is_running


        
    def update_analysis_config(self,norm = None, unit= None, calc_psd =None, calc_didv = None, 
                               enable_pileup_rejection =None,
                               enable_running_avg = None, nb_events_avg=None):
        
        
        
        if norm is not None:
            self._analysis_config['norm'] = norm
            
        if unit is not None:
            self._analysis_config['unit'] = unit
        
        if calc_psd is not None:
            self._analysis_config['calc_psd'] = calc_psd
        
        if calc_didv is not None:
            self._analysis_config['calc_didv'] = calc_didv
        
        if enable_pileup_rejection is not None:
            self._analysis_config['enable_pileup_rejection'] = enable_pileup_rejection
        
        if enable_running_avg is not None:
            self._analysis_config['enable_running_avg'] = enable_running_avg
            
        if nb_events_avg is not None:
            self._analysis_config['nb_events_avg'] = nb_events_avg 

            
        # redraw after analysis update
        self._first_draw = True
        

        # reset running avg
        if (norm is not None or unit is not None or 
            calc_psd is not None or calc_didv is not None or 
            enable_pileup_rejection is not None):
            self._analysis_config['reset_running_avg'] = True

        

    def set_auto_scale(self,enable_auto_scale):
        self._enable_auto_scale  = enable_auto_scale
        


    def run(self,save_redis=False,do_plot=False):
        

        # =========================
        # Initialize data container
        # =========================
        data_array = []
        if self._data_source == 'niadc':
            nb_channels = len(self._data_config['channel_list'])
            nb_samples =  self._data_config['nb_samples']
            data_array = np.zeros((nb_channels,nb_samples), dtype=np.int16)
        
            

        # =========================
        # LOOP Events
        # =========================
        self._do_stop_run = False
        self._is_running = True
        self._first_draw = True
        
        while (not self._do_stop_run):
            
            # event QT process
            if self._is_qt_ui:
                QCoreApplication.processEvents()
                

            # ----------------------
            # Get Traces
            # ----------------------

            if self._data_source == 'niadc':

                self._daq.read_single_event(data_array, do_clear_task=False)


            elif self._data_source == 'hdf5':

                data_array, self._data_config = self._hdf5.read_event(include_metadata=True,
                                                                      adc_name=self._adc_name)
                
                
                # if error -> output is a string
                if isinstance(data_array,str):
                    if self._is_qt_ui:
                        self._status_bar.showMessage('INFO: ' + data_array)
                    break

                # add channel list
                self._data_config['channel_list'] = self._data_config['adc_channel_indices']

                if 'event_num' in self._data_config and self._is_qt_ui:
                    current_file = self._hdf5.get_current_file_name()
                    current_file = current_file.split('/')[-1]
                    self._status_bar.showMessage('INFO: File = ' + current_file + ', EventNumber = ' + 
                                                 str(self._data_config['event_num']))
            
            else:
                print('Not implemented')


            # event QT process
            if self._is_qt_ui:
                QCoreApplication.processEvents()
              


            # ------------------
            # Analysis
            # ------------------

            # check selected channels
            channel_num_list = list()
            channel_index_list = list()
            counter = 0
            for chan in self._data_config['channel_list']:
                if chan in self._selected_channel_list:
                    channel_num_list.append(chan)
                    channel_index_list.append(counter)
                counter+=1

            if len(channel_num_list) == 0:
                continue

            selected_data_array = data_array[channel_index_list,:]
            self._data_config['selected_channel_list'] = channel_num_list
            self._data_config['selected_channel_index'] = channel_index_list


            # process
            selected_data_array = self._analyzer.process(selected_data_array, self._data_config, 
                                                         self._analysis_config)
         
 


            # event QT process
            if self._is_qt_ui:
                QCoreApplication.processEvents()
              

            # ------------------
            # Store in redis
            # ------------------





            # ------------------
            # Display
            # ------------------
        
            if do_plot:
                self._plot_data(selected_data_array,self._analyzer.freq_array)
                
                
          
            # ------------------
            # Clear
            # ------------------
            self._analysis_config['reset_running_avg'] = False




        # =========================
        # Cleanup
        # =========================
        if self._data_source == 'niadc':
            self._daq.clear()    
        self._is_running = False





    def _plot_data(self, data_array,freq_array=[]):


        if self._do_stop_run:
            return


        # chan/bins
        nchan =  np.size(data_array,0)
        nbins =  np.size(data_array,1)


        # sanity checks
        if nchan == 0 or nbins==0:
            return

        if self._plot_ref is None or len(self._plot_ref)!=nchan:
            self._first_draw = True

        if self._analysis_config['calc_psd']:
            if freq_array is None or len(freq_array)!=nbins:
                return


        if self._nb_bins != nbins:
            self._nb_bins = nbins
            self._first_draw = True


        # label
        ylabel = self._analysis_config['unit']
        if self._analysis_config['calc_psd']:
            ylabel = ylabel + '/rtHz'
            
        


        # draw!
        if self._first_draw:
           
            # axes label
            self._axes.clear()
            if self._analysis_config['calc_psd']:
                self._axes.set_xlabel('Hz')
                self._axes.set_ylabel(ylabel)
                self._axes.set_title('PSD')
                self._axes.set_yscale('log')
                self._axes.set_xscale('log')
            else:
                self._axes.set_xlabel('ms')
                self._axes.set_ylabel(ylabel)
                self._axes.set_title('Pulse')
                self._axes.set_yscale('linear')
                self._axes.set_xscale('linear')

            # x axis value
            dt = 1/self._data_config['sample_rate']
            x_axis =np.arange(0,nbins)*1e3*dt
            if self._analysis_config['calc_psd'] and len(freq_array)!=0:
                x_axis = freq_array
          
            self._plot_ref = [None]*nchan
            for ichan in range(nchan):
                chan = self._data_config['selected_channel_list'][ichan]
                self._plot_ref[ichan], = self._axes.plot(x_axis,data_array[ichan],
                                                         color = self._colors[chan]) 
            self._canvas.draw()
            self._first_draw = False
        else:
            
            for ichan in range(nchan):
                self._plot_ref[ichan].set_ydata(data_array[ichan])
            

        if self._enable_auto_scale:
            self._axes.relim()
            self._axes.autoscale_view()
            

        self._axes.grid(which='major',axis='both',alpha=0.5)
        self._axes.grid(which='minor',axis='both',alpha=0.2,ls='dashed')

        self._canvas.draw()
        self._canvas.flush_events()
            
