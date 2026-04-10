import matplotlib
import numpy as np
import pandas as pd
import seaborn as sns

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

# --------------------------------------------------------------------

fig = plt.figure()

ax1 = fig.add_subplot(2, 2, 1)
ax2 = fig.add_subplot(2, 2, 2)
ax3 = fig.add_subplot(2, 2, 3)
ax4 = fig.add_subplot(2, 2, 4)

ax1.hist(np.random.standard_normal(10_000), bins=20, color="black", alpha=0.3)
ax2.scatter(np.arange(30), np.arange(30) + 3 * np.random.standard_normal(30))
ax3.plot(np.random.standard_normal(50).cumsum(), color="black",linestyle="dashed")
ax4.plot(np.random.standard_normal(50).cumsum(), color="black",linestyle="dotted")

# --------------------------------------------------------------------

fig, axes = plt.subplots(2, 2)

for i in range(2):
    for j in range(2):
        axes[i,j].hist(np.random.standard_normal(100), bins=20, color="black", alpha=0.3)
        fig.subplots_adjust(wspace=0, hspace=0)

# --------------------------------------------------------------------

# fig = plt.figure()
# ax = fig.add_subplot()
# data = np.random.standard_normal(50).cumsum()
# ax.plot(data, color="black", linestyle="dashed", label="Default")
# ax.plot(data, color="red", linestyle="dashed", drawstyle="steps-post", label="steps-post") # drawstyle - another option for line style (not default line type)
# ax.legend()
#
# plt.show()
# plt.close()

# --------------------------------------------------------------------

tips = pd.read_csv('tips.csv')
party_counts = pd.crosstab(tips["day"], tips["size"])
print(party_counts)

tips['tip_pct'] = tips['tip'] / (tips['total_bill'] - tips['tip'])
print(tips.head())

print(tips[(tips['day']=='Thur') & (tips['time']=='Dinner')])

print(tips[tips['tip_pct'] > 0.4])

sns.barplot(x="tip_pct", y="day", data=tips, orient='h', hue='time')
plt.show()
# plt.close()
