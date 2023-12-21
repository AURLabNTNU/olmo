import os
import numpy as np
import pandas as pd
import seawater
import xmltodict
from datetime import date, time

import sensor
import config
import util_db
import util_file

logger = util_file.init_logger(config.main_logfile, name='olmo.ctd')


class CTD(sensor.Sensor):
    def __init__(self, influx_clients=None):
        # Init the Sensor() class: This sets some defaults.
        super(CTD, self).__init__()
        self.influx_clients = influx_clients
##        self.data_dir = f'/home/{config.munkholmen_user}/olmo/munkholmen/DATA'  ## Todo: adopted to NTNU. 
        self.data_dir = f'C:\\Users\\aurlab\\Documents\\InstrRig01_CTD\\'   # todo should end with slash?
        self.data_dir_rsync_source = f'Documents\\InstrRig01_CTD\\'   # same as above but shorter. needed for rsync with windows. For linux the two variables probably will be the same.
        self.data_dir_rsync_back = f'Documents\\InstrRig01_CTD_backup\\' # files moves to this folder before deleting. 
#        self.data_dir_rsync_back = f'Documents\\InstrRig01_CTD_delete\\'
##        self.data_dir = f'C:\\Users\\aurlab\\Documents\\DeleteInstRig\\test' 
##        self.file_search_l0 = r"ready_ctd_(\d{14})\.csv"  # TODO  Merge  Sintef and NTNU
        self.file_search_l0 = r"rig01Trd-NTNU-(\d{8})-(\d{6}).txt"
        self.drop_recent_files_l0 = 1   ## if you write 1, the last file will not be copied and ingested and deleted. See sensor.py
        self.remove_remote_files_l0 = True
        self.max_files_l0 = None

        # Some constants needed for calculations:
        self.munkholmen_LATITUDE = 63.456314   ## todo merge ntnu and sintef
        self.instrumentrigTrd01_LATITUDE = 63.456314 # NTNU.  Correct if necessary
        self.ABSZERO = 273.15
        self.PH_CONSTANT = 1.98416e-4

