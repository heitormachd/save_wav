import numpy as np
from scipy.signal import butter, filtfilt
from scipy.io.wavfile import write
import json
from pathlib import Path
from datetime import datetime, timedelta
from acquisition_parameters import AcquisitionParameters

parameters_filename = 'wav_parameters.json'

with open(parameters_filename, 'r') as file:
        data = json.load(file)

spatial_start = data.get('spatial_start')
spatial_end = data.get('spatial_end')
start_time = data.get('start_time')
end_time = data.get('end_time')
spatial_downsampling_factor = data.get('spatial_downsampling_factor') 

hd_id = data.get('hd_id')
json_filename = data.get('json_filename')
input_foldername = data.get('input_foldername')
output_foldername = data.get('output_foldername')

spec_position = data.get('spec_position')

low_cutoff = data.get('f_min')
high_cutoff = data.get('f_max')
audio_speed = data.get('audio_speed')

filter = data.get('filter')

spatial_downsampling_factor = 10

spatial_length_list = ["null", 40, 40, 50, 50]

spatial_length = spatial_length_list[hd_id]

def butter_bandpass(data, fmin, fmax, fs, order=4, axis=1):

    nyquist = 0.5 * fs
    low = fmin / nyquist
    high = fmax / nyquist
    b, a = butter(order, [low, high], btype='band')
    
    return filtfilt(b, a, data, axis).astype(np.float32)

def generate_acquisition_indices(start_time_str, end_time_str, hd_id):

    acquisition_start_str = [0, "21/10/2024 19:14:01", "22/10/2024 16:01:01", "23/10/2024 15:41:41", "24/10/2024 12:04:01"]
    acquisition_start = datetime.strptime(acquisition_start_str[hd_id], '%d/%m/%Y %H:%M:%S')
    start_time = datetime.strptime(start_time_str, '%d/%m/%Y %H:%M:%S')
    end_time = datetime.strptime(end_time_str, '%d/%m/%Y %H:%M:%S')
    file_duration = 100
    start_offset_seconds = int((start_time - acquisition_start).total_seconds())
    end_offset_seconds = int((end_time - acquisition_start).total_seconds())
    start_index = start_offset_seconds // file_duration
    end_index = end_offset_seconds // file_duration
    acquisition_indices = [
        [i * file_duration, (i + 1) * file_duration - 1]
        for i in range(start_index, end_index + 1)
    ]
    return acquisition_indices

indices = generate_acquisition_indices(start_time, end_time, hd_id)

for i in range(len(indices)):
    
    time_start = indices[i][0]
    time_end = indices[i][1]
   
    data = np.load(f'{input_foldername}/HD{hd_id}_ds{spatial_downsampling_factor}_{spatial_length}km_100s_{time_start}_{time_end}.npy')
    data = data.T

    ### AQUISITION PARAMETERS ###
    acquisition_parameters = AcquisitionParameters()
    acquisition_parameters.read_parameters_json(json_file=json_filename)

    fs = acquisition_parameters.rep_rate
    time_step = 1. / fs
    acquisition_step = 1. / acquisition_parameters.sampling_rate
    nu = np.float32(3e8 / 1.4682)
    gauge_length = np.round(1.5 * acquisition_parameters.W / acquisition_step)

    time_arr = np.arange(0, data.shape[1] * spatial_downsampling_factor, dtype=np.float32) * time_step + time_start
    acquisition_time_arr = np.arange(0, data.shape[0] * spatial_downsampling_factor, dtype=np.float32) * acquisition_step
    distance_arr = acquisition_time_arr * nu / 2. + spatial_start
    distance_phase = distance_arr[int(gauge_length):]
    dx = (distance_phase[1] - distance_phase[0]) * spatial_downsampling_factor
    
    if filter == "True":
        data = butter_bandpass(data, low_cutoff, high_cutoff, fs)  
    
    if spec_position[0] == "local":
        spec_position_min_px = int((spec_position[1][0] - distance_phase.min()) / dx)
        signal = data[spec_position_min_px, :]

    if spec_position[0] == "interval":
        spec_position_min_px = int((spec_position[1][0] - distance_phase.min()) / dx)
        spec_position_max_px = int((spec_position[1][1] - distance_phase.min()) / dx)
        signal = np.mean(data[spec_position_min_px:spec_position_max_px, :], axis=0)
    
    signal = np.int16(signal * 32767)
    audio_freq = int(fs * audio_speed)

    if spec_position[0] == "local":
        write(f'{output_foldername}/HD{hd_id}_position{spec_position[1][0]}m_time{time_start}--{time_end}s_speed{audio_speed}x.wav', audio_freq, signal)

    if spec_position[0] == "interval":
        write(f'{output_foldername}/HD{hd_id}_position{spec_position[1][0]}--{spec_position[1][1]}m_time{time_start}--{time_end}s_speed{audio_speed}x.wav', audio_freq, signal)
