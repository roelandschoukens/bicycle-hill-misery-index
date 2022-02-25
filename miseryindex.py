import argparse
import json

import numpy as np
np.set_printoptions(precision=4)

import matplotlib.pyplot as plt
plt.style.use('seaborn-white')
plt.style.use('common.mplstyle')

parser = argparse.ArgumentParser(description="Calculate misery index in terms of slope.")
parser.add_argument("--graph", metavar='SLOPE', help="Make a plot for a given slope, write no output. Slope is given as a percentage", type=float)
parser.add_argument("--power", action='store_true', help="Plot power instead of required traction force")
parser.add_argument("-o", "--output", metavar='DATA.json', help="Set output file", default='misery-index.json')
args = parser.parse_args()

# input assumptions:

WALK_PENALTY = 10 # W for every km/h
HALF_RHO_Cd_A2 = 0.35 # ½ ρ Cd A²
Crr = 0.005
M = 85
G = 9.81

RIDE_MIN_SPEED = 6.5
RIDE_MAX_SPEED = 30
RIDE_SPEED_TAB = [ RIDE_MIN_SPEED, 10, 30, RIDE_MAX_SPEED + 0.1]
RIDE_POWER_TAB =  [         160.0, 80, 20, -.01]


def cycling_power(speed, slope, wind):
    """ how much power do we need in this situation
    
    speed: cycling speed
    slope: positive number is uphill, eg. 0.02 for a 2% slope
    wind: positive number for headwind
    
    All speeds in km/h
    
    Returns power in watts"""
    
    v = speed / 3.6
    vRel = (speed + wind) / 3.6
    p = M * G * (Crr + slope) * v + \
            HALF_RHO_Cd_A2 * vRel * abs(vRel) * v
    return np.maximum(p, 0)

v = np.arange(0.1, RIDE_MAX_SPEED + 0.101, 0.1)

v_walk = np.arange(2, 6, 0.1)
pwr_walk = np.interp(v_walk, [2, 6], [140, 10])

v_ride = np.arange(RIDE_MIN_SPEED, RIDE_MAX_SPEED + 0.101, 0.1)
pwr_ride = np.interp(v_ride, RIDE_SPEED_TAB, RIDE_POWER_TAB)

pwr_intersect = np.maximum(
    np.interp(v, v_ride, pwr_ride, left=0),
    np.interp(v, v_walk, pwr_walk, right=0))

pwr_baseline = cycling_power(v, 0, 0)

def calc_power_use(slope, show_plot=False):

    wind =  np.arange(-20, 20.1, 10) if args.graph is not None else np.arange(-25, 25.1, 5)
    p_corr = 1 if args.power else 1 / v

    pwr = [ cycling_power(v, -slope, w) for w in wind ] +\
          [ cycling_power(v,  slope, w) for w in wind ]
    
    # intersection points
    p_speed = np.empty([2 * len(wind)])
    p_power = np.empty([2 * len(wind)])
    p_speed[:] = np.nan
    p_power[:] = np.nan

    for i, p in enumerate(pwr):
        idx = np.nonzero(np.diff(np.sign(pwr_intersect - p)))[0]
        j = idx[-1]
        p_speed[i] = v[j]
        p_power[i] = p[j] + WALK_PENALTY * v[j] * (v[j] < RIDE_MIN_SPEED)

    energy = p_power / p_speed
    avg = np.average(energy)

    if show_plot:
        fig, ax = plt.subplots(figsize=[6, 4])
        
        # print table
        for pv, pp, pe, w in zip(p_speed, p_power, energy, np.concatenate((wind, wind))):
            print(f'wind: {w:3.0f}km/h | {pv:4.1f}km/h  {pp:4.1f}W  {pe:5.2f}Wh/km')
        print()
        print(f'Average: {avg:5.2f}Wh/km')

        # reference: light gray
        ax.plot(v, pwr_baseline * p_corr, '--', color=(.8, .8, .8))

        for pp, w in zip(pwr, np.concatenate((wind, wind))):
            # tailwind: blue
            if w < 0:   
                c = (.2, .4, 1)
            elif w > 0:
                # headwind: red
                c = (.8, .2, .3)
            else:
                # still: yellow
                c = (.7, .6, 0)
            ax.plot(v, pp * p_corr, color=c)

        # ref: green
        ax.plot(v_walk, pwr_walk * (1 if args.power else 1/v_walk), '--', color=(0.0, 0.6, 0.2))
        ax.plot(v_ride, pwr_ride * (1 if args.power else 1/v_ride), '--', color=(0.0, 0.6, 0.2))

        # intersections
        i_corr = 1 if args.power else 1 / p_speed
        ax.scatter(p_speed, p_power * i_corr, 9, color=(.1, .1, .1))

        ax.grid(True)
        ax.set_title(f'slope: {slope*100:.0f}%')
        if args.power:
            ax.set_ylim([-3, 145])
            ax.set_ylabel('Power (W)')
        else:
            ax.set_ylim([-2, max(30, 1+np.max(energy))])
            ax.set_ylabel('Energy use (Wh/km)')

        ax.set_xlabel('Speed (km/h)')
        plt.show()

    return avg

mi_list = []
pwr_0 = None

if args.graph is not None:
    calc_power_use(args.graph * .01, show_plot=True)
else:
    for sl in np.arange(0, 0.25001, 0.005):
        pwr = calc_power_use(sl, show_plot=False)
        if sl == 0:
            pwr_0 = pwr
        mi = pwr/pwr_0 - 1
        mi_list.append(dict(slope=sl, mi=mi, p=pwr))
        print(f"misery index for {100*sl:4.1f}%: {mi:4.1f}  ({pwr:.2f})")

    f = open(args.output, 'wt')
    json.dump(mi_list, f)