############## Add instrument rig latitude (and longitude?) (and calibration?)
    def load_calibration(self, path=os.path.join(config.base_dir, 'olmo', 'sensor_calibration', '19-8154.xmlcon')):
        with open(path, 'r') as f:
            calibfile = xmltodict.parse(f.read())
        self.calibration = calibfile['SBE_InstrumentConfiguration']['Instrument']['SensorArray']['Sensor']

    def calcpH(self, temp, pHvout):
        phslope = float(self.calibration[3]['pH_Sensor']['Slope'])
        phoffset = float(self.calibration[3]['pH_Sensor']['Offset'])
        ktemp = self.ABSZERO + temp
        ph = 7 + (pHvout - phoffset) / (phslope * ktemp * self.PH_CONSTANT)
        return ph

    def calcCDOM(self, CDOMvout):
        scalefactor = float(self.calibration[4]['FluoroWetlabCDOM_Sensor']['ScaleFactor'])
        vblank = float(self.calibration[4]['FluoroWetlabCDOM_Sensor']['Vblank'])
        CDOM = scalefactor * (CDOMvout - vblank)
        return CDOM

    def calcPAR(self, PARvout):
        PAR_a0 = float(self.calibration[5]['PARLog_SatlanticSensor']['a0'])
        PAR_a1 = float(self.calibration[5]['PARLog_SatlanticSensor']['a1'])
        Im = float(self.calibration[5]['PARLog_SatlanticSensor']['Im'])
        PAR = Im * 10 ** ((PARvout - PAR_a0) / PAR_a1)
        return PAR

    def calcchl(self, chlvout):
        scalefactor = float(self.calibration[6]['FluoroWetlabECO_AFL_FL_Sensor']['ScaleFactor'])
        vblank = float(self.calibration[6]['FluoroWetlabECO_AFL_FL_Sensor']['Vblank'])
        chl = scalefactor * (chlvout - vblank)
        return chl

    def calcNTU(self, NTUvout):
        scalefactor = float(self.calibration[7]['TurbidityMeter']['ScaleFactor'])
        vblank = float((self.calibration[7]['TurbidityMeter']['DarkVoltage']))
        NTU = scalefactor * (NTUvout - vblank)
        return NTU

    def calcDO_T(self, V):
        TA0 = float(self.calibration[8]['OxygenSensor']['TA0'])
        TA1 = float(self.calibration[8]['OxygenSensor']['TA1'])
        TA2 = float(self.calibration[8]['OxygenSensor']['TA2'])
        TA3 = float(self.calibration[8]['OxygenSensor']['TA3'])

        def calcL(V):
            L = np.log((100000 * V) / (3.3 - V))
            return L

        L = calcL(V)
        T = 1 / (TA0 + (TA1 * L) + (TA2 * L**2) + (TA3 * L**3)) - self.ABSZERO
        return T

    def calcDO(self, DOphase, T, S, P):
        # manual-53_011 p47
        A0 = float(self.calibration[8]['OxygenSensor']['A0'])
        A1 = float(self.calibration[8]['OxygenSensor']['A1'])
        A2 = float(self.calibration[8]['OxygenSensor']['A2'])
        B0 = float(self.calibration[8]['OxygenSensor']['B0'])
        B1 = float(self.calibration[8]['OxygenSensor']['B1'])
        C0 = float(self.calibration[8]['OxygenSensor']['C0'])
        C1 = float(self.calibration[8]['OxygenSensor']['C1'])
        C2 = float(self.calibration[8]['OxygenSensor']['C2'])

        def calcSalcorr(T, S):
            Ts = np.log((298.15 - T) / (self.ABSZERO + T))
            SolB0 = -6.24523e-3
            SolB1 = -7.37614e-3
            SolB2 = -1.03410e-2
            SolB3 = -8.17083e-3
            SolC0 = -4.88682e-7
            Scorr = np.exp(S * (SolB0 + SolB1 * Ts + SolB2 * Ts**2 + SolB3 * Ts**3) + SolC0 * S**2)
            return Scorr

        def calcPcorr(T, P):
            E = 0.011
            K = self.ABSZERO + T
            Pcorr = np.exp(E * P / K)
            return Pcorr

        # Divide the phase delay output (μsec) by 39.457071 to get output in volts, and use the output in volts in the calibration equation.
        V = DOphase / 39.457071

        Pcorr = calcPcorr(T, P)
        Scorr = calcSalcorr(T, S)

        Ksv = (C0 + C1 * T + C2 * T**2)

        DO = (((A0 + A1 * T + A2 * V**2) / (B0 + B1 * V) - 1) / Ksv) * Scorr * Pcorr
        return DO

    def ingest_l0(self, files):

        ## NTNU [MeasurementMetadata] 
        ## Columns=Date,Time,Battery,Cond,ADC,TempCT,ADC,Pressure,ADC,UV,Salinity,Density,CalcSV,Depth   maybe wrong ctd, with turbidity
        ## Units=yyyy-mm-dd,hh:mm:ss.ss,V,mS/cm,none,C,none,dbar,2sComp,Status,PSU,kg/cm3,m/s,m   maybe wrong ctd, with turbidity
        ## 2023-04-23,11:40:33.57,8.87,0.000,561,22.674,388849,0.15,832635,0,-99.989998,-99.989998,-99.989998,0.15  maybe wrong ctd, with turbidity

