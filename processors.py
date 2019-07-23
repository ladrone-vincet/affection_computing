import numpy as np
import pandas as pd
from scipy.stats import norm
from abc import ABC, abstractmethod

class SignalProcessor(ABC):
    @abstractmethod
    def process(self, signal, label, data):
        pass

class GaussProcessor(SignalProcessor):
    def process(self, signal, label, data):
        mi, sigma = norm.fit(signal)
        data[label + '_mi'] = [mi]
        data[label + '_sigma'] = [sigma]

class RangeProcessor(SignalProcessor):
    def process(self, signal, label, data):
        new_range = np.ptp(signal)
        data[label + "_range"] = new_range
