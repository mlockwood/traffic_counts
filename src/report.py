import csv
import datetime
import os

def convert_objects(objects):
    records = {}
    for obj in objects:
        records[objects[obj]] = True
    return records

class Report:

    path = '' # '/reports/ridership'
    name = '' # 'Ridership_'

    def __init__(self, records):
        self._records = records # {record_obj: True}

    @staticmethod
    def _dict_to_matrix(data):
        # Set outer and inner keys
        outer_keys = sorted(data.keys())
        inner_keys_D = {}
        # Find all inner key values
        for o_key in outer_keys:
            for i_key in data[o_key]:
                inner_keys_D[i_key] = True
        inner_keys = sorted(inner_keys_D.keys())
        # Set matrix
        matrix = [[''] + inner_keys]
        for o_key in outer_keys:
            row = [o_key]
            for i_key in inner_keys:
                # If inner key is found for the outer key, set amount
                if i_key in data[o_key]:
                    row.append(data[o_key][i_key])
                # Otherwise inner key DNE for outer key, set to 0
                else:
                    row.append(0)
            matrix.append(row)
        return matrix

    @staticmethod
    def _recurse_data(data, features, writer, prev=[], i=0,
                      limit=2):
        if i == (len(features) - limit):
            matrix = Report._dict_to_matrix(data)
            # Write title by previous values
            writer.writerow(prev)
            # Write matrix rows
            for row in matrix:
                writer.writerow(row)
            # Write empty row
            writer.writerow([])
        else:
            for key in sorted(data.keys()):
                Report._recurse_data(data[key], features, writer, prev + [
                                str(features[i]).title() + ': ' + str(key)],
                                     i+1, limit=limit)
        return True
        
    def _prepare(self, features, start, end):
        # If no features, return total only
        if not features:
            count = 0
            for obj in self._records:
                count += obj._count
            return {'Total': count}
        # If features, produce variable data structure
        data = {}
        for obj in self._records:
            # If outside of the daterange, continue
            if obj._date < start or obj._date > end:
                continue
            # If inside the daterange, process count information
            i = 0
            DS = 'data'
            # Process all except the last feature
            while i < (len(features) - 1):
                try:
                    if eval('obj._' + features[i]) not in eval(DS):
                        exec(DS + '[\'' + eval('obj._' + features[i]) +
                             '\']={}')
                    DS += '[\'' + eval('obj._' + features[i]) + '\']'
                except TypeError:
                    if eval('obj._' + features[i]) not in eval(DS):
                        exec(DS + '[' + str(eval('obj._' + features[i])) +
                             ']={}')
                    DS += '[' + str(eval('obj._' + features[i])) + ']'
                i += 1
            # Process the counts of the last feature
            try:
                exec(DS + '[\'' + eval('obj._' + features[-1]) + '\']=' + DS +
                     '.get(\'' + eval('obj._' + features[-1]) +
                     '\', 0) + obj._count')
            # Except if boolean
            except TypeError:
                exec(DS + '[' + str(eval('obj._' + features[-1])) + ']=' + DS +
                     '.get(' + str(eval('obj._' + features[-1])) +
                     ', 0) + obj._count')
        return data    

    def generate(self, features, start=datetime.date(2015, 8, 31),
                end=datetime.date.today()):
        data = self._prepare(features, start, end)
        if not os.path.isdir(Report.path):
            os.makedirs(Report.path)
        writer = csv.writer(open(Report.path + Report.name +
                    '_'.join(features).title() + '.csv', 'w',
            newline=''), delimiter=',', quotechar='|')
        Report._recurse_data(data, features, writer)
        return True
