#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import cdsapi
import xarray as xr

import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import matplotlib.cm as cm
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import datetime

import numpy as np

import pandas as pd


DATADIR = '.'

fn = f'{DATADIR}/data_sfc_20240625_0000.nc'
ds = xr.open_dataset(fn)
da = ds['aod550']

city_group = [
    {
        'city_group_name': '大兴安岭地区',
        'city_group_index': {            
            '漠河': {'latitude':52.98, 'longitude':122.53},
            '塔河': {'latitude':52.33, 'longitude':124.71},
            '呼玛': {'latitude':51.72, 'longitude':126.66}, 
            '加格达奇': {'latitude':50.42, 'longitude':124.13},
            '呼中': {'latitude':52.03, 'longitude':123.59}
        }
    },
    {
        'city_group_name': '呼伦贝尔中部及南部地区2',
        'city_group_index': {
            '伊敏河': {'latitude':48.58, 'longitude':119.79},
            '红花尔基': {'latitude':48.27, 'longitude':119.99},  
            '牙克石': {'latitude':49.29, 'longitude':120.73},
            '博克图': {'latitude':48.75, 'longitude':121.91}, # 48.752318, 121.914976
            '扎兰屯': {'latitude':48.00, 'longitude':122.75} # 48.001883, 122.745577
        }
    }
]

CITY_GROUP_NUM_LIMIT = 5
TOP_COORD = 0.93
BOTTOM_COORD_MIN = 0.05
HEIGHT_OF_ONE_AX = (TOP_COORD - BOTTOM_COORD_MIN) / CITY_GROUP_NUM_LIMIT




# 自定义颜色映射：低 → 高
colorscale = [
    (0.0, "#00cd00"),  # green
    (0.3, "#E4C200"),  # yellow
    (0.6, "#ff0000"),  # red
    (1.0, "#000000")   # black
]
# 创建 colormap 对象
custom_cmap = mcolors.LinearSegmentedColormap.from_list("green_yellow_red_black", colorscale)
# 数据标准化（你可以换成实际数据范围）
norm = mcolors.Normalize(vmin=0, vmax=1.5, clip=True)

# rgba = custom_cmap(norm(1.2))
# rgb_255 = tuple(int(255 * x) for x in rgba[:3])
# print("RGB:", rgb_255)
# hex_color = mcolors.to_hex(rgba)
# print("HEX:", hex_color)
# exit()


