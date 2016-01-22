
import csv
import datetime
import os
import re
import sys

"""
Closed Classes----------------------------------------------------------
"""
class PathSetter:

    def set_pythonpath(directory='', subdirectory=''):
        if directory:
            directory = PathSetter.find_path(directory)
            if subdirectory:
                if directory[-1] != '/' and subdirectory[0] != '/':
                    directory += '/'
                directory += subdirectory
        else:
            directory = os.getcwd()
        sys.path.append(directory)
        return True

    def find_path(directory):
        match = re.search(str(directory), os.getcwd())
        if not match:
            raise IOError(str(directory) + ' is not in current working ' +
                          'directory of ' + str(os.getcwd()))
        return os.getcwd()[:match.span()[0]] + '/' + directory

PathSetter.set_pythonpath()

"""
Main Classes------------------------------------------------------------
"""
class Sheet:

    objects = {}
    ID_generator = 1
    count_path = PathSetter.find_path('traffic_counts')

    def __init__(self, file):
        self._file = file
        self._records = {}
        self.set_id()

    def set_id(self):
        self._ID = hex(Sheet.ID_generator)
        Sheet.ID_generator += 1
        Sheet.objects[self._ID] = self
        return True

    @staticmethod
    def process():
        #Sheet.load_config()
        for dirpath, dirnames, filenames in os.walk(Sheet.count_path +
                                                    '/data'):
            for filename in [f for f in filenames if re.search(
                '\d{4}-\d{2}-\d{2}', f)]:
                obj = Sheet((str(dirpath) + '/' + str(filename)))
                obj.read_sheet()
        #Sheet.write_sheets()
        return True

    def read_sheet(self):
        """Extract each record from the sheet and create a Record class
        object.
        """
        reader = open(self._file, 'r')
        records = []
        for row in reader:
            records.append(row.split(','))
        for record in records[1:]:
            dt = record[0].split()
            """
            IMPORTANT----------------------------------------------------------
            Remember to update the indices if the columns change.
            """
            indices = [('EB', 4), ('NB', 34), ('SB', 64), ('WB', 94)]
            for I in indices:
                self._records[Record(self, dt[0], dt[1], I[0],
                                     int(record[I[1]]))] = True
        return True

class Record:

    objects = {}
    ID_generator = 1

    def __init__(self, count_file, datestr, time, direction, count):
        self._count_file = count_file
        self._datestr = datestr
        self._time = time
        self._direction = direction
        self._count = count
        self.set_date()
        self.set_time()
        self.set_id()

    def set_date(self):
        date = re.split('-', self._datestr)
        self._year = int(date[0])
        self._month = int(date[1])
        self._day = int(date[2])
        self._date = datetime.date(self._year, self._month, self._day)
        self._week = (str(self._date.isocalendar()[0]) + '_' +
                      str(self._date.isocalendar()[1]))
        self._dow = str(self._date.isocalendar()[2])
        return True

    def set_time(self):
        time = re.split(':', self._time)
        self._hour = int(time[0])
        self._minute = int(time[1])
        self._second = int(time[2])

    def set_id(self):
        self._ID = hex(Record.ID_generator)
        Record.ID_generator += 1
        Record.objects[self._ID] = self
        return True

class Report:

    @staticmethod
    def _prepare(features, start, end):
        # If no features, return total only
        if not features:
            count = 0
            for record in Record.objects:
                count += Record.objects[record]._count
            return {'Total': count}
        # If features, produce variable data structure
        data = {}
        for record in Record.objects:
            obj = Record.objects[record]
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

    @staticmethod
    def generate(features, start=datetime.date(2015, 8, 31),
                end=datetime.date.today()):
        data = Report._prepare(features, start, end)
        if not os.path.isdir(Sheet.count_path + '/reports/'):
            os.makedirs(Sheet.count_path + '/reports/')
        writer = csv.writer(open(Sheet.count_path +
            '/reports/Count_' + '_'.join(features).title() +
            '.csv', 'w', newline=''), delimiter=',', quotechar='|')
        Report._recurse_data(data, features, writer)
        return True

"""
User Interface----------------------------------------------------------
"""
Sheet.process()

# Start date of 1 JAN 2012 and End date of 31 DEC 2020
start = datetime.date(2012, 1, 1)
end = datetime.date(2020, 12, 31)

print('Finished sheet processing')

Report.generate(['year', 'month', 'day', 'hour', 'direction'],
                start=start, end=end)
Report.generate(['week', 'dow', 'direction'])
        
