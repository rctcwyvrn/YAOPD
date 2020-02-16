import keras
from keras.preprocessing.sequence import pad_sequences
from keras.layers import LSTM, Dropout, Dense, Embedding
from sklearn import model_selection
import pandas as pd
import numpy as np

####################################
# parameters
####################################
n_epochs = 2
embedding_vector_length = 128


####################################
# getting the data and preprocessing
####################################

def convertToInts(string, dictionary):
    return [dictionary.get(char) for char in string]

#load data
csv_name = "TrainingData.csv"
data = pd.read_csv(csv_name, sep="^", index_col=0)
X = data['features']
y = data['labels']

#encode in numerical form
valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(X)))}
X = [convertToInts(script, valid_chars) for script in X]

#define variable parameters
num_encoder_tokens = len(valid_chars)
maxlen = len(max(X, key=len))
sample_len = maxlen
classes = set(y)


#add padding
X = pad_sequences(X, maxlen=maxlen)

#conver y to binary
label_dict = {x:idx for idx, x in enumerate(set(y))}
y = [convertToInts(label, label_dict) for label in y]

#define training and test sets
X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=0.20)

print(type(X_train))
####################################
# neural net
####################################

#initialize model layers
model = keras.Sequential()
model.add(Embedding(num_encoder_tokens, embedding_vector_length, input_length=sample_len))
model.add(LSTM(100))
model.add(Dropout(0.2))
model.add(Dense(len(classes), activation='sigmoid'))

#compile model
model.compile(loss='categorical_crossentropy', optimizer='adam', metrics=['accuracy'])
print(model.summary())

#train model
print(X_train.shape)
model.fit(np.array(X_train), np.array(y_train), validation_data=(np.array(X_test), np.array(y_test)), epochs=n_epochs, batch_size=64)
