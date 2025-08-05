#!/usr/bin/env python3
import sys
import pandas as pd

csv, impl, param_set, time_ms, status, timestamp = sys.argv[1:7]

df = pd.read_csv(csv)
df['mult_type'] = impl
df['mult_param_set'] = param_set
df['mult_time_ms'] = float(time_ms)
df['exit_code'] = int(status)
df['timestamp'] = timestamp

df.to_csv(csv, index=False)
