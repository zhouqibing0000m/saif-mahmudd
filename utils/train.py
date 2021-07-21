import os
import sys
import warnings

import tensorflow as tf

from model.har_model import create_model

tf.keras.backend.clear_session()
warnings.filterwarnings("ignore")

sys.path.append("../")


def train_model(dataset: str, model_config, train_x, train_y, val_x, val_y, save_model=True):
    n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]

    model = create_model(n_timesteps, n_features, n_outputs,
                         d_model=model_config[dataset]['d_model'],
                         nh=model_config[dataset]['n_head'],
                         dropout_rate=model_config[dataset]['dropout'])

    model.compile(**model_config['training'])
    model.summary()

    earlyStopping = tf.keras.callbacks.EarlyStopping(**model_config['callbacks']['early_stop'])
    reduce_lr_loss = tf.keras.callbacks.ReduceLROnPlateau(**model_config['callbacks']['lr_reduce'])

    model.fit(train_x, train_y,
              epochs=model_config[dataset]['epochs'],
              batch_size=model_config[dataset]['batch_size'],
              verbose=1,
              validation_data=(val_x, val_y),
              callbacks=[reduce_lr_loss, earlyStopping])

    if save_model:
        model.save(os.path.join(model_config['dirs']['saved_models'], dataset))