# CTD without turbidity
# '2023-06-09','13:55:26.62','8.83','35.173','7.850','92.09','0.34','1','33.986626','1026.921021','1482.143921','91.56']]  # 12 elements  (non-turbidity ctd)
# df_all.columns = ['Date','Time','Battery','Cond','TempCT','Pressure','ADC','UV','Salinity','Density','CalcSV','Depth']    # 12 elements  (non-turbidity ctd)

        for f in files:
            df_all = pd.read_csv(f, sep=',')
            print('\n', df_all.head)
            print(len(df_all.columns))
            if len(df_all.columns)==12:
                 # use following line for ctd used on instrument rig 1, summer 2023.
                 df_all.columns = ['Date','Time','Battery','Conductivity','Temperature','Pressure','ADC','UV','Salinity','Density','CalcSV','Depth']    # 12 elements  (non-turbidity ctd) (aml CTD uses capital first letter)
                 # names used by aml: ['Date','Time','Battery','Cond','TempCT','Pressure','ADC','UV','Salinity','Density','CalcSV','Depth'] 
            else: #  if len(df_all.columns)=14:    # if  not right length, pandas create an error messae. and stops.
                 # use this following line for ctd used from dec 2023
                 df_all.columns = ['Date','Time','Battery','Conductivity','ADC_1','Temperature','ADC_2','Pressure','ADC_3','UV','Salinity','Density','CalcSV','Depth']    # 12 elements  (non-turbidity ctd) (aml CTD uses capital first letter)
                 ##Columns=Date,Time,Battery,Cond,ADC,TempCT,ADC,Pressure,ADC,UV,Salinity,Density,CalcSV,Depth    14 columns
                 ##Units=yyyy-mm-dd,hh:mm:ss.ss,V,mS/cm,none,C,none,dbar,2sComp,Status,PSU,kg/cm3,m/s,m    14 columns
                 ##Example: 14,22:52:42.43,8.84,36.240,48763,8.689,194123,92.50,2066358,0,34.306305,1027.045044,1485.696899,91.59
#            df_all.columns = ['Date','Time','Battery','Cond','ADC','TempCT','ADC','Pressure','ADC','UV','Salinity','Density','CalcSV','Depth']  # wrong ctd 
            print('\n', df_all.head)
#            df_all = util_db.force_float_cols(df_all, not_float_cols=[time_col], error_to_nan=True)  # sintef
            df_all['Time'] = pd.to_datetime(df_all['Date'] + ' ' + df_all['Time'])  # ntnu merging date and time and making it a time object
            df_all.rename(columns={"Time": "Timestamp"}, inplace=True)
            df_all = df_all.drop(columns=['Date'])  # ntnu deleting date column
#            df_all['Timestamp'] = df_all['Timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')  # NTNU changing date format to match olmo code. Converts to human readable time.
            time_col = 'Timestamp'   # sintef (and ntnu)
#            df_all[time_col] = pd.to_datetime(df_all[time_col], format='%Y-%m-%d %H:%M:%S') #sintef
#            time_col = 'Timestamp' #sintef
            df_all = df_all.set_index(time_col).tz_localize('CET', ambiguous='infer').tz_convert('UTC')
# delete           df_all.rename(columns={"tempCT": "Temperature"}, inplace=True) # NTNU, for using same names as sintef
# density and depth do not have to be calculated, is already calculated by ctd
#            df_all['density'] = seawater.eos80.dens0(df_all['Salinity'], df_all['Temperature'])
# depth does not have to be calculated
#            df_all['depth'] = seawater.eos80.dpth(df_all['Pressure'], self.munkholmen_LATITUDE)
            print('\n', df_all.head)
##### REMEMBER TO MAKE ALL integers to FLOAT except Timestamp ###########
#            print('after indexing: ', df_all['Timestamp'])  #cant be used, see next line:
            print('after indexing: ', df_all)
# delete            df_all.set_index('Timestamp', inplace=True) # make index before sending to influxdb

# values used by munkholmen ctd and not used by instrument rig
#            tag_values = {'tag_sensor': 'ctd',
#                          'tag_edge_device': 'munkholmen_topside_pi',
#                          'tag_platform': 'munkholmen',
#                          'tag_data_level': 'raw',
#                          'tag_approved': 'no',
#                          'tag_unit': 'none'}

