#from HW_PI_PiezoStage.PiezoStage_Scan import PiezoStage_Scan
from HW_Attocube_ASC500.ASC500_Scan import ASC500_Scan
from ScopeFoundry import Measurement
from ScopeFoundry.helper_funcs import sibling_path, load_qt_ui_file
import pyqtgraph as pg
import numpy as np
import time
import pickle
import os.path
from pyqtgraph.Qt import QtGui, QtCore, QtWidgets
from pyqtgraph.Point import Point
#import customplotting.mscope as cpm
from TimeTagger import Coincidences, Counter, Correlation, createTimeTagger, freeTimeTagger, Histogram, Flim


class Swabian_Scan(ASC500_Scan):

    name = "Swabian_Scan"

    def setup(self):
        ASC500_Scan.setup(self)

        self.tt_hw = self.app.hardware['timetagger']   #this is done so we can call functions and variables from these .py files
        self.asc500_hw = self.app.hardware['ASC500']
        #self.asc500_scan = self.app.measurement['ASC500_Scan']
        
        self.settings.New("flim_binwidth", dtype=int, ro=False, vmin=0, vmax=100e6)
        self.settings.New("flim_n_bins", dtype=int, ro=False, vmin=0, vmax=100e6)
        #S.New("flim_n_pixels", dtype=int, ro=False, vmin=0, vmax=100e14, initial=10000)   #this is just equal to x pixels * y pixels
        self.settings.New('int_time', dtype=int, ro=False, vmin=0, vmax=100e14, initial=1e13)
        # self.settings.New('x_pixels', dtype=int, ro=False, unit="um", vmin=1, vmax=50, initial=10)
        # self.settings.New('y_pixels', dtype=int, ro=False, unit='um', vmin=1, vmax=50, initial=10)

        self.settings.New("IntTime", unit="s", si=True, dtype=float, vmin=1e-3, vmax=100*60*60, initial=1)
        self.settings.New("histogram_n_values", dtype=int, ro=False, vmin=0, vmax=100e6, initial=1000)
        self.settings.New("histogram_bin_width", dtype=int, ro=False, vmin=0, vmax=100e6, initial=1000)#removed si=True to keep units from auto-changing
