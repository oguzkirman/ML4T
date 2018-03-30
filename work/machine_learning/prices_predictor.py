from utils.util import get_data, plot_data
import work.machine_learning.knn as knn
import pandas as pd
import matplotlib.pyplot as plt

def compute_momentum_ratio(prices, window):
    momentum = (prices/prices.shift(periods = -window)) - 1
    return momentum

def compute_sma_ratio(prices, window):
    sma = (prices / prices.rolling(window = window).mean()) - 1
    return sma

def compute_bollinger_bands_ratio(prices, window):
    bb = prices - prices.rolling(window = window).mean()
    bb = bb / (2 * prices.rolling(window = window).std())
    #bb = bb - 1
    return bb

def normalize_ratio(prices):
    return prices - prices.mean()/prices.std()

def evaluate_predictions(learner, input_values, actual_values):
    #TODO: not yet implemented
    predicted_values = learner.query(input_values)
    #predicted_values.shift(periods=5)
    #actual_values.shift(periods=5)
    print(predicted_values)
    print(actual_values)

    rmse = (((actual_values - predicted_values) ** 2).sum() / actual_values.shape) ** 0.5
    #correlation = [actual_values, predicted_values].corr()

    print("RMSE:", rmse)
    #print("Correlation:". correlation)

def main():
    training_start_date = '01/01/2015'
    training_end_date = '31/12/2016'

    testing_start_date = '01/01/2017'
    testing_end_date = '31/12/2017'

    stock = 'IBM'

    training_prices_df = get_data([stock], training_start_date, training_end_date)
    testing_prices_df = get_data([stock], testing_start_date, testing_end_date)

    #learner input, a.k.a. Xs, a.k.a. features
    future_gap = 5 #1 trading week

    #Training Phase
    training_date_range = pd.date_range(training_start_date, training_end_date)
    training_df = pd.DataFrame(index=training_date_range)

    training_df['actual_prices'] = training_prices_df[stock]
    training_df['bolinger_band'] = compute_bollinger_bands_ratio(training_prices_df[stock], future_gap)
    training_df['momentum'] = compute_momentum_ratio(training_prices_df[stock], future_gap)
    training_df['volatility'] = ((training_prices_df[stock]/training_prices_df[stock].shift(periods= -1)) - 1).rolling(window=future_gap).std()
    training_df['y_values'] = training_prices_df[stock].shift(periods = -future_gap)
    training_df = training_df.dropna(subset=['actual_prices'])

    trainX = training_df.iloc[future_gap-1:, :-1]
    trainY = training_df.iloc[future_gap-1:, -1]

    #Testing Phase
    testing_date_range = pd.date_range(testing_start_date, testing_end_date)
    testing_df = pd.DataFrame(index=testing_date_range)

    testing_df['actual_prices'] = testing_prices_df[stock]
    testing_df['bolinger_band'] = compute_bollinger_bands_ratio(testing_prices_df[stock], future_gap)
    testing_df['momentum'] = compute_momentum_ratio(testing_prices_df[stock], future_gap)
    testing_df['volatility'] = ((testing_prices_df[stock]/testing_prices_df[stock].shift(periods= -1)) - 1).rolling(window=future_gap).std()
    testing_df['y_values'] = testing_prices_df[stock].shift(periods = -future_gap)
    testing_df = testing_df.dropna(subset=['actual_prices'])

    testX = testing_df.iloc[:, 0:-1]
    testY = testing_df.iloc[:, -1]

    #kNN Learner
    knn_learner = knn.knn(3)
    knn_learner.train(trainX, trainY)

    #Insample Testing
    evaluate_predictions(knn_learner, trainX, trainY)
    #Outsample Testing
    evaluate_predictions(knn_learner, testX, testY)

if __name__ == "__main__":
    main()