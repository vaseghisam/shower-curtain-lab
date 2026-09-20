"""Time integration of saved calculated loads; never rescales pressure."""
import numpy as np


def mean_over_window(time, field, start=10., end=12.):
    """Exact integral of the piecewise-linear saved signal over [start,end]."""
    time=np.asarray(time)
    if end<=start or start<time[0]-1e-9 or end>time[-1]+1e-9:
        raise ValueError('Averaging window must lie inside the saved simulation')
    times=np.r_[start,time[(time>start+1e-9)&(time<end-1e-9)],end]
    idx=np.clip(np.searchsorted(time,times,side='right')-1,0,len(time)-2)
    shape=(-1,)+(1,)*(np.ndim(field)-1)
    fraction=((times-time[idx])/(time[idx+1]-time[idx])).reshape(shape)
    values=field[idx]*(1-fraction)+field[idx+1]*fraction
    return np.trapezoid(values,times,axis=0)/(end-start)
