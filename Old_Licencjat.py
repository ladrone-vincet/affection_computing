#!/usr/bin/env python
# coding: utf-8
import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import pyedflib as bd 
import os
from xml2dataframe import XML2DataFrame

def read_session():
    with open('../Sessions/2/session.xml', 'r') as file:
        session_data = file.read()
        xml2df = XML2DataFrame(session_data)
        return xml2df.process_data()
print(read_session())
path_to_bdf = './Sessions/2/Part_1_S_Trial1_emotions.bdf'

bdf = bd.EdfReader(path_to_bdf)
print(str(bdf.getSignalLabels()))
print( bdf.readSignal(0) )
