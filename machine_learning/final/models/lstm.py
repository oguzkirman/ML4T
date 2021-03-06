from machine_learning.final.utils.dataset import bulid_TIs_dataset
from machine_learning.final.evaluation.metrics import evaluate
import numpy as np
from keras.models import Sequential
from keras.layers.core import Dense, Dropout
from keras.layers.recurrent import LSTM
from keras.optimizers import Adam

def lstm_dataset_reshape(dataset, time_steps, future_gap, split):
    print("Dataset Shape:", dataset.shape)
    X = dataset[:, :-1]
    Y = dataset[:, -1]
    print("X Shape:", X.shape)
    print("Y Shape:", Y.shape)

    X_sampled = []
    for i in range(X.shape[0] - time_steps + 1):
        X_sampled.append(X[i : i+time_steps])
    X_sampled = np.array(X_sampled)
    print("Sampled X Shape:", X_sampled.shape)

    future_gap_index = future_gap - 1
    X_sampled = X_sampled[:-future_gap]
    Y_sampled = Y[time_steps+future_gap_index: ]
    print("Applying Future Gap...")
    print("Sampled X Shape:", X_sampled.shape)
    print("Sampled Y Shape:", Y_sampled.shape)

    if split != None:
        split_index = int(split*X_sampled.shape[0])
        X_train = X_sampled[:split_index]
        X_test = X_sampled[split_index:]
        Y_train = Y_sampled[:split_index]
        Y_test = Y_sampled[split_index:]
        print("(X_train, Y_train, X_test, Y_test) Shapes:")
        print(X_train.shape, Y_train.shape, X_test.shape, Y_test.shape)
        return X_train, Y_train, X_test, Y_test

    return X_sampled, Y_sampled

def build_model(time_steps, features, neurons, drop_out, decay=0.0):
    model = Sequential()
    
    model.add(LSTM(neurons[0], input_shape=(time_steps, features), return_sequences=True))
    model.add(Dropout(drop_out))
        
    model.add(LSTM(neurons[1], input_shape=(time_steps, features), return_sequences=False))
    model.add(Dropout(drop_out))
        
    model.add(Dense(neurons[2], activation='relu'))        
    model.add(Dense(neurons[3], activation='linear'))

    adam = Adam(decay=decay)
    model.compile(loss='mse',optimizer=adam)
    model.summary()
    return model

def model_fit(model, X_train, Y_train, batch_size, epochs, validation_split, verbose, callbacks):

    history = model.fit(
    X_train,
    Y_train,
    batch_size = batch_size,
    epochs = epochs,
    validation_split = validation_split,
    verbose = verbose,
    callbacks = callbacks
    )

    return history

def final_test_lstm(stock_symbol, start_date, end_date, window, future_gap, time_steps,
              neurons, drop_out, batch_size, epochs, validation_split, verbose, callbacks):
    #building the dataset
    print("> building the dataset...")
    df_train, _ = bulid_TIs_dataset(stock_symbol, None, start_date, window)
    df_test, scaler = bulid_TIs_dataset(stock_symbol, start_date, end_date, window)
    #reshaping the dataset for LSTM
    print("\n> reshaping the dataset for LSTM...")
    ds_train = df_train.values
    ds_test = df_test.values
    X_train, Y_train = lstm_dataset_reshape(ds_train, time_steps, future_gap, None)
    X_test, Y_test = lstm_dataset_reshape(ds_test, time_steps, future_gap, None)
    #building the LSTM model
    print("\n> building the LSTM model...")
    features = X_train.shape[2]
    model = build_model(time_steps, features, neurons, drop_out)
    #fitting the training data
    print("\n> fitting the training data...")
    model_fit(model, X_train, Y_train, batch_size, epochs, validation_split, verbose, callbacks)
    #predictions
    print("\n> testing the model for predictions...")
    predictions = model.predict(X_test)
    #inverse-scaling
    print("\n> inverse-scaling the scaled values...")
    predictions = predictions.reshape((predictions.shape[0], 1))
    predictions_inv_scaled = scaler.inverse_transform(predictions)
    Y_test = Y_test.reshape((Y_test.shape[0], 1))
    Y_test_inv_scaled = scaler.inverse_transform(Y_test)
    #evaluation
    normalized_metrics, inv_normalized_metrics = evaluate(Y_test, predictions, 
                                                          Y_test_inv_scaled, predictions_inv_scaled)
    #grouping the actual prices and predictions
    print("\n> grouping the actual prices and predictions...")
    feature_cols = df_test.columns.tolist()
    feature_cols.remove("actual_price")
    df_test.drop(columns=feature_cols, inplace=True)
    df_test.rename(columns={"actual_price" : 'Actual'}, inplace=True)
    df_test = df_test.iloc[time_steps+future_gap-1:]
    df_test['Actual'] = Y_test_inv_scaled
    df_test['Prediction'] = predictions_inv_scaled

    return normalized_metrics, inv_normalized_metrics, df_test