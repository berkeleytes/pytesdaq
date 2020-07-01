"""
Main Frame Window
"""
import sys
from PyQt5 import QtCore, QtGui, QtWidgets
from matplotlib import pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT  as NavigationToolbar
from matplotlib.figure import Figure
from pytesdaq.viewer import readout
from glob import glob
import os

class MainWindow(QtWidgets.QMainWindow):
    
    def __init__(self):
        super().__init__()
        
       

        # initialize attribute
        self._data_source = 'niadc'
        self._file_list = list()
        self._select_hdf5_dir = False
        self._default_data_dir = '/data/analysis'


        # initalize main window
        self.setWindowModality(QtCore.Qt.NonModal)
        self.resize(900, 700)
        self.setStyleSheet("background-color: rgb(211, 252, 255);")
        self.setTabShape(QtWidgets.QTabWidget.Rounded)
        self.setWindowTitle("Pulse Viewer")



        # channel color map
        self._channels_color_map = {0:(0, 85, 255),
                                    1:(255, 0, 0),
                                    2:(0, 170, 127),
                                    3:(170, 0, 255),
                                    4:(170, 116, 28),
                                    5:(15, 235, 255),
                                    6:(255, 207, 32),
                                    7:(121, 121, 121)}
        


        # channel list
        self._channel_list = list()

        # setup frames
        self._init_main_frame()
        self._init_title_frame()
        self._init_control_frame()
        self._init_display_frame()
        self._init_channel_frame()
        self._init_tools_frame()

        # temporary
        self._tools_frame.setEnabled(False)
        self.show()
        

        # run control
        self._is_running = False
        self._stop_request = False
   

         # initialize readout
        self._readout = []
        self.initialize_readout()



    def initialize_readout(self):
        self._readout = readout.Readout()
        self._readout.register_ui(self._axes,self._canvas, self.statusBar(),
                                  self._channels_color_map)
        
    
    def closeEvent(self,event):
        """
        This function is called when exiting window
        superse base class
        """

        print("Exiting Pulse Display UI")
        



    def _handle_display(self):
        """
        Handle display. Called when clicking on display waveform 
        """


        if self._is_running:

            # Stop run
            self._readout.stop_run()
            self._is_running=False

            # change button display
            self._set_display_button(False)

            # enable
            self._data_source_tabs.setEnabled(True)
            self._source_combobox.setEnabled(True)

            # status bar
            self.statusBar().showMessage("Display Stopped")
          
            
        else:


            # disable
            self._data_source_tabs.setEnabled(False)
            self._source_combobox.setEnabled(False)


            if self._data_source  == 'niadc':
                
                # get all channels
                channel_list = list(range(8))
                status = self._readout.configure('niadc',adc_name="adc1",channel_list=channel_list,
                                                 sample_rate=1250000)

                # error
                if isinstance(status,str):
                    self.statusBar().showMessage(status)
                    return

            elif self._data_source  == 'hdf5':
                
                # check selection done
                if not self._file_list:
                    self.statusBar().showMessage("WARNING: No files selected!")  
                    return

                status = self._readout.configure('hdf5', file_list = self._file_list)

                # error
                if isinstance(status,str):
                    self.statusBar().showMessage(status)
                    return
            
            else:
                self.statusBar().showMessage("WARNING: Redis not implemented")  
                return



            # status bar
            self.statusBar().showMessage("Running...")
          
            # run 
            self._set_display_button(True)
            self._is_running=True
            self._readout.run(do_plot=True)

            # enable
            self._data_source_tabs.setEnabled(True)
            self._source_combobox.setEnabled(True)

            # status bar
            self.statusBar().showMessage("Run stopped...")
          

  
    def _handle_source_selection(self):
        
        # get source
        data_source = str(self._source_combobox.currentText())
        
        # select tab
        if data_source== "Redis":
            self._data_source  = 'redis'

            self._redis_tab.setEnabled(True)
            self._hdf5_tab.setEnabled(False)
            self._niadc_tab.setEnabled(False)
            
            self._data_source_tabs.setCurrentWidget(self._redis_tab)

        elif data_source== "HDF5":
            self._data_source  = 'hdf5'
            
            self._redis_tab.setEnabled(False)
            self._hdf5_tab.setEnabled(True)
            self._niadc_tab.setEnabled(False)

            self._data_source_tabs.setCurrentWidget(self._hdf5_tab)

        elif data_source== "ADC Device":
            self._data_source  = 'niadc'

            self._redis_tab.setEnabled(False)
            self._hdf5_tab.setEnabled(False)
            self._niadc_tab.setEnabled(True)

            self._data_source_tabs.setCurrentWidget(self._niadc_tab)

        else:
            print("WARNING: Unknown selection")



    def _handle_hdf5_selection_type(self):

        if self._hdf5_dir_radiobutton.isChecked():
            self._select_hdf5_dir = True
        else:
            self._select_hdf5_dir = False
                

    def _handle_hdf5_selection(self):
        """
        Handle hdf5 selection. 
        Called when clicking on select HDF5
        """
        options = QtWidgets.QFileDialog.Options()
        options |= QtWidgets.QFileDialog.DontUseNativeDialog

        files = list()
        if not self._select_hdf5_dir:
            files, _ = QtWidgets.QFileDialog.getOpenFileNames(self,"Select File (s)",self._default_data_dir,
                                                              "HDF5 Files (*.hdf5)", options=options)
        else:
            options |= QtWidgets.QFileDialog.ShowDirsOnly  | QtWidgets.QFileDialog.DontResolveSymlinks
            dir = QtWidgets.QFileDialog.getExistingDirectory(self,"Select Directory",
                                                             self._default_data_dir,options=options)
                                 

            if os.path.isdir(dir):
                files = glob(dir+'/*_F*.hdf5')

        if not files:
            self.statusBar().showMessage('No file have been selected!')
        else:
            self.statusBar().showMessage('Number of files selected = ' + str(len(files)))
            self._file_list = files
            self._file_list.sort()



    def _handle_channel(self):
        """
        Handle channel buttons selection (Signal/Slot connection)
        """

        # get sender
        button = self.sender()

        # get channel number
        object_name = str(button.objectName())
        name_split =  object_name.split('_')
        channel_num = int(name_split[1])

        # change color
        if button.isChecked():
            # change color
            button.setStyleSheet("background-color: rgb(226, 255, 219);")

            # remove from list
            if self._channel_list and channel_num in self._channel_list:
                self._channel_list.remove(channel_num)
        else:

            # change color
            color = self._channels_color_map[channel_num]
            color_str = "rgb(" + str(color[0]) + "," + str(color[1]) + "," + str(color[2]) + ")" 
            button.setStyleSheet("background-color: " + color_str +";")
        
            # add to list
            self._channel_list.append(channel_num)

            # make sure it is unique...
            self._channel_list = list(set(self._channel_list))

        if self._readout:
            self._readout.select_channels(self._channel_list)
            



    def _init_main_frame(self):
        
       
        # add main widget
        self._central_widget = QtWidgets.QWidget(self)
        self._central_widget.setEnabled(True)
        self._central_widget.setObjectName("central_widget")
        self.setCentralWidget(self._central_widget)
        

        # add menubar and status 
        self._menu_bar = self.menuBar()
        self.statusBar().showMessage('Status information')
        

    def _init_title_frame(self):

        # add title frame
        self._title_frame = QtWidgets.QFrame(self._central_widget)
        self._title_frame.setGeometry(QtCore.QRect(10, 8, 877, 61))
        self._title_frame.setStyleSheet("background-color: rgb(0, 0, 255);")
        self._title_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._title_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._title_frame.setObjectName("titleWindow")

        # add title label
        self._title_label = QtWidgets.QLabel(self._title_frame)
        self._title_label.setGeometry(QtCore.QRect(26, 12, 261, 37))
        font = QtGui.QFont()
        font.setFamily("Sans Serif")
        font.setPointSize(23)
        font.setBold(True)
        font.setWeight(75)
        self._title_label.setFont(font)
        self._title_label.setStyleSheet("color: rgb(255, 255, 127);")
        self._title_label.setObjectName("titleLabel")
        self._title_label.setText("Pulse Display")

        # add device selection box + label
        
        # combo box
        self._device_combobox = QtWidgets.QComboBox(self._title_frame)
        self._device_combobox.setGeometry(QtCore.QRect(470, 16, 93, 29))
        self._device_combobox.setObjectName("deviceComboBox")

        # device label
        device_label = QtWidgets.QLabel(self._title_frame)
        device_label.setGeometry(QtCore.QRect(402, 20, 65, 17))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        device_label.setFont(font)
        device_label.setStyleSheet("color: rgb(200, 255, 255);")
        device_label.setObjectName("deviceLabel")
        device_label.setText("Device:")


        # status widget  
    
        '''
        # status label
        status_label = QtWidgets.QLabel(self._title_frame)
        status_label.setGeometry(QtCore.QRect(674, 24, 59, 15))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        status_label.setFont(font)
        status_label.setStyleSheet("color: rgb(200, 255, 255);")
        status_label.setObjectName("statusLabel")
        status_label.setText("Status:")

        # status widget
        self._status_textbox = QtWidgets.QLabel(self._title_frame)
        self._status_textbox.setGeometry(QtCore.QRect(736, 12, 77, 41))
        font = QtGui.QFont()
        font.setPointSize(10)
        font.setBold(True)
        font.setWeight(75)
        self._status_textbox.setFont(font)
        self._status_textbox.setStyleSheet("background-color: rgb(255, 0, 0);")
        self._status_textbox.setObjectName("statusTextbox")
        self._status_textbox.setText("  Stopped")
        '''



    def _init_control_frame(self):
        
        # add control frame
        self._control_frame = QtWidgets.QFrame(self._central_widget)
        self._control_frame.setGeometry(QtCore.QRect(10, 76, 269, 269))
        self._control_frame.setStyleSheet("background-color: rgb(226, 255, 219);")
        self._control_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._control_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._control_frame.setObjectName("controlFrame")

        # data source tabs
        self._data_source_tabs = QtWidgets.QTabWidget(self._control_frame)
        self._data_source_tabs.setEnabled(True)
        self._data_source_tabs.setGeometry(QtCore.QRect(14, 92, 243, 157))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._data_source_tabs.setFont(font)
        self._data_source_tabs.setAutoFillBackground(False)
        self._data_source_tabs.setStyleSheet("")
        self._data_source_tabs.setTabPosition(QtWidgets.QTabWidget.North)
        self._data_source_tabs.setTabShape(QtWidgets.QTabWidget.Rounded)
        self._data_source_tabs.setIconSize(QtCore.QSize(16, 16))
        self._data_source_tabs.setElideMode(QtCore.Qt.ElideNone)
        self._data_source_tabs.setUsesScrollButtons(False)
        self._data_source_tabs.setDocumentMode(False)
        self._data_source_tabs.setTabsClosable(False)
        self._data_source_tabs.setTabBarAutoHide(False)
        self._data_source_tabs.setObjectName("sourceTabs")
       

          
        # -------------
        # NI device tab
        # -------------
        self._niadc_tab = QtWidgets.QWidget()
        self._niadc_tab.setEnabled(True)
        self._niadc_tab.setStyleSheet("background-color: rgb(243, 255, 242);")
        self._niadc_tab.setObjectName("deviceTab")
        self._data_source_tabs.addTab(self._niadc_tab, "ADC Device")
      

        # --------
        # HDF5 tab
        # --------
        self._hdf5_tab = QtWidgets.QWidget()
        self._hdf5_tab.setEnabled(True)
        self._hdf5_tab.setStyleSheet("background-color: rgb(243, 255, 242);")
        self._hdf5_tab.setObjectName("hdf5Tab")
        self._data_source_tabs.addTab(self._hdf5_tab, "HDF5")
        
        
        self._hdf5_file_radiobutton =  QtWidgets.QRadioButton(self._hdf5_tab)
        self._hdf5_file_radiobutton.setGeometry(QtCore.QRect(120, 40, 101, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._hdf5_file_radiobutton.setFont(font)
        self._hdf5_file_radiobutton.setText("Files")
        self._hdf5_file_radiobutton.setChecked(True)

        self._hdf5_dir_radiobutton =  QtWidgets.QRadioButton(self._hdf5_tab)
        self._hdf5_dir_radiobutton.setGeometry(QtCore.QRect(120, 65, 101, 25))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._hdf5_dir_radiobutton.setFont(font)
        self._hdf5_dir_radiobutton.setText("Directory")
        



        self._hdf5_select_button = QtWidgets.QPushButton(self._hdf5_tab)
        self._hdf5_select_button.setGeometry(QtCore.QRect(36, 32, 71, 65))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._hdf5_select_button.setFont(font)
        self._hdf5_select_button.setStyleSheet("background-color: rgb(162, 162, 241);")
        self._hdf5_select_button.setObjectName("fileSelectButton")
        self._hdf5_select_button.setText("Select \n" "Files/Dir")


        # disable
        self._hdf5_tab.setEnabled(False)
        

        # ---------
        # Redis tab
        # ---------
        self._redis_tab = QtWidgets.QWidget()
        font = QtGui.QFont()
        font.setStrikeOut(False)
        font.setKerning(True)
        self._redis_tab.setFont(font)
        self._redis_tab.setLayoutDirection(QtCore.Qt.LeftToRight)
        self._redis_tab.setAutoFillBackground(False)
        self._redis_tab.setStyleSheet("background-color: rgb(243, 255, 242);")
        self._redis_tab.setObjectName("redisTab")
        self._data_source_tabs.addTab(self._redis_tab, "Redis")
        
        # disable
        self._redis_tab.setEnabled(False)


        # -----------------
        # source selection combox box
        # -----------------
        self._source_combobox = QtWidgets.QComboBox(self._control_frame)
        self._source_combobox.setGeometry(QtCore.QRect(10, 36, 110, 23))
        font = QtGui.QFont()
        font.setBold(False)
        font.setWeight(50)
        self._source_combobox.setFont(font)
        self._source_combobox.setObjectName("sourceComboBox")
        self._source_combobox.addItem("ADC Device")
        self._source_combobox.addItem("HDF5")
        self._source_combobox.addItem("Redis")

        # combo box label
        source_label = QtWidgets.QLabel(self._control_frame)
        source_label.setGeometry(QtCore.QRect(12, 16, 100, 15))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        source_label.setFont(font)
        source_label.setObjectName("sourceLabel")
        source_label.setText("Data Source:")


        # --------------
        # display control
        # --------------
        self._display_control_button = QtWidgets.QPushButton(self._control_frame)
        self._display_control_button.setGeometry(QtCore.QRect(142, 12, 91, 65))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._display_control_button.setFont(font)
        self._display_control_button.setStyleSheet("background-color: rgb(255, 0, 0);")
        self._display_control_button.setObjectName("displayControlButton")
        self._display_control_button.setText("Display \n" "Waveform")
    
        

        # ---------------
        # connect buttons
        # ---------------
        self._display_control_button.clicked.connect(self._handle_display)
        self._hdf5_select_button.clicked.connect(self._handle_hdf5_selection)
        self._hdf5_dir_radiobutton.toggled.connect(self._handle_hdf5_selection_type)
        self._source_combobox.activated.connect(self._handle_source_selection)
       
        
    def _init_display_frame(self):


        # frame
        self._display_frame = QtWidgets.QFrame(self._central_widget)
        self._display_frame.setGeometry(QtCore.QRect(290, 76, 597, 597))
        self._display_frame.setStyleSheet("background-color: rgb(254, 255, 216);")
        self._display_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._display_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._display_frame.setLineWidth(1)
        self._display_frame.setObjectName("DisplayFrame")
        

        

        # canvas
        self._fig = Figure((3.0,3.0), dpi=100)
        #self._fig, self._axes = plt.subplots(sharex=False)
        self._axes = self._fig.add_subplot(111)
        #self._fig.subplots_adjust(hspace=.3)
        self._canvas = FigureCanvas(self._fig)
        #self._canvas.setParent(self._display_frame)
        self._canvas_toolbar = NavigationToolbar(self._canvas,self._display_frame)

        # canvas layout
        canvas_layout_widget = QtWidgets.QWidget(self._display_frame)
        canvas_layout_widget.setGeometry(QtCore.QRect(12, 11, 574, 537))
        canvas_layout = QtWidgets.QVBoxLayout(canvas_layout_widget)
        canvas_layout.setContentsMargins(0, 0, 0, 0)
        canvas_layout.addWidget(self._canvas)
        canvas_layout.addWidget(self._canvas_toolbar)
        


    def _init_channel_frame(self):
        
        # channel frame
        self._channel_frame = QtWidgets.QFrame(self._central_widget)
        self._channel_frame.setGeometry(QtCore.QRect(10, 352, 269, 161))
        self._channel_frame.setStyleSheet("background-color: rgb(226, 255, 219);")
        self._channel_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._channel_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._channel_frame.setLineWidth(2)
        self._channel_frame.setObjectName("ChannelFrame")

        # set grid layout
        channel_layout = QtWidgets.QWidget(self._channel_frame)
        channel_layout.setGeometry(QtCore.QRect(8, 11, 254, 137))
        channel_layout.setObjectName("layoutWidget")
     

        # add grid layout 
        channel_grid_layout = QtWidgets.QGridLayout(channel_layout)
        channel_grid_layout.setContentsMargins(0, 0, 0, 0)
        channel_grid_layout.setObjectName("gridLayout")
        
        # add buttons
        self._channel_buttons = dict()
        row_num = 0
        col_num = 0
        for ichan in range(8):
            # create button
            button = QtWidgets.QPushButton(channel_layout)
            
            # size policy
        
            size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Minimum, 
                                                QtWidgets.QSizePolicy.Expanding)
            size_policy.setHorizontalStretch(0)
            size_policy.setVerticalStretch(0)
            size_policy.setHeightForWidth(button.sizePolicy().hasHeightForWidth())
            button.setSizePolicy(size_policy)
        
            # text font
            font = QtGui.QFont()
            font.setBold(True)
            font.setWeight(75)
            button.setFont(font)
            button.setText("AI" + str(ichan))
            button.setCheckable(True)
            button.toggle()
            # background color
            #color = self._channels_color_map[ichan]
            #color_str = "rgb(" + str(color[0]) + "," + str(color[1]) + "," + str(color[2]) + ")" 
            #button.setStyleSheet("background-color: " + color_str +";")
            button.setObjectName("chanButton_" + str(ichan))
            
            # layout
            channel_grid_layout.addWidget(button, row_num, col_num, 1, 1)
            row_num+=1
            if ichan==3:
                row_num = 0
                col_num = 1

            # connect 
            button.clicked.connect(self._handle_channel)
            
            # save
            self._channel_buttons[ichan] = button




    def _init_tools_frame(self):
        
        # create frame
        self._tools_frame = QtWidgets.QFrame(self._central_widget)
        self._tools_frame.setGeometry(QtCore.QRect(10, 520, 269, 153))
        self._tools_frame.setStyleSheet("background-color: rgb(226, 255, 219);")
        self._tools_frame.setFrameShape(QtWidgets.QFrame.StyledPanel)
        self._tools_frame.setFrameShadow(QtWidgets.QFrame.Raised)
        self._tools_frame.setObjectName("ToolsFrame")

        # Add tools button
        self._tools_button = QtWidgets.QPushButton(self._tools_frame)
        self._tools_button.setGeometry(QtCore.QRect(156, 32, 89, 65))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._tools_button.setFont(font)
        self._tools_button.setStyleSheet("background-color: rgb(162, 162, 241);")
        self._tools_button.setObjectName("toolsButton")
        self._tools_button.setText("Tools")
        
        # add running avg box
        self._running_avg_checkbox = QtWidgets.QCheckBox(self._tools_frame)
        self._running_avg_checkbox.setGeometry(QtCore.QRect(16, 16, 109, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._running_avg_checkbox.setFont(font)
        self._running_avg_checkbox.setObjectName("runningAvgCheckBox")
        self._running_avg_checkbox.setText("Running Avg")

        # running avg spin box
        self._running_avg_spinbox = QtWidgets.QSpinBox(self._tools_frame)
        self._running_avg_spinbox.setEnabled(False)
        self._running_avg_spinbox.setGeometry(QtCore.QRect(34, 40, 85, 21))
        self._running_avg_spinbox.setMaximum(20000)
        self._running_avg_spinbox.setProperty("value", 1)
        self._running_avg_spinbox.setObjectName("runningAvgSpinBox")

        # add lopw pass filter
        self._lpfilter_checkbox = QtWidgets.QCheckBox(self._tools_frame)
        self._lpfilter_checkbox.setGeometry(QtCore.QRect(16, 76, 119, 21))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self._lpfilter_checkbox.setFont(font)
        self._lpfilter_checkbox.setObjectName("lpFilterCheckBox")
        self._lpfilter_checkbox.setText("LP Filter [kHz]")

        # lp filter spin box
        self._lpfilter_spinbox = QtWidgets.QSpinBox(self._tools_frame)
        self._lpfilter_spinbox.setEnabled(False)
        self._lpfilter_spinbox.setGeometry(QtCore.QRect(34, 100, 83, 21))
        self._lpfilter_spinbox.setMinimum(1)
        self._lpfilter_spinbox.setMaximum(500)
        self._lpfilter_spinbox.setObjectName("lpFilterSpinBox")
      

    def closeEvent(self,event):
        print("Exiting Pulse Display UI")
        

    def _set_display_button(self,do_run):
        
        if do_run:
            self._display_control_button.setStyleSheet("background-color: rgb(0, 255, 0);")
            self._display_control_button.setText("Stop \n" "Display")
        else:
            self._display_control_button.setStyleSheet("background-color: rgb(255, 0, 0);")
            self._display_control_button.setText("Display \n" "Waveform")
        
        



if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    ui = MainWindow()
    sys.exit(app.exec_())
