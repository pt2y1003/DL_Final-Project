# -*- coding: utf-8 -*-
"""base.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1I6b-HHPQK4Znx7yNCabSgzR13hdHwHWk
"""

!nvidia-smi

import pandas as pd

# There are 2 tables on the Wikipedia page
# we want the first table

payload = pd.read_html('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
first_table = payload[0]
second_table = payload[1]
symbols = first_table.Symbol
first_table.head()

!pip install yfinance
!pip install talib-binary

import numpy as np
import matplotlib.pyplot as plt
import yfinance as yf
import talib as ta
import time

start = time.time()
period_y = '11y'

df_X = yf.Ticker(symbols[0]).history(period=period_y).ffill()
df_X["Close_mom_sht"] = ta.MOM(df_X["Close"], timeperiod = 5)
df_X["Close_mom_mid"] = ta.MOM(df_X["Close"], timeperiod = 25)
df_X["Close_mom_lng"] = ta.MOM(df_X["Close"], timeperiod = 75)
df_X["Close_rsi"] = ta.RSI(df_X["Close"])
df_X["Close_Price_NATR"] = ta.NATR(df_X["High"], df_X["Low"], df_X["Close"])
df_X["Close"] = ta.ROCP(df_X["Close"], timeperiod = 1)
df_X = df_X.filter(regex='Close', axis = 1)
df_X.columns = ["MMM_" + c for c in df_X.columns]

for smb in symbols[1:]:
    new_df_X = yf.Ticker(smb).history(period=period_y).ffill()
    if len(new_df_X) == 0:
        continue
    if (new_df_X.index[0] != df_X.index[0]):
        continue
    new_df_X["Close_mom_sht"] = ta.MOM(new_df_X["Close"], timeperiod = 5)
    new_df_X["Close_mom_mid"] = ta.MOM(new_df_X["Close"], timeperiod = 25)
    new_df_X["Close_mom_lng"] = ta.MOM(new_df_X["Close"], timeperiod = 75)
    new_df_X["Close_rsi"] = ta.RSI(new_df_X["Close"])
    new_df_X["Close_Price_NATR"] = ta.NATR(new_df_X["High"], new_df_X["Low"], new_df_X["Close"])
    new_df_X["Close"] = ta.ROCP(new_df_X["Close"], timeperiod = 1)
    new_df_X = new_df_X.filter(regex='Close', axis = 1)
    new_df_X.columns = [smb + "_" + c for c in new_df_X.columns]
    df_X = df_X.join(new_df_X, how = "outer")
print(f"{(time.time() - start) / 60: 0.2f} min.")

start = time.time()

df_X_low_cor = df_X.copy()
print(df_X_low_cor.shape)
cor = df_X_low_cor.filter(regex='Close$', axis = 1).corr()
cor_n_diag = cor - np.diag(np.ones(cor.shape[0]))
print(((cor_n_diag > 0.8).sum() > 0).sum())
print(((cor_n_diag > 0.7).sum() > 0).sum())

while (cor_n_diag > 0.7).sum().sum() > 0:
    candidates = cor_n_diag[np.any(cor_n_diag == cor_n_diag.max().max(), axis = 1)].mean(axis = 1)
    col_del_names = candidates[candidates == candidates.max()]
    col_del_names = df_X_low_cor.filter(regex = col_del_names.index.values[0], axis = 1).columns.values

    df_X_low_cor = df_X_low_cor.loc[:, [not cl in col_del_names for cl in df_X_low_cor.columns.values]]
    cor = df_X_low_cor.filter(regex='Close$', axis = 1).corr()
    cor_n_diag = cor - np.diag(np.ones(cor.shape[0]))

print(f"{(time.time() - start) / 60: 0.2f} min.")
print(df_X_low_cor.shape)
print(((cor_n_diag > 0.7).sum() > 0).sum())

df_X = df_X_low_cor
print(df_X.isna().sum().sum())
df_X = df_X.ffill()
print(df_X.head(6))

df_X = df_X.dropna()
print(df_X.shape)
print(df_X.head(6))

import pandas_datareader.data as web
import datetime

SP500 = web.DataReader(['sp500'], 'fred', df_X.index[0], datetime.datetime(2022, 5, 2))
print(SP500.isna().sum())
SP500 = SP500.dropna()
print(SP500)

SP500['sp500'] = ta.ROCP(SP500['sp500'], timeperiod = 1)
y_ind = SP500.index[1:-2]
SP500_t2 = SP500.iloc[3:, :].rename(columns = {"sp500": "sp500_t2"})
SP500_t2.index = y_ind
df = SP500_t2.join(SP500).join(df_X)
print(df.isna().sum().sum())
print(df)

df.shape

n_t = 3
df_org = df.copy()

df_ind = df_org.index[:-1]
df_t_1 = df_org.iloc[1:, 1:]
df_t_1.index = df_ind
df_t_1.columns = [c + "_t_1" for c in df_org.columns[1:]]
df = df.join(df_t_1, how = "inner")

for i in range(2, (n_t + 1)):
    df_ind = df_t_1.index[:-1]
    df_t_1 = df_t_1.iloc[1:, :]
    df_t_1.index = df_ind
    df_t_1.columns = [c + "_t_" + str(i) for c in df_org.columns[1:]]
    df = df.join(df_t_1, how = "inner")

print(df)

print(df.columns[:1430])

import random
import os
import tensorflow as tf
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, LeakyReLU, Dropout, BatchNormalization, LSTM

def seed_everything(seed):
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    np.random.seed(seed)
    tf.random.set_seed(seed)
    tf.compat.v1.set_random_seed(seed)
    session_conf = tf.compat.v1.ConfigProto(
        intra_op_parallelism_threads=1,
        inter_op_parallelism_threads=1
    )
    sess = tf.compat.v1.Session(graph=tf.compat.v1.get_default_graph(), config=session_conf)
    tf.compat.v1.keras.backend.set_session(sess)

n_train = int(np.round(df.shape[0] * 0.8))

df_train = df.iloc[:n_train, :]
df_test = df.iloc[n_train:, :]

sc = StandardScaler()
df_train_tf = sc.fit_transform(df_train.values)
df_test_tf = sc.transform(df_test.values)

def data_generator_lstm(df, window, batchsize):
  feature = np.empty((batchsize, 1429, window))
  target = np.empty((batchsize, 1))

  ite = 0
  while True:
    i = random.randint(window, len(df)-1)
    # for i in range(window, len(df)):
    onefeature = df[(i-window):i,1:1430]
    feature[ite] = onefeature.T

    target[ite] = df[i,0]

    ite += 1

    if ite == batchsize-1:
      yield feature, target
      ite = 0

dropout_p = 0.1
lr_alpha = 0.05
window = 10

model = Sequential()
model.add(Dropout(dropout_p, input_shape = [1429, window]))

model.add(LSTM(256, return_sequences=True))
model.add(LeakyReLU(alpha=lr_alpha))
model.add(BatchNormalization())
model.add(Dropout(dropout_p))

model.add(LSTM(64))
model.add(LeakyReLU(alpha=lr_alpha))
model.add(BatchNormalization())
model.add(Dropout(dropout_p))

model.add(Dense(1))

model.compile(loss='mse', optimizer=tf.keras.optimizers.Adam(), metrics=[tf.keras.metrics.MeanAbsoluteError()])

model.summary()

seed_everything(0)
start = time.time()

n_epoch = 7
batchsize = 64

generator = data_generator_lstm(df_train_tf, window = window, batchsize = batchsize)
valid_generator = data_generator_lstm(df_test_tf, window = window, batchsize = batchsize)
train_steps = (len(df_train_tf) - window) // batchsize
test_steps = (len(df_test_tf) - window) // batchsize

hist = model.fit(generator, 
          steps_per_epoch = train_steps, 
          verbose = True, epochs=n_epoch, 
          validation_data=valid_generator,
          validation_steps = test_steps,
          )

print(f"{(time.time() - start) / 60: 0.2f} min.")

train_for_inv = np.concatenate((np.transpose([hist.history["mean_absolute_error"]]), df_train_tf[:n_epoch, 1:]), axis = 1)
test_for_inv = np.concatenate((np.transpose([hist.history["val_mean_absolute_error"]]), df_train_tf[:n_epoch, 1:]), axis = 1)
train_mae_org_sc = sc.inverse_transform(train_for_inv)[:, 0]
test_mae_org_sc = sc.inverse_transform(test_for_inv)[:, 0]

plt.plot(range(n_epoch), hist.history["loss"], label = "train_MSE_scaled");
plt.plot(range(n_epoch), hist.history["val_loss"], label = "test_MSE_scaled");
plt.legend()
plt.show()

plt.plot(range(n_epoch), train_mae_org_sc, label = "train_MAE_original_scale");
plt.plot(range(n_epoch), test_mae_org_sc, label = "test_MAE_original_scale");
plt.legend()
plt.show()

from tqdm import tqdm
pred_for_inv_feature = np.empty((len(df_test_tf)-window, 1429, window))
for i in tqdm(range(window,len(df_test_tf))):
  pred_for_inv_feature[i-window] = df_test_tf[(i-window):i,1:1430].T
pred_for_inv = model.predict(pred_for_inv_feature)

pred_for_inv = np.concatenate((pred_for_inv, df_test_tf[window:, 1:]), axis=1)

pred = sc.inverse_transform(pred_for_inv)[:,0]
y_test = df_test.iloc[:, 0]

pred_price = [100 * (pred[window] + 1)]
y_test_price = [100 * (y_test[window] + 1)]
for i in range(1, len(pred)):
    pred_price.append(pred_price[i-1] * (pred[i] + 1))
    y_test_price.append(y_test_price[i-1] * (y_test[i] + 1))

plt.plot(df_test.index[window:], pred_price, label = "pred");
plt.plot(df_test.index[window:], y_test_price, label = "sp500");
plt.legend()
plt.show()

start = time.time()

def predict_dist(X, model, num_samples):
    preds = [model(X, training=True) for _ in tqdm(range(num_samples))]
    return np.hstack(preds)

pred_dist_feature = np.empty((len(df_test_tf)-window, 1429, window))
for i in tqdm(range(window, len(df_test_tf))):
  pred_dist_feature[i-window] = df_test_tf[(i-window):i, 1:1430].T

pred_dist = predict_dist(pred_dist_feature, model = model, num_samples = 101)

pred_mean = pred_dist.mean(axis=1)

pred_dist = pd.DataFrame(pred_dist)
pred_dist.index = df_test.index[window:]

for i in tqdm(range(pred_dist.shape[1])):
    pred_for_inv = np.concatenate((np.transpose([pred_dist.iloc[:, i]]), df_test_tf[window:, 1:]), axis = 1)
    pred_dist.iloc[:, i] = sc.inverse_transform(pred_for_inv)[:, 0]

pred_for_inv = np.concatenate((np.transpose([pred_mean]), df_test_tf[window:, 1:]), axis = 1)
pred_mean = sc.inverse_transform(pred_for_inv)[:, 0]

pred_05 = pred_dist.quantile(0.05, axis = 1)
pred_50 = pred_dist.quantile(0.5, axis = 1)
pred_95 = pred_dist.quantile(0.95, axis = 1)

pred_mean_price = [100 * (pred_mean[0] + 1)]
pred_05_price = [100 * (pred_05[0] + 1)]
pred_50_price = [100 * (pred_50[0] + 1)]
pred_95_price = [100 * (pred_95[0] + 1)]
for i in range(1, len(pred_mean)):
    pred_mean_price.append(pred_mean_price[i-1] * (pred_mean[i] + 1))
    pred_05_price.append(pred_05_price[i-1] * (pred_05[i] + 1))
    pred_50_price.append(pred_50_price[i-1] * (pred_50[i] + 1))
    pred_95_price.append(pred_95_price[i-1] * (pred_95[i] + 1))

print(f"{(time.time() - start) / 60: 0.2f} min.")

pred_dist_price = (pred_dist + 1)
pred_dist_price.iloc[0,:] = 100 * pred_dist_price.iloc[0,:]
pred_dist_price = pred_dist_price.cumprod()

pred_05_price = pred_dist_price.quantile(0.05, axis = 1)
pred_50_price = pred_dist_price.quantile(0.5, axis = 1)
pred_95_price = pred_dist_price.quantile(0.95, axis = 1)

pred_mean_price = [100 * (pred_mean[0] + 1)]
for i in range(1, len(pred_mean)):
    pred_mean_price.append(pred_mean_price[i-1] * (pred_mean[i] + 1))

plt.figure(figsize=(20,8))
plt.ylim([70, 200]);

plt.plot(df_test.index[window:], y_test_price, label = "S&P 500", color = "black");
plt.plot(df_test.index[window:], pred_95_price, label = "prediction 95% bound", linestyle = "dashed", color = "red");
plt.plot(df_test.index[window:], pred_mean_price, label = "prediction mean", linestyle = "dotted", color = "purple");
plt.plot(df_test.index[window:], pred_05_price, label = "prediction 5% bound", linestyle = "dashed", color = "blue");
plt.xlabel("date", size=15)
plt.ylabel("index value", size=15)
plt.grid()
plt.legend(prop={'size': 15})
plt.show()