import numpy as np

def mae(truth, preds):
    return np.mean(np.abs(np.array(truth) - np.array(preds)))
