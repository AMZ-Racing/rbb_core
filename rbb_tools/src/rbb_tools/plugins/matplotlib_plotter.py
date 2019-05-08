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

import matplotlib
matplotlib.use('agg')
import matplotlib.pyplot as plt
plt.switch_backend('agg')
import operator

import rosbag

from rbb_tools.extraction.extractor import AbstractExtractionPlugin
from rbb_tools.extraction.registry import Product


def safe_file_name(name, replace="-"):
    return "".join([(c if c.isalpha() or c.isdigit() or c==' ' else replace) for c in name]).rstrip()


class DataColumn(object):
    def __init__(self, config):
        self._values = []
        self._name = config['name']
        self._column_type = config['type']
        self._topic = ""

    def _topic_name_and_field(self, topic):
        parts = topic.split(".")
        if len(parts) < 2:
            raise RuntimeError("Topic field should mention at least a topic name and a data field")

        return parts[0].strip(), ".".join(parts[1:]).strip()

    def get_topic_name(self):
        return self._topic

    def set_topic_name(self, t):
        self._topic = t

    def get_name(self):
        return self._name

    def message(self, t, topic, data):
        raise NotImplementedError()

    def post_process(self, columns):
        pass

    def get_values(self):
        return self._values


class RostimeColumn(DataColumn):

    def __init__(self, config):
        super(RostimeColumn, self).__init__(config)
        self._topic, self._field = self._topic_name_and_field(config['topic'])
        self._getter = operator.attrgetter(self._field)
        self._zero = "zero" in config and config["zero"]
        self._first_message = True
        self._time_offset = 0

    def message(self, t, topic, data):
        if topic == self._topic:
            rostime_msg = self._getter(data)

            if self._first_message and self._zero:
                self._time_offset = rostime_msg.secs

            self._first_message = False
            secs = rostime_msg.secs - self._time_offset
            nsecs = rostime_msg.nsecs
            t = float(secs) + float(nsecs) * (10.0 ** -9)
            self._values.append(t)


class RawColumn(DataColumn):

    def __init__(self, config):
        super(RawColumn, self).__init__(config)
        self._topic, self._field = self._topic_name_and_field(config['topic'])
        self._getter = operator.attrgetter(self._field)
        self._zero = "zero" in config and config["zero"]
        self._first_message = True
        self._offset = 0

    def message(self, t, topic, data):
        if topic == self._topic:
            value = self._getter(data)

            if self._first_message:
                self._offset = value
            self._first_message = False

            if self._zero:
                self._values.append(value - self._offset)
            else:
                self._values.append(value)


class Figure:
    def __init__(self, config, columns):
        self._config = config
        self._columns = columns

    def plot(self, bag_length=0):

        if 'width' in self._config and 'height' in self._config:
            width = self._config['width'] / 90.0
            height = self._config['height'] / 90.0
            if 'scale_width_with_time' in self._config and self._config['scale_width_with_time']:
                width *= bag_length

            plt.figure(figsize=(width, height), dpi=90)
        else:
            plt.figure()

        if "title" in self._config:
            plt.title(self._config['title'])

        if "xlabel" in self._config:
            plt.xlabel(self._config['xlabel'])

        if "ylabel" in self._config:
            plt.ylabel(self._config['ylabel'])

        if "aspect" in self._config:
            plt.gca().set_aspect(self._config['aspect'])

        if "xlim" in self._config:
            plt.xlim(self._config['xlim']['min'], self._config['xlim']['max'])

        if "ylim" in self._config:
            plt.ylim(self._config['ylim']['min'], self._config['ylim']['max'])

        has_at_least_one_plot = False
        for plot_config in self._config['plots']:
            plot = None
            if plot_config['type'] == 'lineplot':
                plot = LinePlot(plot_config, self._columns)
            elif plot_config['type'] == 'scatterplot':
                plot = ScatterPlot(plot_config, self._columns)
            elif plot_config['type'] == 'histogram':
                plot = Histogram(plot_config, self._columns)
            else:
                raise RuntimeError("Plot type '%s' not found" % plot_config['type'])

            if plot.plot():
                has_at_least_one_plot = True

        if "legend" in self._config:
            plt.legend(loc=self._config['legend'])

        if "colorbar" in self._config and self._config['colorbar']:
            plt.colorbar()

        return has_at_least_one_plot

    def save(self, file_name):
        plt.tight_layout()
        plt.savefig(file_name, dpi=90)


class LinePlot:
    def __init__(self, config, columns):
        self._config = config
        self._columns = columns

    def plot(self):
        xs = None
        ys = None

        if "x" in self._config and self._config['x'] in self._columns:
            xs = self._columns[self._config['x']].get_values()
        else:
            return False

        if "y" in self._config and self._config['y'] in self._columns:
            ys = self._columns[self._config['y']].get_values()
        else:
            return False

        if len(xs) <= 0 or len(ys) <= 0:
            return False

        kwargs = {}

        if 'kwargs' in self._config:
            kwargs = self._config['kwargs']

        plt.plot(xs, ys, **kwargs)

        return True


