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
from processors import *

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
    # for key in session.iloc[:, 7:12]:
    #     data[key] = session[key][0]

    vlnc = float(session['feltVlnc'])
    arsl = float(session['feltArsl'])
    emo = float(session['feltEmo'])
    data['class_1_vlnc'] = '0' if vlnc >= 4.5 else '1'
    data['class_1_arls'] = '0' if arsl >= 4.5 else '1'

    data['class_2_vlnc'] = '2' if vlnc >= 6 else ('1' if vlnc >= 3 else '0')
    data['class_2_arsl'] = '2' if arsl >= 6 else ('1' if arsl >= 3 else '0')

    data['class_3_vlnc'] = classifyToClass3(emo, 'vlnc')
    data['class_3_arsl'] = classifyToClass3(emo, 'arsl')

def classifyToClass3(feltEmo, type):
    vlnc = {
        'Clam': [0, 2, 5],
        'Medium': [4, 11],
        'Activated': [1, 3, 6, 12]}
    arsl = {
        'Unpleasent': [1, 2, 3, 5, 12],
        'Neutral': [0, 6],
        'Pleasent': [4, 11]}
    cur = vlnc if type == 'vlnc' else arsl

    for emoClass in cur:
        if feltEmo in cur[emoClass]:
            return emoClass

    return None


def read_and_cut_signal(signal, margin):
    #TODO: cut margins
    sampling = 256
    end = len(signal) // sampling - margin
    cut_signal = signal[margin:end]
    return cut_signal

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

    return pd.DataFrame(data), signals


def write_dataframe_to_file(df, name="df"):
    with open(f'./{name}.csv', 'w+') as file:
        file.write(df.to_csv(index=False))


def iterate_files(db_path, limit):
    files_paths = []
    bdf_path = lambda ses_nr, dir: f'{db_path}/Sessions/{ses_nr}/{dir}'
    xml_path = lambda ses_nr: f'{db_path}/Sessions/{ses_nr}/session.xml'
    ses_path = lambda ses_nr: f'{db_path}/Sessions/{ses_nr}'

    sessions_dirs = os.listdir(f'{db_path}/Sessions')

    for session_number in sessions_dirs[:limit]:
        for dir_file in os.listdir(ses_path(session_number)):
            if not is_bdf(dir_file):
                continue
            if is_xml(xml_path(session_number)) and isExperimentOne(xml_path(session_number)):
                files_paths.append((
                    bdf_path(session_number, dir_file),
                    xml_path(session_number)))

    return files_paths

def is_bdf(file):
    return re.search(r'.bdf\Z', file)

def is_xml(file):
    return True if re.search(r'.xml\Z', file) else False

def create_data_frame_for_files(db_path='../database', limit=100):
    dfs = []
    for pair in iterate_files(db_path, limit)[:limit]:
        with pyedflib.EdfReader(pair[0]) as bdf:
            frequency = bdf.getSampleFrequency(0)
            n_signals = bdf.signals_in_file
            labels = bdf.getSignalLabels()

            sec_before_and_after = 30

            df, signals = create_data_frame(bdf,
                                            sec_before_and_after,
                                            read_session(pair[1]))
            dfs.append(df)

    return dfs, signals

if __name__ == "__main__":
    print(sys.argv)
    limit = 50
    if sys.argv[1]:
        limit = int(sys.argv[1])

    frames_for_files, signals = create_data_frame_for_files(limit=limit)
    concated_frames = pd.concat(frames_for_files)


    print(f'Feautres: {concated_frames.shape[1]}')
    write_dataframe_to_file(concated_frames)