def plot_pic(city_group_name, city_group_index):
    print(city_group_name)
    print(city_group_index)
    if len(city_group_index) == 0:
        print('plot_pic : len(city_group_index) == 0 : no data exist, pass')
        return
    
    if len(city_group_index) > CITY_GROUP_NUM_LIMIT:
        print('plot_pic : len(city_group_index) > 6 :' + str(len(city_group_index)) + ', pass')
        return

    city_data = {}
    for city, coordinate in city_group_index.items():
        city_data[city] = da.sel(latitude=coordinate['latitude'], longitude=coordinate['longitude'], method='nearest')

    plt.rcParams['font.sans-serif']=['Yuanti SC']
    fig, axes = plt.subplots(nrows = len(city_data), ncols = 1, figsize = (9, 12), dpi=70, sharex = False)
    
    
    time_limit = set()

    for ax, city, data in zip(axes, city_data.keys(), city_data.values()): 
        reference_time = data.coords['forecast_reference_time'].values[0]  # <class 'numpy.datetime64'>
        periods = data.coords['forecast_period'].values  # <class 'numpy.ndarray'>: int
        reference_pd_time = pd.to_datetime(reference_time) # <class 'pandas._libs.tslibs.timestamps.Timestamp'>
        time_utc = reference_pd_time + pd.to_timedelta(periods) # <class 'pandas.core.indexes.datetimes.DatetimeIndex'>
        time_utc = time_utc.sort_values()
        time_local = time_utc.tz_localize('UTC').tz_convert('Asia/Shanghai') # <class 'pandas.core.indexes.datetimes.DatetimeIndex'>
        time_local_py = time_local.to_pydatetime() # <class 'numpy.ndarray'>: datetime.datetime

        time_limit.add(time_local.min())
        time_limit.add(time_local.max())

        x_vals = list(range(len(time_local_py)))

        x_vals_ticks = [idx for idx, dt in enumerate(time_local_py) if dt.hour % 6 == 0]
        

        def custom_formatter(idx):
            if idx >= len(time_local_py):
                return ""
            dt = time_local_py[idx]
            # return f"{dt.hour}时"
            if dt.hour == 0:
                # return f"{dt.hour}时\n{dt.month}月{dt.day}日"
                return f"{dt.hour}\n|"
            elif dt.hour == 12:
                return f"{dt.hour}\n{dt.month}月{dt.day}日"
            else:
                return f"{dt.hour}"    
        x_vals_labels = list(map(custom_formatter, x_vals_ticks))

        aod_values = [val[0] for val in data.values]

        colors = [custom_cmap(norm(val)) for val in aod_values]

        ax.set_xlim(-1, len(time_local_py))
        ax.set_xticks(x_vals_ticks)
        ax.set_xticklabels(x_vals_labels, fontsize=12,  ha='center',va='top', weight='bold')
        ax.xaxis.set_minor_locator(ticker.AutoMinorLocator(6))
        # ax.set_xlabel("Hour of Day")

        ax.set_ylim(0, 3.0)    
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1.0))
        ax.yaxis.set_minor_locator(ticker.AutoMinorLocator(2))
        # ax.set_ylabel(city, rotation=0, labelpad=10, fontsize=15, ha='right', va='center')

        city_label = city + ' ' + str(city_group_index[city]['latitude']) + '°N, ' + \
                    str(city_group_index[city]['longitude']) + '°E'
        ax.text(0.01, 0.96, city_label, transform=ax.transAxes,
                ha='left', va='top', fontsize=14)

        ax.grid(True, linestyle='--', alpha=0.3)
        ax.grid(True, which='minor', axis='y', linestyle='--', alpha=0.3)

        

        # set solid gridline of midnight
        x_vals_ticks_hours = [dt.hour for idx, dt in enumerate(time_local_py) if dt.hour % 6 == 0]
        x_gridlines = ax.get_xgridlines()
        for x_gridline, hour in zip(x_gridlines, x_vals_ticks_hours):
            if hour == 0:
                x_gridline.set_linewidth(1.5)
                x_gridline.set_linestyle('-')
                x_gridline.set_alpha(0.3)

        ax.bar(x_vals, aod_values, width=0.9, color=colors)


    earliest = min(time_limit)
    latest = max(time_limit)
    city_group_value_params = f"Total AOD @ 550nm\n"\
            f"{earliest.year:04d}/{earliest.month:02d}/{earliest.day:02d} {earliest.hour:02d}:{earliest.minute:02d}"\
            f" - {latest.year:04d}/{latest.month:02d}/{latest.day:02d} {latest.hour:02d}:{latest.minute:02d} UTC+8"

    # fig.suptitle(city_group_name, fontsize=30, weight='bold',ha='right')
    fig.text(0.11, 0.98, city_group_name,
         ha='left', va='top',
         fontsize=20, weight='bold')
    fig.text(0.115, 0.95, city_group_value_params,
         ha='left', va='top',
         fontsize=12, weight='bold')
    
    # plt.tight_layout()
    botm = BOTTOM_COORD_MIN
    if len(city_group_index) < CITY_GROUP_NUM_LIMIT:
        botm = BOTTOM_COORD_MIN + HEIGHT_OF_ONE_AX * (CITY_GROUP_NUM_LIMIT - len(city_group_index))
    plt.tight_layout(rect=[0.08, round(botm,2), 0.92, TOP_COORD])


    time_str = f"{earliest.year:04d}{earliest.month:02d}{earliest.day:02d}{earliest.hour:02d}{earliest.minute:02d}_"
    plt.savefig(time_str + f"{city_group_name}_aod120h.png", dpi=300, transparent=True)
    # plt.savefig(f"{city_group_name}_{str(datetime.datetime.now())}_aod120h.png", dpi=300, transparent=True)
    # plt.show()


for group in city_group:
    plot_pic(group['city_group_name'], group['city_group_index'])