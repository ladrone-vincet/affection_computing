import numpy as np
import pandas as pd
from scipy.stats import norm
from abc import ABC, abstractmethod
from biosppy.signals import eeg
import pandas as pd
import neurokit as nk
from sklearn import externals
from sklearn.externals import joblib

class SignalProcessor(ABC):
    @abstractmethod
    def process(self, signal, label, data):
        pass

class GaussProcessor(SignalProcessor):
    def process(self, signal, label, data):
        for i, channel in enumerate(signal):
            #  print(channel, i, signal)
            mi, sigma = norm.fit(channel)
            data[label + f'_{i}_mi'] = [mi]
            data[label + f'_{i}_sigma'] = [sigma]

class RangeProcessor(SignalProcessor):
    def process(self, signal, label, data):
        for i, channel in enumerate(signal):
            new_range = np.ptp(channel)
            data[label + f"_{i}_range"] = new_range


class EEGPowerProcessor(SignalProcessor):
    def process(self, signal, label, data, sampling=256):
        prepared_signal = pd.DataFrame(signal).transpose()
        features = eeg.get_power_features(prepared_signal, sampling)
        band_order = ['theta', 'alpha_low', 'alpha_high', 'beta', 'gamma', 'rest']
        for band_i, band in enumerate(features[1:]):
            for i, channel in enumerate(band.transpose()):
                #it returns ~470 values (s?) and row has only 1
                data[label + f'_{i}_{band_order[band_i]}'] = channel[:]
        return features

class ECGNeuroKitProcessor(SignalProcessor):
    def process(self, signal, label, data, sampling=256):

        # TODO: Process 3 ecg channels to create one clear 
        for i, channel in enumerate(signal):
            c = pd.DataFrame(channel)[0]
            features = nk.ecg_process(ecg=c, sampling_rate=256)
            del features['ECG']['HRV']['RR_Intervals'] #exlude because it is seriesd
            f = self.attach_non_zero_values(features['ECG']['HRV'], label + str(i), data)

    def attach_non_zero_values(self, dict, label, data):
        for key in dict.keys():
            if dict[key] != 0:
                data[f'[{label}_{key}]'] = dict[key]

