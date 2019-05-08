# AMZ-Driverless
#  Copyright (c) 2019 Authors:
#   - Huub Hendrikx <hhendrik@ethz.ch>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import numbers
import operator

import rosbag

from rbb_tools.extraction.extractor import AbstractExtractionPlugin
from rbb_tools.extraction.registry import Product


def safe_file_name(name, replace="-"):
    return "".join([(c if c.isalpha() or c.isdigit() or c==' ' else replace) for c in name]).rstrip()


class TimeSeriesField(object):
    def __init__(self, label, msg_attr_name, symbol="", unit="?", format="{0:.9g}", default_color="#0000FF"):
        self.values = []
        self._getter = operator.attrgetter(msg_attr_name)
        self.label = label
        self.symbol = symbol
        self.unit = unit
        self.format = format
        self.default_color = default_color
        self._error = False

    def format_value(self, value):
        return self.format.format(value)

    def append_value(self, value):
        if not isinstance(value, numbers.Number):
            raise RuntimeError("Time series value is not a number")

        self.values.append(value)

    def append_value_from_msg(self, msg):
        try:
            value = self._getter(msg)
        except:
            self._error = True
            value = -1

        self.append_value(value)

    def get_data(self):
        return {
            'label': self.label,
            'symbol': self.symbol,
            'unit': self.unit,
            'default_color': self.default_color,
            'error': self._error
        }


class TimeSeriesSet(object):
    def __init__(self, name):
        self.name = name
        self.time_secs = []
        self.time_format = "{0:.9f}"
        self.fields = {}
        self._time_offset = 0
        self._first_message = True
        self._use_bag_time = False

    def is_empty(self):
        return len(self.time_secs) == 0

    def set_time_offset(self, offset):
        offset = int(offset)  # Only take seconds
        self._time_offset = offset

    def append_ros_stamp(self, stamp):
        secs = stamp.secs - self._time_offset
        nsecs = stamp.nsecs

        t = float(secs) + float(nsecs) * (10.0**-9)
        self.time_secs.append(t)

    def append_msg(self, msg, t):
        if self._first_message:
            self._first_message = False

            if hasattr(msg, 'header'):
                self._use_bag_time = False
            else:
                self._use_bag_time = True

        if self._use_bag_time:
            self.append_ros_stamp(t)
        else:
            self.append_ros_stamp(msg.header.stamp)

        for field in self.fields:
            self.fields[field].append_value_from_msg(msg)

    def get_data(self):
        fields = {}

        for f in self.fields:
            fields[f] = self.fields[f].get_data()

        return {
            'name': self.name,
            'time_offset': self._time_offset,
            'fields': fields
        }


class CsvWriter(object):

    def __init__(self, series):
        self._series = series

    def write(self, filename):
        with open(filename, 'w') as file:
            t_iter = iter(self._series.time_secs)
            value_iters = []

            # Write csv header
            line = "t,"
            for f in self._series.fields:
                field = self._series.fields[f]
                field_iter_tuple = (field, iter(field.values))
                value_iters.append(field_iter_tuple)
                line += f + ","

            file.write(line[:-1] + "\n")  # Skip last comma

            # Write the values
            for t in t_iter:
                time_str = self._series.time_format.format(t) + ","

                values = [i[0].format_value(next(i[1])) for i in value_iters]
                file.write(time_str + ",".join(values) + "\n")


class TimeSeriesPlugin(AbstractExtractionPlugin):

    def __init__(self, configuration, logger, resource_directory):
        super(TimeSeriesPlugin, self).__init__(configuration, logger, resource_directory)

    def check_topics(self, topics):
        return True

    def get_plugin_meta_data(self):
        return {
            'name': 'Time Series Extractor',
            'version': '0.0.1'
        }

    def get_default_configuration(self):
        return {

        }

    def extract(self, bag_file, topics, tmp_dir, output_dir, product_factory):

        series_config = self.config("topics")
        time_series_sets = {}

        # Setup the configuration
        self._logger.info("Time series sets:")
        for topic in series_config:
            bag_topic = ""
            if topic in topics:
                bag_topic = topics[topic]
            else:
                self._logger.warning("Configured time series topic '%s' is not in matched topic list!" % topic)
                bag_topic = topic

            t_set = None
            if 'name' in series_config[topic]:
                t_set = TimeSeriesSet(series_config[topic]['name'])
            else:
                t_set = TimeSeriesSet(topic)

            self._logger.info(" - %s -> %s" % (topic, bag_topic))
            config_fields = series_config[topic]['series']
            for field in config_fields:
                config_field = config_fields[field]
                t_field = TimeSeriesField(config_field['label'] if 'label' in config_field else field, field)

                if 'symbol' in config_field:
                    t_field.symbol = config_field['symbol']

                if 'unit' in config_field:
                    t_field.unit = config_field['unit']

                if 'format' in config_field:
                    t_field.format = config_field['format']

                if 'default_color' in config_field:
                    t_field.default_color = config_field['default_color']

                self._logger.info("   - %s (%s)" % (field, t_field.label))

                t_set.fields[field] = t_field

            time_series_sets[bag_topic] = t_set

        with rosbag.Bag(bag_file, "r") as bag:
            bag_topics = list(time_series_sets.keys())
            info = bag.get_type_and_topic_info(topic_filters=bag_topics)

            for topic in bag_topics:
                if not topic in info.topics:
                    self._logger.warning("Topic %s is not in the bag!" % topic)

            # Set the offset, so that the time series start around 0 seconds
            bag_start = bag.get_start_time()
            for t_set in time_series_sets:
                time_series_sets[t_set].set_time_offset(bag_start)

            for topic, msg, t in bag.read_messages(topics=bag_topics):
                t_set = time_series_sets[topic]
                t_set.append_msg(msg, t)

        product = product_factory.new() # type: Product
        product.set_type("time-series")
        product.set_title("Time Series")
        product.set_topics(topics)

        data = {
            'version': 1,
            'series': []
        }

        series = data['series']

        for t in time_series_sets:
            t_set = time_series_sets[t]
            if t_set.is_empty():
                self._logger.info("Skipping empty set '%s'" % t_set.name)
                continue

            filename = safe_file_name(t_set.name.replace(" ","_").lower()) + ".csv"
            writer = CsvWriter(t_set)
            writer.write(output_dir + "/" + filename)
            product.add_file(filename, filename, "text/csv")

            t_set_data = t_set.get_data()
            t_set_data['file'] = filename
            series.append(t_set_data)

        product.set_data(data)

        return [product]


plugin = TimeSeriesPlugin
