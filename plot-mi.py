import json
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
plt.style.use('seaborn-white')
plt.style.use('common.mplstyle')

""" this script simply plots the misery index vs. slope. """

# set filename here
mi_list = json.load(open("misery-index.json"))

ax = plt.gca()
ax.plot(
    [x['slope'] for x in mi_list[0:20]],
    [x['mi'] for x in mi_list[0:20]])
ax.set_xlim(xmin=0)
ax.set_ylim(ymin=0)
ax.grid(axis='both')
ax.xaxis.set_major_formatter(mtick.PercentFormatter(1))
ax.set_xlabel('Slope')
ax.set_ylabel('Misery Index')

plt.show()
