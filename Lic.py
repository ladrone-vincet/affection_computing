#!/usr/bin/env python3.6
# coding: utf-8

import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import pyedflib
import os
import re
import sys
from scipy.stats import norm
from xml2dataframe import XML2DataFrame
import xml.etree.ElementTree as ET
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

def calculateGauss(signal):
    return norm.fit(signal)

ranges = {
        'eeg': {'ch_no': slice(0, 32), 'processor': [GaussProcessor()]},
        'ecg': {'ch_no': slice(33, 36), 'processor': [GaussProcessor()]},
        'gsr': {'ch_no': slice(40, 41), 'processor': [GaussProcessor(), RangeProcessor()]},
        'resp': {'ch_no': slice(44, 45), 'processor': [GaussProcessor(), RangeProcessor()]},
        'temp': {'ch_no': slice(45, 46), 'processor': [GaussProcessor(), RangeProcessor()]},
        'status': {'ch_no': slice(46, 47), 'processor': []}
        }

def read_session(file):
    with open(file, 'r') as file:
        session_data = file.read()
        xml2df = XML2DataFrame(session_data)
        return xml2df.process_data()

def attach_session(session, data):
    for key in session.iloc[:, 7:12]:
        data[key] = session[key][0]

    vlnc = float(data['feltVlnc'])
    arsl = float(data['feltArsl'])
    data['class_1_vlnc'] = '0' if vlnc >= 4.5 else '1'
    data['class_1_arls'] = '0' if arsl >= 4.5 else '1'

    data['class_2_vlnc'] = '2' if vlnc >= 6 else ('1' if vlnc >= 3 else '0')
    data['class_2_arsl'] = '2' if arsl >= 6 else ('1' if arsl >= 3 else '0')
    #TODO: third class

def read_and_cut_signal(signal, margin):
    #TODO: cut margins
    return signal


def isExperimentOne(file):
    root = ET.parse(file).getroot()
    isStim = root.attrib['isStim']
    type = root.attrib['experimentType']
    return isStim == '1' and type == 'emotion elicitation'


def create_data_frame(bdf, margin, session=None):
    data = {}
    signals = {}
    raw_signals = [read_and_cut_signal(bdf.readSignal(signal_nr), margin) for signal_nr in range(bdf.signals_in_file)]

    for dimension in ranges:
        processors = ranges[dimension]['processor']
        related_channels = ranges[dimension]['ch_no']

        signals[dimension] = raw_signals[related_channels]

        for i, signal in enumerate(signals[dimension]):
            for processing in processors:
                processing.process(signal, f'{dimension}_{i}', data)

    if session is not None:
        attach_session(session, data)

    return pd.DataFrame(data)


def write_dataframe_to_file(df, name="df"):
    with open(f'./{name}.csv', 'w+') as file:
        file.write(df.to_csv(index=False))


def iterate_files(limit):
    files_paths = []
    bdf_path = lambda ses_nr, dir: f'../database/Sessions/{ses_nr}/{dir}'
    xml_path = lambda ses_nr: f'../database/Sessions/{ses_nr}/session.xml'
    ses_path = lambda ses_nr: f'../database/Sessions/{ses_nr}'

    sessions_dirs = os.listdir('../database/Sessions/')

    for session_number in sessions_dirs[:limit]:
        for dir_file in os.listdir(ses_path(session_number)):
            if not is_bdf(dir_file):
                continue
            if is_xml(xml_path(session_number)) and isExperimentOne(xml_path(session_number)):
                files_paths.append((
                    bdf_path(session_number, dir_file),
                    xml_path(session_number)))

    return files_paths


def extract_bdf(file, file_no):
    return re.search('../database/Session/' + file_no + '/.bdf' / file)


def is_bdf(file):
    return re.search(r'.bdf\Z', file)

def is_xml(file):
    return True if re.search(r'.xml\Z', file) else False

def create_data_frame_for_files(limit=100):
    dfs = []
    for pair in iterate_files(limit)[:limit]:
        with pyedflib.EdfReader(pair[0]) as bdf:
            frequency = bdf.getSampleFrequency(0)
            n_signals = bdf.signals_in_file
            labels = bdf.getSignalLabels()

            sec_before_and_after = 30
            ticks_b_a_a = sec_before_and_after * frequency

            df = create_data_frame(bdf,
                                   ticks_b_a_a,
                                   read_session(pair[1]))
            dfs.append(df)

    return dfs


print(sys.argv)
limit = 50
if sys.argv[1]:
    limit = int(sys.argv[1])

frames_for_files = create_data_frame_for_files(limit)
concated_frames = pd.concat(frames_for_files)


print(f'Feautres: {concated_frames.shape[1]}')
write_dataframe_to_file(concated_frames)
