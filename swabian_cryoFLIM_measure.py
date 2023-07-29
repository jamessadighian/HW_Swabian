# -*- coding: utf-8 -*-
"""
Created on Tue Apr 26 11:35:17 2022

@author: James Sadighian
"""

from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
# from PyQt5.QtWidgets import QMainWindow, QApplication, QFileDialog
# from PyQt5.QtCore import QTimer
# from PyQt5 import uic
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
import numpy as np
import time
# import pyqtgraph as pg
import os
from TimeTagger import DelayedChannel, GatedChannel, TimeDifferences, Flim, createTimeTagger, freeTimeTagger

class SwabianCryoFLIM(Measurement):
    
    # this is the name of the measurement that ScopeFoundry uses when displaying your measurement and saving data related to it
    name='swabian_cryoFLIM_measure'
    
    def setup(self):
        """0
        Runs once during App initialization.
        This is the place to load a user interface file,
        define settings, and set up data structures. 
        """
        
        self.display_update_period = 0.1 #seconds
        
        S = self.settings                               #create variable S, which is all the settings
        S.New("flim_binwidth", dtype=int, ro=False, vmin=0, vmax=100e6)
        S.New("flim_n_bins", dtype=int, ro=False, vmin=0, vmax=100e6)
        #S.New("flim_n_pixels", dtype=int, ro=False, vmin=0, vmax=100e14, initial=10000)   #this is just equal to x pixels * y pixels
        S.New('int_time', dtype=int, ro=False, vmin=0, vmax=100e14, initial=1e13)
        S.New('x_pixels', dtype=int, ro=False, unit="um", vmin=1, vmax=50, initial=10)
        S.New('y_pixels', dtype=int, ro=False, unit='um', vmin=1, vmax=50, initial=10)
        
        
        # UI 
        self.ui_filename = sibling_path(__file__,"swabian_cryoFLIM_measure.ui")    #this whole section just loads the ui file
        self.ui = load_qt_ui_file(self.ui_filename)
        self.ui.setWindowTitle(self.name)
        self.ui.setWindowTitle('scan me harder FLIM daddy')

        self.elapsed_time = 0                               #creates a counter and empty data arrays
        #self.xdata = [] #array storing countrate data
        #self.ydata = [] #array storing time points
        
    
    def setup_figure(self):
        S = self.settings                           #creates instance of S within this function?
        #self.tt_hw = self.app.hardware['timetagger'] #creates instance of the timetagger hw in this function?
        
        #self.corrbinwidth = 1000
        
        
        #connect events/settings to ui
        #S.progress.connect_bidir_to_widget(self.ui.progressBar) #no need to connect this since its in daisy rn
        self.ui.start_pushButton.clicked.connect(self.start)
        #self.ui.interrupt_pushButton.clicked.connect(self.interrupt) #no need to connect this

        
        
        
        #self.corrbinwidth.connect_bidir_to_widget(self.ui.picoharp_tacq_doubleSpinBox)
        #self.corrbins.connect_bidir_to_widget(self.ui.picoharp_tacq_doubleSpinBox)
        #self.count_rate0.connect_to_widget(self.ui.ch0_label)
        #self.count_rate1.connect_to_widget(self.ui.ch1_label)
        #self.histbinwidth.connect_bidir_to_widget(self.ui.hist_binwidth_doubleSpinBox)
        #self.histbins.connect_bidir_to_widget(self.ui.hist_numbins_doubleSpinBox)
        
        
        
        '''
        active connections on gui
        '''
        S.flim_binwidth.connect_bidir_to_widget(self.ui.hist_binwidth_doubleSpinBox)
        S.flim_n_bins.connect_bidir_to_widget(self.ui.hist_numbins_doubleSpinBox)        
        S.y_pixels.connect_bidir_to_widget(self.ui.num_ypixels_doubleSpinBox)
        S.x_pixels.connect_bidir_to_widget(self.ui.num_xpixels_doubleSpinBox)
        '''
        
        james come back and connect these later - 20220907
        '''
        self.ui.save_data_pushButton.clicked.connect(self.save_flim_data)
        self.ui.clearplot_pushButton.clicked.connect(self.clear_plot)
        
        
        '''matplotlib figure'''
        
        self.fig = Figure()
        self.flimAxis = self.fig.add_subplot(111)
        
        # self.fig, self.flim = Figure(figsize=(50,50))

        
        self.canvas = FigureCanvasQTAgg(self.fig)

        self.toolbar = NavigationToolbar2QT(self.canvas, parent = None) #self)
        self.ui.plot_groupBox.layout().addWidget(self.toolbar)
        self.ui.plot_groupBox.layout().addWidget(self.canvas)
        
        self.mylabelsize=8
        
        self.flimAxis.set_xlabel('pixels', fontsize=self.mylabelsize)
        self.flimAxis.set_xlim(0,self.settings['x_pixels'])
        self.flimAxis.set_ylabel('pixels', fontsize=self.mylabelsize)
        self.flimAxis.set_ylim(0,self.settings['y_pixels'])
        self.flimAxis.set_title('FLIM', fontsize=self.mylabelsize)
        self.flimAxis.tick_params(axis='both', labelsize=8)
        
        
        
        self.flimarray = np.zeros((self.settings['y_pixels'], self.settings['x_pixels']))
        
        self.flimim = self.flimAxis.imshow(self.flimarray, cmap='gray', vmin=0, vmax=100, origin='lower')
        # self.counterline, = self.counterAxis.plot([],[])
        # self.counterline2, = self.counterAxis.plot([],[])
        
        #self.fig.tight_layout()
        
        '''
        Runs once during App initialization, after setup()
        This is the place to make all graphical interface initializations,
        build plots, etc.
        
        20220906 commented getCounterNormalizationFactor so i can swap the counteraxis to correlation
        
        '''
    def getCounterNormalizationFactor(self):
        bin_index = self.counter.getIndex()
        # normalize 'clicks / bin' to 'kclicks / second'
        return 1e12 / bin_index[1] / 1e3
        
    def run(self):
        '''
        Runs when measurement is started. Runs in a separate thread from GUI.
        It should not update the graphical interface directly, and should only
        focus on data acquisition.
        '''
        self.tt_hw = self.app.hardware['timetagger']                      
        #sw_hw = self.app.hardware['timetagger']
        #sw = self.swabian = sw_hw.tt
        
        #tt_hw = self.app.hardware['timetagger']

        #sleep_time = self.display_update_period
        
        flim_n_pixels = self.settings['x_pixels'] * self.settings['y_pixels']
        
        sleep_time = self.display_update_period
        
        t0 = time.time()
        
        
        integr_time=self.settings['int_time']
        delayed_vch = DelayedChannel(self.tt_hw.tagger, 4, self.settings['int_time'])
        
        PIXEL_END_CH = delayed_vch.getChannel()
        
        gated_vch = GatedChannel(self.tt_hw.tagger, 2, 4, PIXEL_END_CH)
        GATED_SPD_CH = gated_vch.getChannel()
        
        self.flim = Flim(self.tt_hw.tagger, 
                         click_channel=GATED_SPD_CH,
                         start_channel=1,
                         next_channel=4,
                         binwidth=self.settings['flim_binwidth'],
                         n_bins=self.settings['flim_n_bins'],
                         n_histograms=flim_n_pixels
                        )

        while not self.interrupt_measurement_called:
            time.sleep(.01)
        #self.elasped_time = 0
        
        # save_dict = {
        #              'time_histogram': countdata,
        #              'time_array': timedata
        #             }        
        
    def update_display(self):
        '''
        Displays (plots) the data
        This function runs repeatedly and automatically during the measurement run.
        its update frequency is defined by self.display_update_period
        '''
        self.tt_hw = self.app.hardware['timetagger']
        '''
        beginning of cryostat FLIM plotting code
        '''
        
        temp = self.flim.getCurrentFrameIntensity()
        
        #temp.shape = (temp.size//self.settings['x_pixels'], self.settings['x_pixels'])  #if this doesn't work i think ill just kill myself

        b = np.reshape(temp, (-1, self.settings['x_pixels'])) #if the bullshit above doesn't work, we can try this
        
        self.flimim.set_data(b)
        
        self.flimim.set_clim(vmax=np.amax(b))
        
        self.canvas.draw()
        self.canvas.flush_events()  #james, check if this runs in background in scopefoundry as part of a measurement class
        
        
        #print('test1.6')
    
    def save_flim_data(self):
        print('daddy im saving as hard as i can')
        
        temp = self.flim.getCurrentFrame()
        flim_data = temp.np.reshape(self.settings['x_pixels'], self.settings["y_pixels"], temp.shape[0])
        append = '_flim_data.npy' #string to append to sample name

        self.check_filename(append)
        
        np.save(self.app.settings['save_dir']+"/"+ self.app.settings['sample'] + append, flim_data, fmt='%f')

        # np.save(r"C:\Users\GingerCryostat\Desktop\flim.npy", flim_data, fmt='%f') 

        
        print('finished saving daddy')
    
    def clear_plot(self):
        self.flim.clear()
    
    def check_filename(self, append):
        '''
        If no sample name given or duplicate sample name given, fix the problem by appending a unique number.
        append - string to add to sample name (including file extension)
        '''
        samplename = self.app.settings['sample']
        filename = samplename + append
        directory = self.app.settings['save_dir']
        if samplename == "":
            self.app.settings['sample'] = int(time.time())
        if (os.path.exists(directory+"/"+filename)):
            self.app.settings['sample'] = samplename + str(int(time.time()))