class ScatterPlot:
    def __init__(self, config, columns):
        self._config = config
        self._columns = columns

    def plot(self):
        xs = None
        ys = None
        colors = None

        if "x" in self._config and self._config['x'] in self._columns:
            xs = self._columns[self._config['x']].get_values()
        else:
            return False

        if "y" in self._config and self._config['y'] in self._columns:
            ys = self._columns[self._config['y']].get_values()
        else:
            return False

        if "color" in self._config and self._config['color'] in self._columns:
            colors = self._columns[self._config['color']].get_values()

        if len(xs) <= 0 or len(ys) <= 0:
            return False

        kwargs = {}

        if 'kwargs' in self._config:
            kwargs = self._config['kwargs']

        if colors is not None:
            kwargs['c'] = colors

        plt.scatter(xs, ys, **kwargs)

        return True


class Histogram:
    def __init__(self, config, columns):
        self._config = config
        self._columns = columns

    def plot(self):
        xs = None

        if "x" in self._config and self._config['x'] in self._columns:
            xs = self._columns[self._config['x']].get_values()
        else:
            return False

        if len(xs) <= 0:
            return False

        kwargs = {}
        bins = 10

        if 'kwargs' in self._config:
            kwargs = self._config['kwargs']

        if 'bins' in self._config:
            bins = self._config['bins']

        plt.hist(xs, bins, **kwargs)

        return True


class MatplotlibPlotterPlugin(AbstractExtractionPlugin):

    def __init__(self, configuration, logger, resource_directory):
        super(MatplotlibPlotterPlugin, self).__init__(configuration, logger, resource_directory)

    def check_topics(self, topics):
        return True

    def get_plugin_meta_data(self):
        return {
            'name': 'Matplotlib Plotter',
            'version': '0.0.1'
        }

    def get_default_configuration(self):
        return {
        }

    def extract(self, bag_file, topics, tmp_dir, output_dir, product_factory):

        data_columns_config = self.config("data")
        data_columns = []  # Need this to preserve the order
        data_columns_dict = {}
        topic_filter = {}

        # Setup the configuration
        self._logger.info("Time series columns:")
        for column_config in data_columns_config:

            column_type = column_config['type']

            column = None
            if column_type == "rostime":
                column = RostimeColumn(column_config)
            elif column_type == "raw":
                column = RawColumn(column_config)
            else:
                self._logger.warning("Unknown column type '%s'" % column_type)

            if column_type is None:
                continue

            if column.get_topic_name() != "":
                if column.get_topic_name() not in topics:
                    self._logger.warning("Configured data topic '%s' is not in matched topic list!" % column.get_topic_name())
                else:
                    # Remap the topic to the correct one
                    column.set_topic_name(topics[column.get_topic_name()])

            topic = column.get_topic_name()
            data_columns_dict[column.get_name()] = column
            data_columns.append(column)
            self._logger.info("%s -> %s" % (column.get_name(), topic))

            if topic not in topic_filter:
                topic_filter[topic] = []
            topic_filter[topic].append(column)


        # Fill the columns
        rosbag_length = 0
        with rosbag.Bag(bag_file, "r") as bag:
            bag_topics = list(topic_filter.keys())
            info = bag.get_type_and_topic_info(topic_filters=bag_topics)
            rosbag_length = bag.get_end_time() - bag.get_start_time()

            for topic in bag_topics:
                if not topic in info.topics:
                    self._logger.warning("Topic %s is not in the bag!" % topic)

            for topic, msg, t in bag.read_messages(topics=bag_topics):
                for column in topic_filter[topic]:
                    column.message(t, topic, msg)

        # Post process the columns
        for column in data_columns:
            column.post_process(data_columns_dict)

        # Plot the plots
        figures = self.config('figures')
        images = []
        for figure_key in figures:
            figure_config = figures[figure_key]
            figure = Figure(figure_config, data_columns_dict)

            if figure.plot(bag_length=rosbag_length):
                file_name = safe_file_name("fig_" + figure_key) + ".png"
                figure.save(output_dir + "/" + file_name)
                images.append((figure_key, file_name))
            else:
                self._logger.info("Plot '%s' has no plots, skipping save" % figure_key)

        if len(images) > 0:
            product = product_factory.new() # type: Product
            product.set_type("images")
            product.set_title("Plots")
            product.set_topics(topics)

            data = {
                'version': 1
            }

            product.set_data(data)

            for image in images:
                product.add_file(image[0], image[1], "image/png")

            return [product]
        else:
            return []

plugin = MatplotlibPlotterPlugin
