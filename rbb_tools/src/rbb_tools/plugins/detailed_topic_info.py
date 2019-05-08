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

import matplotlib.cm as cmx
import matplotlib.colors as colors
import matplotlib.pyplot as plt
import numpy as np

import cv2
import rosbag

from rbb_tools.extraction.extractor import AbstractExtractionPlugin
from rbb_tools.extraction.registry import Product


class DetailedTopicInfoPlugin(AbstractExtractionPlugin):

    def __init__(self, configuration, logger, resource_directory):
        super(DetailedTopicInfoPlugin, self).__init__(configuration, logger, resource_directory)

    def check_topics(self, topics):
        return True

    def get_plugin_meta_data(self):
        return {
            'name': 'Detailed Topic Info',
            'version': '0.0.1'
        }

    def get_default_configuration(self):
        return {
            'timeline_height': 50,
            'timeline_vertical_margin': 10,
            'timeline_left_margin': 10,
            'timeline_right_margin': 10,
            'timeline_max_before': 30,
            'topic_name_left_margin': 20,
            'topic_name_right_margin': 20,
            'scales': [0.05, 0.25]
        }

    def generate_timeline(self, delta_t, name, bag_file, topics, output_dir):
        # Setting point
        timeline_height = self.config('timeline_height')
        timeline_vertical_margin = self.config('timeline_vertical_margin')
        timeline_left_margin = self.config('timeline_left_margin')
        timeline_right_margin = self.config('timeline_right_margin')
        timeline_max_before = self.config('timeline_max_before')
        delta_t_per_pixel = delta_t
        topic_name_left_margin = self.config('topic_name_left_margin')
        topic_name_right_margin = self.config('topic_name_right_margin')

        # Calculated dimensions
        height = 0
        width = 0
        timeline_width = 0
        timeline = {}

        # Determine the width of the name block
        topic_name_block_width = 0
        for original_topic in topics:
            size = cv2.getTextSize(topics[original_topic], cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
            if size[0][0] > topic_name_block_width:
                topic_name_block_width = size[0][0]

        timeline_left_margin += topic_name_block_width + topic_name_left_margin + topic_name_right_margin

        # Create the timeline
        self._logger.info("Reading bag...")
        with rosbag.Bag(bag_file, 'r') as bag:
            t_bag_start = bag.get_start_time()

            timeline_width = int(np.trunc((bag.get_end_time() - t_bag_start) / delta_t_per_pixel) + 1)

            for original_topic in topics:
                timeline[original_topic] = np.zeros(timeline_width, np.uint16)

            msg_generator = bag.read_messages(topics=topics.keys())
            end_of_bag = False
            while not end_of_bag:
                try:
                    topic, msg, t = next(msg_generator)
                    timeline[topic][int(np.trunc((t.to_sec() - t_bag_start) / delta_t_per_pixel))] += 1
                except StopIteration:
                    end_of_bag = True

        height = len(topics) * (timeline_height + timeline_vertical_margin) + timeline_vertical_margin
        width = timeline_width + timeline_left_margin + timeline_right_margin
        img = np.full((height, width, 3), 255, np.uint8)

        topic_offset_x = timeline_left_margin
        topic_offset_y = timeline_vertical_margin

        list_max_msgs_per_dt = []
        for original_topic in topics:
            list_max_msgs_per_dt.append(np.max(timeline[original_topic]))

        # Color mapping
        color_map = plt.get_cmap('viridis')
        normalizer = colors.Normalize(vmin=0, vmax=max(list_max_msgs_per_dt))
        color_mapping = cmx.ScalarMappable(norm=normalizer, cmap=color_map)

        self._logger.info("Drawing image...")
        for original_topic in sorted(topics.keys()):
            max_msgs_per_dt = np.max(timeline[original_topic])
            self._logger.info(" - %s (peak: %d)" % (original_topic, max_msgs_per_dt))

            # Bottom top line
            cv2.line(img,
                     (topic_offset_x, topic_offset_y + timeline_height + 1),
                     (topic_offset_x + timeline_width, topic_offset_y + timeline_height + 1),
                     (30, 30, 30), 1)

            cv2.line(img,
                     (topic_offset_x - timeline_max_before, topic_offset_y),
                     (topic_offset_x + timeline_width, topic_offset_y),
                     (200, 200, 200), 1)

            for i in range(timeline_width):
                msgs = timeline[original_topic][i]

                if msgs > 0:
                    line_height = float(msgs) / (float(max_msgs_per_dt) / float(timeline_height))
                    color = color_mapping.to_rgba(msgs)
                    cv2.line(img,
                             (topic_offset_x + i, topic_offset_y + timeline_height - int(line_height)),
                             (topic_offset_x + i, topic_offset_y + timeline_height),
                             # OpenCV takes colors as BGR
                             (color[2] * 255, color[1] * 255, color[0] * 255), 1)

            # Write max
            font = cv2.FONT_HERSHEY_SIMPLEX
            cv2.putText(img, '%d' % max_msgs_per_dt,
                        (topic_offset_x - timeline_max_before, topic_offset_y + 15),
                        font, 0.3, (0, 0, 0), 1, cv2.LINE_AA)

            # Write topic name
            cv2.putText(img, topics[original_topic],
                        (topic_name_left_margin, topic_offset_y + 15),
                        font, 0.5, (0, 0, 0), 1, cv2.LINE_AA)

            topic_offset_y += timeline_height + timeline_vertical_margin

        cv2.imwrite(output_dir + '/%s.png' % name, img)

        topic_name_full_width = topic_name_block_width + topic_name_left_margin + topic_name_right_margin
        cv2.imwrite(output_dir + '/%s_topics.png' % name, img[:, 0:topic_name_full_width])
        cv2.imwrite(output_dir + '/%s_timeline.png' % name, img[:, topic_name_full_width:width])

        return topic_name_full_width

    def extract(self, bag_file, topics, tmp_dir, output_dir, product_factory):

        scales = self.config('scales')
        product = product_factory.new() # type: Product
        product.set_type("detailed-topic-info")
        product.set_title("Detailed Topic Info")
        product.set_topics(topics)

        data = {
            'version': 1,
            'scales': {}
        }

        for scale in scales:
            scale_name = "%f" % scale
            topic_name_full_width = self.generate_timeline(scale, scale_name, bag_file, topics, output_dir)

            # Topics are the same for every scale
            product.add_file("topics.png", scale_name + "_topics.png", "image/png", overwrite_if_exists=True)
            product.add_file(scale_name + ".png", scale_name + "_timeline.png", "image/png")

            data['scales'][scale_name] = {
                'scale': scale,
                'topics': "topics.png",
                'timeline': scale_name + ".png",
                'topic_name_width': topic_name_full_width
            }

        product.set_data(data)

        return [product]


plugin = DetailedTopicInfoPlugin
