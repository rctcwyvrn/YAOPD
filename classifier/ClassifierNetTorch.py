import torch
import pandas as pd

####################################
# getting the data and preprocessing
####################################

def convertToInts(string, dictionary):
    return [dictionary.get(char) for char in string]

csv_name = "TrainingData.csv"
data = pd.read_csv(csv_name, sep="^", index_col=0)
features = data['features']

valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(features)))}

newData = [convertToInts(script, valid_chars) for script in features]