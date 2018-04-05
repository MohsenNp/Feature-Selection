import numpy as np
import pandas as pd
import os, sys

import tensorflow as tf
import matplotlib.pyplot as plt
import keras
from keras.layers import Input, Dense, Dropout, GaussianNoise
from keras.models import Model
from keras.callbacks import ModelCheckpoint, Callback

from sklearn.model_selection import train_test_split

"""
    Created by Mohsen Naghipourfar on 3/26/18.
    Email : mn7697np@gmail.com
    Website: http://ce.sharif.edu/~naghipourfar
"""
# Constants
DAMAVAND_LOCATION_X = "~/f/Behrooz/dataset_local/fpkm_normalized.csv"
DAMAVAND_LOCATION_Y = "~/f/Behrooz/dataset_local/disease.csv"
LOCAL_LOCATION_X = "../Data/fpkm_normalized.csv"
LOCAL_LOCATION_Y = "../Data/disease.csv"

# Hyper-Parameters
LEARNING_RATE = 1e-3
DROP_OUT = 0.5
N_SAMPLES = 10787
N_FEATURES = 19671
N_DISEASES = 34
N_BATCHES = 256
N_EPOCHS = 2500
N_BATCH_LEARN = 10
N_RANDOM_FEATURES = 200
neurons = {
    'in': 200,
    'l1': 1024,
    'l2': 512,
    'l3': 256,
    'l4': 128,
    'out': N_DISEASES
}


def modify_output(target):
    global N_DISEASES
    output_dict = {}
    a = target[0].value_counts()
    # print(a)
    a = pd.DataFrame(a)
    i = 0
    for row in a.itertuples():
        output_dict[row[0]] = i
        i += 1
    N_DISEASES = i
    new_output = [0 for _ in range(N_SAMPLES)]
    for idx, y in target.iterrows():
        new_output[idx] = output_dict[y[0]]
    return new_output


def run(stddev):
    # Train/Test Split
    x_train, x_test, y_train, y_test = train_test_split(x_data, y_data, test_size=0.20)

    # Random Feature Selection
    random_feature_indices = np.random.choice(19671, N_RANDOM_FEATURES, replace=False)
    x_train = x_train[random_feature_indices]
    x_test = x_test[random_feature_indices]

    # Design Model
    input_layer = Input(shape=(neurons['in'],))

    noise_layer = GaussianNoise(stddev)(input_layer)

    l1 = Dense(neurons['l1'], activation='relu')(noise_layer)

    l1_dropout = Dropout(DROP_OUT)(l1)

    l2 = Dense(neurons['l2'], activation='relu')(l1_dropout)

    l2_dropout = Dropout(DROP_OUT)(l2)

    l3 = Dense(neurons['l3'], activation='relu')(l2_dropout)

    l3_dropout = Dropout(DROP_OUT)(l3)

    l4 = Dense(neurons['l4'], activation='relu')(l3_dropout)

    l4_dropout = Dropout(DROP_OUT)(l4)

    output_layer = Dense(neurons['out'], activation='softmax')(l4_dropout)

    # Compile Model
    network = Model(input_layer, output_layer)

    network.compile(optimizer='adam', loss='categorical_crossentropy', metrics=['accuracy'])

    # network.summary()
    if not os._exists('./Results/Keras/{0}_{1}/'.format(os.getpid(), stddev)):
        os.makedirs('./Results/Keras/{0}_{1}/'.format(os.getpid(), stddev))
    save_path = './Results/Keras/{0}_{1}/'.format(os.getpid(), stddev) + 'model.{epoch:02d}-{val_acc:.4f}.hdf5'

    # Create a Callback for Model
    checkpointer = ModelCheckpoint(filepath=save_path,
                                   verbose=0,
                                   monitor='val_acc',
                                   save_best_only=True,
                                   mode='auto',
                                   period=1)

    # Train Model
    network.fit(x=x_train.as_matrix(),
                y=y_train.as_matrix(),
                epochs=N_EPOCHS,
                batch_size=N_BATCHES,
                shuffle=True,
                validation_data=(x_test.as_matrix(), y_test.as_matrix()),
                callbacks=[checkpointer],
                verbose=1)
    # Save Accuracy, Loss
    import csv
    with open('./result_noised_{0}.csv'.format(stddev), 'a') as file:
        writer = csv.writer(file)
        loss, accuracy = network.evaluate(x_test.as_matrix(), y_test.as_matrix(), verbose=0)
        writer.writerow([accuracy, loss])

    # class DummyCheckpoint(Callback):
    #     def on_train_begin(self, logs=None):
    #         self.accuracies = []
    #
    #     def on_epoch_end(self, epoch, logs=None):
    #         if (max(self.accuracies)) < logs.get('acc'):
    #             self.accuracies.append(logs.get('acc'))


if __name__ == '__main__':
    # Load Data
    x_data = pd.read_csv(DAMAVAND_LOCATION_X, header=None)
    y_data = pd.read_csv(DAMAVAND_LOCATION_Y, header=None)
    y_data = pd.DataFrame(modify_output(y_data))
    y_data = pd.DataFrame(keras.utils.to_categorical(y_data, num_classes=N_DISEASES))
    for i in range(1000):
        for stddev in [0.1, 0.05, 0.01]:
            run(stddev)
    print("Finished")
