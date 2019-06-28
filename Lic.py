#!/usr/bin/env python3
# coding: utf-8

# In[1]:


import numpy as np
import pandas as pd
import xml.etree.ElementTree as ET
import pyedflib
import os
import re
import sys
from scipy.stats import norm
from xml2dataframe import XML2DataFrame


# In[2]:
#  bdf = pyedflib.EdfReader(path_to_bdf)


def read_session(file):
   with open(file, 'r') as file:
       session_data = file.read()
       xml2df = XML2DataFrame(session_data)
       return xml2df.process_data()

def calculateGauss(signal):
    return norm.fit(signal)

def create_data_frame(bdf, n_signals, ticks_b_a_a, labels, session=None, include_range=False, include_gauss=False):
   data = {}
   for n in range(n_signals):
       signal = bdf.readSignal(n)[ticks_b_a_a:]
       signal_average = [np.average(signal)]
       data[labels[n]] = signal 
   if include_range:
       new_range  = np.ptp(signal)
       data[labels[n] + "_range"] = new_range
   if include_gauss:
       mi, sigma = calculateGauss(signal)
       data[labels[n] + "_mi"] = mi
       data[labels[n] + "_sigma"] = sigma
   if session is not None:
       for i in session:
           data[i] = session[i][0]
   return pd.DataFrame(data)

def write_dataframe_to_file(df, name="df"):
   with open(f'./{name}.csv', 'w+') as file:
       file.write(df.to_csv(index=False))

def iterate_files(limit):
   files_paths = [] 
   sessions_dirs = os.listdir('../Sessions/')
   for session_number in sessions_dirs[:limit]: 
       for dir_file in os.listdir(f'../Sessions/{session_number}'):
           if is_bdf(dir_file):
              files_paths.append((
                  f'../Sessions/{session_number}/{dir_file}',
                  f'../Sessions/{session_number}/session.xml')) 
   return files_paths

def extract_bdf(file, file_no):
   return re.search('../Session/' + file_no + '/.bdf'/file)

def is_bdf(file):
   return re.search(r'.bdf\Z', file)

def create_data_frame_for_files(limit=100):
   dfs = []
   for pair in iterate_files(limit)[:limit]:
       with pyedflib.EdfReader(pair[0]) as bdf:
           frequency = bdf.getSampleFrequency(0)
           n_signals = bdf.signals_in_file
           labels = bdf.getSignalLabels()

           sec_before_and_after = 30
           ticks_b_a_a = sec_before_and_after * frequency
           ticks_end = len( bdf.readSignal(0) ) - sec_before_and_after * frequency

           df = create_data_frame(bdf, n_signals, ticks_b_a_a, labels, read_session(pair[1]), include_range=True, include_gauss=True)
           dfs.append(df)

   return dfs

print(sys.argv)
limit = 50
if sys.argv[1]:
    limit = int(sys.argv[1])
write_dataframe_to_file(pd.concat(create_data_frame_for_files(limit)))
#  session = read_session()
#  df = create_data_frame()

#  print(read_session())
#  print(str(bdf.getSignalLabels()))
#  print( bdf.readSignal(0) )
#  print(df)
#  write_dataframe_to_file(df)
       




# In[ ]:





# In[ ]:
