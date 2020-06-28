"""
Main instrumentation class

"""
import time
import numpy
import pytesdaq.config.settings as settings
import pytesdaq.instruments.feb  as feb
import pytesdaq.io.redis as redis
from pytesdaq.utils import connections
from math import nan


class Control:
    """
    Control TES related instruments
    """
    
    def __init__(self,verbose=True, dummy_mode = True):
        
        # for code development
        self._dummy_mode = dummy_mode
        self._verbose = verbose

        # initialize
        self._config = settings.Config()
        self._squid_controller = self._config.get_squid_controller()
        self._signal_generator = self._config.get_signal_generator()
        self._temperature_controller = self._config.get_temperature_controller()

        # redis
        self._enable_redis = self._config.enable_redis()
        self._read_from_redis = False
        if self._enable_redis:
             self._redis_db = redis.RedisCore()
             self._redis_db.connect()
              
        # readback
        self._enable_readback = self._config.enable_redis()

        # instantiate / check instruments

        # FEB
        if self._squid_controller == 'feb' and not self._dummy_mode:
            address = self._config.get_feb_address()
            if address:
                if self._verbose:
                    print('FEB address: ' + address)
                self._feb_inst = feb.FEB(address)
            else:
                print('ERROR: Unable to find GPIB address')
            
        


        # get connection map
        self._connection_table= self._config.get_adc_connections()
        
               
    @property
    def verbose(self):
        return self._verbose
        
    @verbose.setter
    def verbose(self,value):
        self._verbose=value
        
    @property
    def read_from_redis(self):
        return self._read_from_redis
        
    @read_from_redis.setter
    def read_from_redis(self,value):
        if value and not self._enable_redis:
            print('WARNING: unable to read from Redis! Redis DB not enabled...)')
        else:
            self._read_from_redis=value
        


    def set_tes_bias(self, bias, 
                     tes_channel=str(),
                     detector_channel= str(),
                     adc_id=str(), adc_channel=str()):
        
        """
        Set TES bias 
        """
        try:
            self._set_sensor_val('tes_bias', bias,
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting TES bias')
            return False

        return True
    


    def set_squid_bias(self, bias, 
                       tes_channel=str(),
                       detector_channel= str(),
                       adc_id=str(), adc_channel=str()):
        
        """
        Set SQUID bias 
        """
        try:
            self._set_sensor_val('squid_bias', bias,
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting SQUID bias')
            return False

        return True
    



    def set_squid_lock_point(self, lock_point, 
                             tes_channel=str(),
                             detector_channel= str(),
                             adc_id=str(), adc_channel=str()):
        

        """
        Set SQUID lock point
        """
        try:
            self._set_sensor_val('lock_point', bias,
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting SQUID lock point')
            return False

        return True
    


 
    def set_feedback_gain(self, gain, 
                          tes_channel=str(),
                          detector_channel= str(),
                          adc_id=str(), adc_channel=str()):
        

        """
        Set Feedback gain
        """
        try:
            self._set_sensor_val('feedback_gain', gain,
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting feedback gain')
            return False

        return True
    



    def set_output_offset(self, offset, 
                          tes_channel=str(),
                          detector_channel= str(),
                          adc_id=str(), adc_channel=str()):
        

        """
        Set output offset
        """
        try:
            self._set_sensor_val('output_offset',offset,
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting output offset')
            return False

        return True
    


    def set_output_gain(self, gain, 
                        tes_channel=str(),
                        detector_channel= str(),
                        adc_id=str(), adc_channel=str()):
        

        """
        Set output gain
        """
        try:
            self._set_sensor_val('output_gain',gain,
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting output gain')
            return False

        return True  
            

    def set_feelback_polarity(self, do_invert, 
                                   tes_channel=str(),
                                   detector_channel= str(),
                                   adc_id=str(), adc_channel=str()):
        

        """
        Set feedback loop polarity
        invert = True
        non invert = False
        """
        try:
            self._set_sensor_val('feedback_polarity',bool(do_invert),
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting feedback polarity')
            return False
        
        return True
        
            
    def set_feedback_loop_state(self, do_open, 
                                tes_channel=str(),
                                detector_channel= str(),
                                adc_id=str(), adc_channel=str()):
        

        """
        Set feedback loop open (True) or closed (False)
        """
        try:
            self._set_sensor_val('feedback_open',bool(do_open),
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting feedback loop state (open/closed)')
            return False

        return True   


    def set_source_preamp(self, preamp_source, 
                          tes_channel=str(),
                          detector_channel= str(),
                          adc_id=str(), adc_channel=str()):
        

        """
        Set source to preamp (True) or feedback (False)
        """

        

        try:
            self._set_sensor_val('preamp_source',bool(preamp_source),
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting signal source')
            return False

        return True   



    def connect_signal_gen_feedback(self, do_connect, 
                                    tes_channel=str(),
                                    detector_channel= str(),
                                    adc_id=str(), adc_channel=str()):
        
        
        """
        Set signal generator feedback connection (True) or feedback (False)
        """
        
        

        try:
            self._set_sensor_val('signal_gen_feedback_connection',bool(do_connect),
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting signal generator feedback connection')
            return False

        return True   



    def connect_signal_gen_tes(self, do_connect, 
                               tes_channel=str(),
                               detector_channel= str(),
                               adc_id=str(), adc_channel=str()):
        
        
        """
        Set  connection signal generator TES line (True) or tes (False)
        """
        
        

        try:
            self._set_sensor_val('signal_gen_tes_connection',bool(do_connect),
                                 tes_channel=tes_channel,
                                 detector_channel=detector_channel,
                                 adc_id=adc_id, adc_channel=adc_channel)
        except:
            print('ERROR setting signal generator TES line connection')
            return False

        return True   





    def get_tes_bias(self, 
                     tes_channel=str(),
                     detector_channel= str(),
                     adc_id=str(), adc_channel=str()):
        


        """
        Get TES bias 
        """
        bias = nan
        try:
            bias = self._get_sensor_val('tes_bias',
                                        tes_channel=tes_channel,
                                        detector_channel=detector_channel,
                                        adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting TES bias')
            
        return bias
        
        
    def get_squid_bias(self, 
                       tes_channel=str(),
                       detector_channel= str(),
                       adc_id=str(), adc_channel=str()):
        


        """
        Get SQUID bias 
        """
        bias = nan
        try:
            bias = self._get_sensor_val('squid_bias',
                                        tes_channel=tes_channel,
                                        detector_channel=detector_channel,
                                        adc_id=adc_id, adc_channel=adc_channel)
                                                   
        except:
            print('ERROR getting SQUID bias')
            
        return bias




    def get_lock_point(self, 
                       tes_channel=str(),
                       detector_channel= str(),
                       adc_id=str(), adc_channel=str()):
        


        """
        Get lock point 
        """
        lock_point = nan
        try:
            lock_point = self._get_sensor_val('lock_point',
                                              tes_channel=tes_channel,
                                              detector_channel=detector_channel,
                                              adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting lock point')
            
        return lock_point




    def get_feedback_gain(self, 
                          tes_channel=str(),
                          detector_channel= str(),
                          adc_id=str(), adc_channel=str()):
        


        """
        Get feedback gain

        """
        feedback_gain = nan
        try:
            feedback_gain = self._get_sensor_val('feedback_gain',
                                                 tes_channel=tes_channel,
                                                 detector_channel=detector_channel,
                                                 adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting feedback gain')
            
        return feedback_gain


    def get_output_offset(self, 
                          tes_channel=str(),
                          detector_channel= str(),
                          adc_id=str(), adc_channel=str()):
        


        """
        Get output offset
        """
        output_offset = nan
        try:
            output_offset = self._get_sensor_val('output_offset',
                                                 tes_channel=tes_channel,
                                                 detector_channel=detector_channel,
                                                 adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting output offset')
            
        return output_offset




    def get_output_gain(self, 
                        tes_channel=str(),
                        detector_channel= str(),
                        adc_id=str(), adc_channel=str()):
        


        """
        Get output gain
        """
        output_gain = nan
        try:
            output_gain = self._get_sensor_val('output_gain',
                                                 tes_channel=tes_channel,
                                                 detector_channel=detector_channel,
                                                 adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting output gain')
            
        return output_gain


    def get_feedback_polarity(self, 
                              tes_channel=str(),
                              detector_channel= str(),
                              adc_id=str(), adc_channel=str()):
        


        """
        Get feedback polarity
        """
        feedback_polarity = nan
        try:
            feedback_polarity = self._get_sensor_val('feedback_polarity',
                                                     tes_channel=tes_channel,
                                                     detector_channel=detector_channel,
                                                     adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting  feedback polarity')
            
        return feedback_polarity
            

    def is_feedback_open(self, 
                         tes_channel=str(),
                         detector_channel= str(),
                         adc_id=str(), adc_channel=str()):
        


        """
        Is feedback open
        """

        is_open = nan
        try:
            is_open = self._get_sensor_val('feedback_open',
                                           tes_channel=tes_channel,
                                           detector_channel=detector_channel,
                                           adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting  feedback polarity')
            
        return is_open
            

    def is_source_preamp(self, 
                         tes_channel=str(),
                         detector_channel= str(),
                         adc_id=str(), adc_channel=str()):
        


        """
        Is source preamp
        """

        is_preamp = nan
        try:
            is_preamp = self._get_sensor_val('source_preamp',
                                             tes_channel=tes_channel,
                                             detector_channel=detector_channel,
                                             adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting signal source')
            
        return is_preamp
            


    def is_signal_gen_feedback_connected(self, 
                                         tes_channel=str(),
                                         detector_channel= str(),
                                         adc_id=str(), adc_channel=str()):
        


        """
        Is signal generator connected to feedback
        """
        
        is_connected = nan
        try:
            is_connected = self._get_sensor_val('signal_gen_feedback_connection',
                                                tes_channel=tes_channel,
                                                detector_channel=detector_channel,
                                                adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting signal generator connection')
            
        return is_connected
            


    def is_signal_gen_tes_connected(self, 
                                    tes_channel=str(),
                                    detector_channel= str(),
                                    adc_id=str(), adc_channel=str()):
        
        

        """
        Is signal generator connected to TES line
        """

        is_connected = nan
        try:
            is_connected = self._get_sensor_val('signal_gen_tes_connection',
                                                tes_channel=tes_channel,
                                                detector_channel=detector_channel,
                                                adc_id=adc_id, adc_channel=adc_channel)
            
        except:
            print('ERROR getting signal generator connection')
            
        return is_connected
            




    def _get_sensor_val(self,param_name, 
                        tes_channel=str(),
                        detector_channel= str(),
                        adc_id=str(), adc_channel=str()):
        
        

        if not self._dummy_mode and not self.squid_controller:
            print('ERROR: No SQUID controller, check config')
            return nan
            

        # get readout controller ID and Channel
        controller_id_channel = connections.get_controller_info(self._connection_table,
                                                                tes_channel=tes_channel,
                                                                detector_channel= detector_channel,
                                                                adc_id=adc_id,adc_channel=adc_channel)
        
        controller_id = controller_id_channel[0]
        controller_channel= controller_id_channel[1]

      
        param_val = nan
        
        if not self._read_from_redis:

            if self._squid_controller=='feb':
                # CDMS FEB device
                
                feb_info = self._config.get_feb_subrack_slot(controller_id)
                subrack = int(feb_info[0])
                slot = int(feb_info[1])
            
                if self._verbose:
                    print('Getting setting "' + param_name + '" from FEB')
                    print('(subrack = ' + str(subrack) + ', slot = ' + str(slot) + 
                          ', channel = ' + str(controller_channel) + ')')
                
                if not self._dummy_mode:
                    if param_name == 'tes_bias':
                        param_val = feb.get_phonon_qet_bias(subrack, slot,controller_channel)
                    elif param_name == 'squid_bias':
                        param_val = feb.get_phonon_squid_bias(subrack, slot,controller_channel)
                    elif param_name == 'lock_point':
                        param_val = feb.get_phonon_lock_point(subrack, slot,controller_channel)
                    elif param_name == 'feedback_gain':
                        param_val = feb.get_phonon_feedback_gain(subrack, slot,controller_channel)
                    elif param_name == 'output_offset':
                        param_val = feb.get_phonon_offset(subrack, slot,controller_channel)
                    elif param_name == 'output_gain':
                        param_val = feb.get_phonon_output_gain(subrack, slot,controller_channel)
                    elif param_name == 'feedback_polarity':
                        param_val = feb.get_phonon_feedback_polarity(subrack, slot,controller_channel)
                    elif param_name == 'feedback_open':
                        param_value = feb.is_phonon_feedback_open(subrack, slot,controller_channel)
                    elif param_name == 'source_preamp':
                        param_val = feb.is_phonon_source_preamp(subrack, slot,controller_channel)
                    elif param_name == 'signal_gen_feedback_connection':
                        param_val = feb.is_signal_generator_feedback_connected(subrack, slot,controller_channel)
                    elif param_name == 'signal_gen_tes_connection':
                        param_val = feb.is_signal_generator_tes_connected(subrack, slot,controller_channel)
                    else:
                        pass
                else:
                    param_val= 1

            elif self._squid_controller=='magnicon':
                print('Magnicon')
            else:
                print('ERROR: Unknow SQUID controller "' + 
                      self._squid_controller + '"!')

        else:
            print('ERROR: Reading from redis N/A')

            
            
        return param_val


        
        
    def _set_sensor_val(self,param_name,value, 
                        tes_channel=str(),
                        detector_channel= str(),
                        adc_id=str(),adc_channel=str()):
        
        
        """
        TBD
        """

        if not self._dummy_mode and not self.squid_controller:
            print('ERROR: No SQUID controller, check config')
            return nan
            
            

        # get readout controller ID and Channel
        controller_id_channel = connections.get_controller_info(self._connection_table,
                                                                tes_channel=tes_channel,
                                                                detector_channel= detector_channel,
                                                                adc_id=adc_id,adc_channel=adc_channel)
        
        controller_id = controller_id_channel[0]
        controller_channel= controller_id_channel[1]
        
        # ================
        # Set value
        # ================
      
        if self._squid_controller=='feb':
            # CDMS FEB device
            
            feb_info = self._config.get_feb_subrack_slot(controller_id)
            subrack = int(feb_info[0])
            slot = int(feb_info[1])
            
            if self._verbose:
                print('INFO: Setting ' + param_name + ' to ' + str(value) + ' using FEB:')
                print('subrack = ' + str(subrack) + ', slot = ' + str(slot) + ', channel = ' + 
                      str(controller_channel))
                 
            if not self._dummy_mode:
                if param_name == 'tes_bias':
                    feb.set_phonon_qet_bias(subrack, slot,controller_channel,value)
                elif param_name == 'squid_bias':
                    feb.set_phonon_squid_bias(subrack, slot,controller_channel,value)
                elif param_name == 'lock_point':
                    feb.set_phonon_lock_point(subrack, slot,controller_channel,value)
                elif param_name == 'feedback_gain':
                    feb.set_phonon_feedback_gain(subrack, slot,controller_channel,value)
                elif param_name == 'output_offset':
                    feb.set_phonon_offset(subrack, slot,controller_channel,value)
                elif param_name == 'output_gain':
                    feb.set_phonon_output_gain(subrack, slot,controller_channel,value)
                elif param_name == 'feedback_polarity':
                    feb.set_phonon_feedback_polarity(subrack, slot,controller_channel,value)
                elif param_name == 'feedback_loop_open':
                    feb.set_phonon_feedback_loop(subrack, slot,controller_channel,value)
                elif param_name == 'preamp_source':
                    feb.set_phonon_source_preamp(subrack, slot,controller_channel,value)
                elif param_name == 'signal_gen_feedback_connected':
                    feb.connect_signal_generator_feedback(subrack, slot,controller_channel,value)
                elif param_name == 'signal_gen_tes_connected':
                    feb.connect_signal_generator_tes(subrack, slot,controller_channel,value)
                           
        elif self._squid_controller=='magnicon' and not self._dummy_mode:
            # Magnicon
            print('Magnicon')
            
        else:
            print('ERROR: Unknow SQUID controller "' + 
                  self._squid_controller + '"!')
        
    
        # ================
        # Read back
        # ================
        time.sleep(0.2)
        if self._enable_readback and not self._dummy_mode:
            value_readback= self._get_sensor_val(param_name,
                                                 tes_channel=tes_channel,
                                                 detector_channel=detector_channel,
                                                 adc_id=adc_id, adc_channel=adc_channel)
            
            if self._verbose:
                print('INFO: Parameter ' + param_name)
                print('Value set = ' + str(value))
                print('Value readback = ' + str(value_readback))
        
        
        # ================
        # Redis
        # ================
        time.sleep(0.2)
        if self._enable_redis:
            hash_name = param_name
            hash_key  = controller_id + '/' + controller_channel
            hash_val =  value
            if self._enable_readback:
                hash_val = value_readback
            
            try:
                self._redis_db.add_hash(hash_name, hash_key, hash_val)
            except:
                print('ERROR adding value in redis!')
            
            

    def _get_controller_id_channel(self,
                                   tes_channel=str(),
                                   detector_channel= str(),
                                   adc_id=str(), adc_channel=str()):
        
        
        controller_id_channel = list()
        index_list = [slice(None),slice(None),slice(None),slice(None)]
        if tes_channel:
            index_list[0] = str(tes_channel)
        if detector_channel:
            index_list[1] = str(detector_channel)
        if adc_id:
            index_list[2] = str(adc_id)
        if adc_channel:
            index_list[3] = str(adc_channel)
     
            
        index_tuple = tuple(index_list)
        
        try:
            controller_id_channel = self._connection_table.loc[index_tuple,
                                                              ('controller_id',
                                                               'controller_channel')].values[0]
        except:
            pass

        return controller_id_channel
                
                

    def set_signal_gen_amplitude(self, amplitude):

        """
        Signal Generator Amplitude [mVpp]
        (assume only 1 signal generator available?)

        """
        
        print('Setting signal generator amplitdue to ' + str(amplitude) + 'mV')


    def set_signal_gen_frequency(self, frequency):

        """
        Signal generator frequency [Hz]
        (assume only 1 signal generator available?)

        """
        
        print('Setting signal generator frequency to ' + str(frequency) + 'Hz')


    
    def set_signal_gen_shape(self, shape):

        """
        Signal generator shape
            1. square wave
            2. sine wave
            3. triangle wave
            4. DC constant
            5. arbitrary pulse shape
        """
        
        print('Setting signal generator shape to ' + str(shape)  + 'Hz')

    
    def get_signal_gen_amplitude(self):

        """
        Signal Generator Amplitude [mVpp]
        (assume only 1 signal generator available?)

        """
        
        return 20.0



    def get_signal_gen_frequency(self):

        """
        Signal generator frequency [Hz]
        (assume only 1 signal generator available?)

        """

        return 100.0

    
    def get_signal_gen_shape(self):

        """
        Signal generator shape
        (assume only 1 signal generator available?)
            1. square wave
            2. sine wave
            3. triangle wave
            4. DC constant
            5. arbitrary pulse shape
        """
        
        return 1


    def set_heater(self, percent):
        
        """
        Set heater percent
        
        """
        
        print('Setting heater to  ' + str(percent) + '/%')
        

    
    def get_heater(self):
        
        """
        Set heater percent
        
        """
        return 0

        

    
    def set_temperature(self, temperature):
        
        """
        Iteratively set the temperature by increasing 
        the heater (feedback co
        """
        
        print('Setting heater to  ' + str(temperature) + 'mK')
        
        
    def get_temperature(self, channel=[]):
        
        """
        Get temperature [mK]
        
        """
        return 20
        
        

    def get_resistance(self, channel=[]):
        
        """
        Get resistance [Ohms]
        
        """
        return 99999
         
