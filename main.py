import argparse
import os
import warnings

import tensorflow as tf
import yaml

from model.har_model import create_model
from preprocess.opp.data_loader import get_opp_data
from preprocess.pamap2.data_loader import get_pamap2_data
from preprocess.skoda.data_loader import get_skoda_data
from preprocess.uschad.data_loader import get_uschad_data
from utils.result import generate_result

tf.keras.backend.clear_session()
warnings.filterwarnings("ignore")


def get_data(dataset: str):
    if dataset == 'pamap2':
        (train_x, train_y), (val_x, val_y), (test_x, test_y), y_test = get_pamap2_data()

        return train_x, train_y, val_x, val_y, test_x, test_y

    elif dataset == 'skoda':
        (train_x, train_y), (val_x, val_y), (test_x, test_y) = get_skoda_data()
        return train_x, train_y, val_x, val_y, test_x, test_y

    elif dataset == 'opp':
        (train_x, train_y), (val_x, val_y), (test_x, test_y) = get_opp_data()
        return train_x, train_y, val_x, val_y, test_x, test_y

    elif dataset == 'uschad':
        return get_uschad_data()


def train_model(dataset: str, model_config, train_x, train_y, val_x, val_y, save_model=False):
    n_timesteps, n_features, n_outputs = train_x.shape[1], train_x.shape[2], train_y.shape[1]

    model = create_model(n_timesteps, n_features, n_outputs, d_model=model_config[dataset]['d_model'])

    model.compile(**model_config['training'])
    model.summary()

    earlyStopping = tf.keras.callbacks.EarlyStopping(monitor='val_accuracy', patience=5, verbose=1, mode='max')
    reduce_lr_loss = tf.keras.callbacks.ReduceLROnPlateau(monitor='val_loss',
                                                          factor=0.1,
                                                          patience=4,
                                                          verbose=1,
                                                          min_delta=1e-4,
                                                          mode='min')

    model.fit(train_x, train_y,
              epochs=model_config[dataset]['epochs'],
              batch_size=model_config[dataset]['batch_size'],
              verbose=1,
              validation_data=(val_x, val_y),
              callbacks=[reduce_lr_loss, earlyStopping])

    if save_model:
        model.save(os.path.join(model_config['dirs']['saved_models'], dataset))


def test_model(dataset: str, model_config, test_x):
    if os.path.exists(os.path.join(model_config['dirs']['saved_models'], dataset)):
        model = tf.keras.models.load_model(os.path.join(model_config['dirs']['saved_models'], dataset))
    else:
        print('PLEASE, TRAIN THE MODEL FIRST OR PUT PRETRAINED MODEL IN "saved_model" DIRECTORY')
        return

    pred = model.predict(test_x, batch_size=model_config[dataset]['batch_size'], verbose=1)

    return pred


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Self Attention Based HAR Model Training')

    parser.add_argument('--train', action='store_true', default=False, help='Training Mode')
    parser.add_argument('--test', action='store_true', default=False, help='Testing Mode')
    parser.add_argument('--save_model', action='store_true', default=False, help='Save Trained Model')
    parser.add_argument('--dataset', default='pamap2', type=str, help='Name of Dataset for Model Training')

    args = parser.parse_args()

    model_config_file = open('configs/model.yaml', mode='r')
    model_cfg = yaml.load(model_config_file, Loader=yaml.FullLoader)

    train_x, train_y, val_x, val_y, test_x, test_y = get_data(dataset=args.dataset)

    if args.train:
        train_model(dataset=args.dataset,
                    model_config=model_cfg,
                    train_x=train_x, train_y=train_y,
                    val_x=val_x, val_y=val_y,
                    save_model=args.save_model)

    if args.test:
        pred = test_model(dataset=args.dataset, model_config=model_cfg, test_x=test_x)
        generate_result(dataset=args.dataset, ground_truth=test_y, prediction=pred)
