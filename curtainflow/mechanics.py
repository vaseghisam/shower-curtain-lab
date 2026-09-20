"""Hanging-strip mechanics, per metre of curtain width. All inputs are SI."""
import numpy as np
from scipy.integrate import solve_ivp


def exact_profile(s, H=1.8, sigma=.2, hem=.1, pressure=.2, g=9.81):
    s = np.asarray(s, dtype=float)
    if H <= 0 or sigma <= 0 or hem < 0:
        raise ValueError('Require H>0, sigma>0, hem>=0.')
    if hem == 0:
        return pressure*s/(sigma*g)
    a = hem/sigma
    return pressure/(sigma*g)*(s-a*np.log1p(s/(H-s+a)))


def matrices(n=128, H=1.8, sigma=.2, hem=.1, g=9.81):
    """Linear-element stiffness and lumped mass; top degree of freedom omitted."""
    s = np.linspace(0, H, n+1)
    h = H/n
    k = g*(sigma*(H-(s[:-1]+s[1:])/2)+hem)/h
    mass = np.full(n, sigma*h)
    mass[-1] = sigma*h/2+hem
    weights = np.full(n, h)
    weights[-1] /= 2
    return s, k, mass, weights


def elastic(y, k):
    """K y for shape (..., n), including a fixed zero top displacement."""
    jump = np.diff(np.concatenate((np.zeros(y.shape[:-1]+(1,)), y), axis=-1), axis=-1)
    flux = k*jump
    out = flux.copy()
    out[..., :-1] -= flux[..., 1:]
    return out


def equilibrium(pressure, n=128, **kwargs):
    s, k, mass, weights = matrices(n=n, **kwargs)
    q = pressure(s[1:]) if callable(pressure) else np.full(n, pressure)
    y = np.cumsum(np.cumsum((q*weights)[::-1])[::-1]/k)
    return s, np.r_[0, y]


def transient(n=64, H=1.8, sigma=.2, hem=.1, pressure=.2, damping=.05,
              ramp=.3, duration=5., frames=101, clearance=None):
    """Integrate M y'' + C y' + K y = q(t) w using adaptive DOP853.

    Clearance, if given, defines a flat first-contact plane. Integration stops
    at the earliest nodal contact. No post-contact or adhesion model is used.
    """
    s,k,m,w=matrices(n,H,sigma,hem)
    def rhs(t,state):
        y,v=state[:n],state[n:]
        amplitude = 1. if ramp == 0 else min(t/ramp,1.)
        q = pressure(s[1:]) if callable(pressure) else pressure
        return np.r_[v,(q*amplitude*w-elastic(y,k)-damping*w*v)/m]
    def contact(t,state):
        return clearance-np.max(state[:n])
    contact.terminal=True
    contact.direction=-1
    t=np.linspace(0,duration,frames)
    sol=solve_ivp(rhs,(0,duration),np.zeros(2*n),method='DOP853',t_eval=t,
                  rtol=2e-8,atol=2e-10,events=contact if clearance is not None else None)
    if not sol.success:
        raise RuntimeError(sol.message)
    event = float(sol.t_events[0][0]) if clearance is not None and len(sol.t_events[0]) else None
    t_saved=sol.t
    states=sol.y[:n].T
    if event is not None and event>t_saved[-1]:
        t_saved=np.r_[t_saved,event]
        states=np.vstack([states,sol.y_events[0][0,:n]])
    y=np.c_[np.zeros(len(t_saved)),states]
    return dict(t=t_saved,s=s,y=y,first_contact=event)