#        self.settings.New("Tacq", unit="s", dtype=float, vmin=1e-3, vmax=100*60*60, initial=1) #removed si=True to keep units from auto-changing
        self.settings.New('APDChannel', dtype=int, choices=[1, 2, 3, 4], initial=2)
        self.settings.New('laserchannel', dtype=int, choices=[1, 2, 3, 4], initial=1)
        self.settings.New('ASC500Channel', dtype=int, choices=[1, 2, 3, 4], initial=4)
    def setup_figure(self):
        ASC500_Scan.setup_figure(self)

        #setup ui for picoharp specific settings
        # #details_groupBox = self.set_details_widget(widget = self.settings.New_UI(include=["Tacq", "Resolution", "count_rate0", "count_rate1"]))
        # details_groupBox = self.set_details_widget(widget = self.settings.New_UI(include=["IntTime"]))
        # widgets = details_groupBox.findChildren(QtGui.QWidget)
        # tacq_spinBox = widgets[1]
        # #resolution_comboBox = widgets[4]
        # #count_rate0_spinBox = widgets[6]
        # #count_rate1_spinBox = widgets[9]
        # #connect settings to ui
        
        # print(self.settings.mychannel)
        # temp = self.settings.mychannel.value
        # print(temp)
        # self.settings.IntTime.connect_to_widget(tacq_spinBox)
        self.settings.APDChannel.connect_to_widget(self.ui.APD_comboBox)    #theoretically all that needs to happen now is that these variables get put in the measurement routine
        self.settings.laserchannel.connect_to_widget(self.ui.Laser_comboBox)
        self.settings.ASC500Channel.connect_to_widget(self.ui.ASC500_comboBox)
        self.settings.flim_binwidth.connect_bidir_to_widget(self.ui.hist_binwidth_doubleSpinBox)
        self.settings.flim_n_bins.connect_bidir_to_widget(self.ui.hist_numbins_doubleSpinBox)
        # #self.picoharp_hw.settings.Resolution.connect_to_widget(resolution_comboBox)
        # #self.picoharp_hw.settings.count_rate0.connect_to_widget(count_rate0_spinBox)
        # #self.picoharp_hw.settings.count_rate1.connect_to_widget(count_rate1_spinBox)

        # tacq_spinBox.valueChanged.connect(self.update_estimated_scan_time)
        # self.update_estimated_scan_time()

        #save data buttons
        self.ui.save_image_pushButton.clicked.connect(self.save_intensities_image)
        self.ui.save_array_pushButton.clicked.connect(self.save_intensities_data)
        self.ui.save_histo_pushButton.clicked.connect(self.save_histogram_arrays)
    
        #setup imageview
        # self.imv = pg.ImageView()
        # self.imv.getView().setAspectLocked(lock=False, ratio=1)
        # self.imv.getView().setMouseEnabled(x=True, y=True)
        # self.imv.getView().invertY(False)
        # roi_plot = self.imv.getRoiPlot().getPlotItem()
        # roi_plot.getAxis("bottom").setLabel(text="Time (ns)"))


    def update_estimated_scan_time(self):
        try:
            scan_time = self.asc500_hw.settings.Columns * self.asc500_hw.settings.Lines * self.asc500_hw.settings.sampTime #determined by running scans and timing
            self.ui.estimated_scan_time_label.setText("Estimated scan time: " + "%.2f" % scan_time + "s")
        except:
            pass
            
    def update_display(self):
        ASC500_Scan.update_display(self)
        # if hasattr(self, 'sum_intensities_image_map'):
        #     #self.picoharp_hw.read_from_hardware() #will need to figure out what this does and replace it
        #     if not self.interrupt_measurement_called:
        #         seconds_left = ((self.x_range * self.y_range) - self.pixels_scanned) * self.settings["IntTime"] + self.overhead
        #         self.ui.estimated_time_label.setText("Estimated time remaining: " + "%.2f" % seconds_left + "s")
        #     self.img_item.setImage(self.sum_intensities_image_map) #update stage image

        #     #update imageview
        #     self.times = self.time_data[:, 0, 0]*1e-3
        #     self.imv.setImage(img=self.hist_data, autoRange=False, autoLevels=True, xvals=self.times)
        #     self.imv.show()
        #     self.imv.window().setWindowFlag(QtCore.Qt.WindowCloseButtonHint, False) #disable closing image view window

        #     #update progress bar
        #     progress = 100 * ((self.pixels_scanned+1)/np.abs(self.x_range*self.y_range))
        #     self.ui.progressBar.setValue(progress)
        #     self.set_progress(progress)
        #     pg.QtGui.QApplication.processEvents()

    def pre_run(self):
        try:
            ASC500_Scan.pre_run(self) #setup scan parameters
            #self.picoharp = self.picoharp_hw.picoharp
            self.check_filename("_raw_PL_hist_data.pkl")
    
            dirname = self.app.settings['save_dir']        
            self.check_filename('_histdata.dat')
            sample_filename = self.app.settings['sample']
            self.hist_filename = os.path.join(dirname, sample_filename + '_histdata.dat')
            self.check_filename('_timedata.dat')
            self.time_filename = os.path.join(dirname,  sample_filename + '_timedata.dat')
            
            #hist_len = self.num_hist_chans
            hist_len=self.settings['histogram_n_values'] #does this need to be equal to number of bins??? james...test this out.
            #hist_len=1000
            #Use memmaps to use less memory and store data into disk
            self.hist_data= np.memmap(self.hist_filename,dtype='float32',mode='w+',shape=(hist_len, self.x_range, self.y_range))
            self.time_data= np.memmap(self.time_filename,dtype='float32',mode='w+',shape=(hist_len, self.x_range, self.y_range))
    
            #Store histogram sums for each pixel
            # self.sum_intensities_image_map = np.zeros((self.x_range, self.y_range), dtype=float)
    
            scan_time = self.x_range * self.y_range * self.settings["IntTime"] #* 1e-3 #s
            self.ui.estimated_scan_time_label.setText("Estimated scan time: " + "%.2f" % scan_time + "s")
            
            if self.asc500_scan.settings['fix_xy'] == True:
                self.asc500.scanner.setXEqualY(1)
            elif self.asc500_scan.settings['fix_xy'] == False:
                self.asc500.scanner.setXEqualY(0)
                
        except:
            pass

    # def scan_measure(self):
    #     """
    #     Data collection for each pixel.
    #     """
    #     print("before scan")

        
    #     flim_n_pixels = self.settings['x_pixels'] * self.settings['y_pixels']
        
    #     sleep_time = self.display_update_period
        
    #     t0 = time.time()
        
        
    #     integr_time=self.settings['int_time']
    #     delayed_vch = DelayedChannel(self.tt_hw.tagger, 4, self.settings['int_time'])
        
    #     PIXEL_END_CH = delayed_vch.getChannel()
        
    #     gated_vch = GatedChannel(self.tt_hw.tagger, 2, 4, PIXEL_END_CH)
    #     GATED_SPD_CH = gated_vch.getChannel()
        
    #     self.flim = Flim(self.tt_hw.tagger, 
    #                       click_channel=GATED_SPD_CH,
    #                       start_channel=1,
    #                       next_channel=4,
    #                       binwidth=self.settings['flim_binwidth'],
    #                       n_bins=self.settings['flim_n_bins'],
    #                       n_histograms=flim_n_pixels
    #                     )

    #     while not self.interrupt_measurement_called:
    #         time.sleep(.01)
        
    #     self.asc500.scanner.setScanOnce(1)

        
    #     print("after scan")

    def post_run(self):
        """
        Export data.
        """
        ASC500_Scan.post_run(self)
        # save_dict = {"Histogram data": self.hist_data, "Time data": self.time_data,
        #          "Scan Parameters":{"X scan start (um)": self.x_start, "Y scan start (um)": self.y_start,
        #                             "X scan size (um)": self.x_scan_size, "Y scan size (um)": self.y_scan_size,
        #                             "X step size (um)": self.x_step, "Y step size (um)": self.y_step},
        #                             "PicoHarp Parameters":{"Acquisition Time (s)": self.settings['IntTime']}}#,
                                                              #"Resolution (ps)": self.settings['Resolution']} }
        # print('about to save daddy')
        # pickle.dump(save_dict, open(self.app.settings['save_dir']+"/"+self.app.settings['sample']+"_raw_PL_hist_data.pkl", "wb"))
        # print('just saved daddy')

    def save_intensities_data(self):
 
        ASC500_Scan.save_intensities_data(self, self.flim.getSummedFramesIntensity(), 'swabian')

    def save_intensities_image(self):
        # intensity_data = self.flim.getSummedFramesIntensity()
        ASC500_Scan.save_intensities_image(self, self.flim.getSummedFramesIntensity(), 'swabian')
        
    def save_histogram_arrays(self):
        print('daddy im saving as hard as i can')
        
        temp = self.flim.getCurrentFrame()
        flim_data = temp.np.reshape(self.settings['x_pixels'], self.settings["y_pixels"], temp.shape[0])
        index_bins = self.flim.getIndex()
        ASC500_Scan.save_histogram_arrays(self, flim_data, index_bins, 'swabian')
