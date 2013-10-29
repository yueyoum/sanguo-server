import os
import sys
import csv

from head import DEFINITION_PATH


csv_file = sys.argv[1]
output_file = os.path.join(DEFINITION_PATH, 'level_totalexp.py')

data = ["level_totalexp_dict = {\n"]
with open(csv_file, 'r') as f:
    reader = csv.reader(f)
    for level, exp in reader:
        data.append("    {0}: {1},\n".format(level.strip(), exp.strip()))

data.append("}\n")

with open(output_file, 'w') as f:
    f.writelines(data)

