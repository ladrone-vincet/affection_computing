import numpy as np
import pandas as pd
from scipy.stats import norm
from abc import ABC, abstractmethod
from biosppy.signals import eeg
import pandas as pd

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
                data[label + f'_{i}_{band_order[band_i]}'] = channel
        return features
