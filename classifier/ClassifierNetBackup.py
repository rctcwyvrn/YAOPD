import keras
import InputProcessor
from sklearn import model_selection

n_epochs
#Define dataset
X, y = InputProcessor.generateData()
#at the moment this won't do anything because X and y don't exist
X_train, X_test, y_train, y_test = model_selection.train_test_split(X, y, test_size=0.20)

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
model.fit(X_train, y_train, validation_data=(X_test, y_test), epochs=n_epochs, batch_size=64)
