import torch

####################################
# getting the data and preprocessing
####################################

data = ["oH bOy iT's An oBFusCaTiON"]

valid_chars = {x:idx+1 for idx, x in enumerate(set(''.join(data)))}

print(data)
print(len(valid_chars))