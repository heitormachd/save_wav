import pandas as pd
import json
import os
import numpy as np
 

class AcquisitionParameters:
    def __init__(self):
        # JSON
        self.segment_size = None
        self.fiber_length = None
        self.sampling_rate = None
        self.W = None
        self.rep_rate = None
        self.acq_time = None
        self.n_segment = None

        # CSV
        self.filenames_from_csv = None
        self.samples_arquivo = None

    def read_parameters_json(self, json_file: str):
        with open(json_file, 'r') as file:
            data = json.load(file)

        self.segment_size = np.float32(data.get('segmentSize'))
        self.fiber_length = np.float32(data.get('fiberLength'))
        self.sampling_rate = np.float32(data.get('samplingRate') * 1e6)
        self.W = np.float32(data.get('pulseWidth') * 1e-9)
        self.rep_rate = np.float32(data.get('repRate') * 1e3)
        self.acq_time = np.float32(data.get('acqTime'))
        self.n_segment = np.float32(data.get('nSegment'))

    def read_samples_csv(self, csv_file: str):
        if os.path.exists(csv_file):
            sample_data = pd.read_csv(csv_file)

            self.filenames_from_csv = sample_data['Name'].to_list()
            self.samples_arquivo = cp.asarray(sample_data['Samples'].to_list(), dtype=cp.float32)

            print(f'CSV de samples carregado com sucesso. Número de arquivos listados: {len(self.filenames_from_csv)}')
        else:
            raise Exception(f'Arquivo CSV de samples não encontrado: {csv_file}')
