import os
import pandas as pd
import glob

# get directory
origin_dir = "../generator/res/"

# glob load data
general_name = "dataset-*-obfs.ps1"
general_file_dir = os.path.join(origin_dir, general_name)
file_names = glob.glob(general_file_dir)

#load all files into dataframes
df_list = [pd.read_csv(file_name, header=None, names=["script"]) for file_name in file_names]

#concatenate dataframes together
big_df = pd.concat(df_list, ignore_index=True)

big_df.rename(columns={'script': 'features'}, inplace=True)

#write to csv
csv_name = "TrainingData.csv"
big_df.to_csv(path_or_buf=csv_name)