# instrument rig CTD values
            tag_values = {'tag_sensor': 'ctd',
                          'tag_edge_device': 'instrument_rig_01_topside_pc',
                          'tag_platform': 'instrument_rig_01',
                          'tag_data_level': 'raw',
                          'tag_approved': 'no',
                          'tag_unit': 'none'}

            print('01')
            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_temperature_munkholmen'
            measurement_name = 'ctd_temperature_instrument_rig_01'
            field_keys = {"Temperature": 'temperature'}
            tag_values['tag_unit'] = 'degrees_celcius'
            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
            print('02')
            print(df)
#### DOES THE DF NEED ONE COLUMN SELECTED AS INDEX???????
#try
#            util_db.ingest_df(measurement_name, df, )
#            exit()
            util_db.ingest_df(measurement_name, df, self.influx_clients)
            print('03')

# example   df
#temperature tag_sensor  ... tag_approved         tag_unit
#Timestamp                                                 ...                              
#2023-06-05 01:54:24.070000+00:00        7.838        ctd  ...           no  degrees_celcius
#2023-06-05 01:54:24.570000+00:00        7.838        ctd  ...           no  degrees_celcius
#[2 rows x 7 columns]

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_conductivity_munkholmen'
            measurement_name = 'ctd_conductivity_instrument_rig_01'
            field_keys = {"Conductivity": 'conductivity'}
            tag_values['tag_unit'] = 'siemens_per_metre'
            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_pressure_munkholmen'
            measurement_name = 'ctd_pressure_instrument_rig_01'
            field_keys = {"Pressure": 'pressure'}
            tag_values['tag_unit'] = 'none'
            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # -------------drop----------------------------------------------- #
#            measurement_name = 'ctd_sbe63_munkholmen'
#            measurement_name = 'ctd_sbe63_instrument_rig_01'
#            field_keys = {"SBE63": 'sbe63',
#                          "SBE63Temperature": 'sbe63_temperature_voltage'}
#            tag_values['tag_unit'] = 'none'
#            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
#            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_salinity_munkholmen'
            measurement_name = 'ctd_salinity_instrument_rig_01'
            field_keys = {"Salinity": 'salinity'}
            tag_values['tag_unit'] = 'none'
            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_voltages_munkholmen'
#            field_keys = {"Volt0": 'volt0',
#                          "Volt1": 'volt1',
#                          "Volt2": 'volt2',
#                          "Volt4": 'volt4',
#                          "Volt5": 'volt5'}
#            tag_values['tag_unit'] = 'none'
#            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
#            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_voltages_instrument_rig_01'
#            field_keys = {"Volt0": 'volt0',
#                          "Volt1": 'volt1',   we only have battery voltage, remove the rest
#                          "Volt2": 'volt2',
#                          "Volt4": 'volt4',
#                          "Volt5": 'volt5'}
#            tag_values['tag_unit'] = 'none'
#            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
#            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_depth_munkholmen'
            measurement_name = 'ctd_depth_instrument_rig_01'
            field_keys = {"Depth": 'depth'}
            tag_values['tag_unit'] = 'metres'
            tag_values['tag_data_level'] = 'processed'
            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
            util_db.ingest_df(measurement_name, df, self.influx_clients)

            # ------------------------------------------------------------ #
#            measurement_name = 'ctd_density_munkholmen'
            measurement_name = 'ctd_density_instrument_rig_01'
            field_keys = {"Density": 'density'}
            tag_values['tag_unit'] = 'kilograms_per_cubic_metre'
            tag_values['tag_data_level'] = 'processed'
            df = util_db.filter_and_tag_df(df_all, field_keys, tag_values)
            util_db.ingest_df(measurement_name, df, self.influx_clients)

            print('9')
            logger.info(f'File {f} ingested.')

    def rsync_and_ingest(self):

        files = self.rsync()
        logger.info('ctd.rsync() finished.')

        if files['l0'] is not None:
            self.ingest_l0(files['l0'])

        logger.info('ctd.rsync_and_ingest() finished.')
