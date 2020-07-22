import os
import pickle
import pandas as pd
import numpy as np


class CompiledNormalizedData:

    def __init__(self, basename):
        matrix_value_filename = basename + '.npy'
        matrix_conf = basename + '.pck'

        with open(matrix_conf, 'rb') as fi:
            df_shape = pickle.load(fi)

        matrix_values = np.memmap(matrix_value_filename, dtype='float32', mode='r', shape=(len(df_shape['index']), len(df_shape['columns'])))

        self.df = pd.DataFrame(matrix_values, index=df_shape['index'], columns=df_shape['columns'])