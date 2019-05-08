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

import datetime
import numpy as np
import os

import cv2
import rosbag
from cv_bridge import CvBridge

from rbb_tools.common.shell import Command
from rbb_tools.extraction.extractor import AbstractExtractionPlugin
from rbb_tools.extraction.registry import Product


# https://stackoverflow.com/questions/40895785/using-opencv-to-overlay-transparent-image-onto-another-image
def blend_transparent(face_img, overlay_t_img):
    # Split out the transparency mask from the colour info
    overlay_img = overlay_t_img[:,:,:3] # Grab the BRG planes
    overlay_mask = overlay_t_img[:,:,3:]  # And the alpha plane

    # Again calculate the inverse mask
    background_mask = 255 - overlay_mask

    # Turn the masks into three channel, so we can use them as weights
    overlay_mask = cv2.cvtColor(overlay_mask, cv2.COLOR_GRAY2BGR)
    background_mask = cv2.cvtColor(background_mask, cv2.COLOR_GRAY2BGR)

    # Create a masked out face image, and masked out overlay
    # We convert the images to floating point in range 0.0 - 1.0
    face_part = (face_img * (1 / 255.0)) * (background_mask * (1 / 255.0))
    overlay_part = (overlay_img * (1 / 255.0)) * (overlay_mask * (1 / 255.0))

    # And finally just add them together, and rescale it back to an 8bit integer image
    return np.uint8(cv2.addWeighted(face_part, 255.0, overlay_part, 255.0, 0.0))


class VideoExtractorPlugin(AbstractExtractionPlugin):

    def __init__(self, configuration, logger, resource_directory):
        super(VideoExtractorPlugin, self).__init__(configuration, logger, resource_directory)

    def get_plugin_meta_data(self):
        return {
            'name': 'Video Extractor',
            'version': '0.0.1'
        }

    def get_default_configuration(self):
        return {

        }

    def check_topics(self, topics):
        if topics.has_key('/image'):
            return True
        else:
            return False

    @staticmethod
    def write_text(cv_img, text, x, y):
        cv2.putText(cv_img, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, .5, (0,0,0), thickness=2)
        cv2.putText(cv_img, text, (x, y), cv2.FONT_HERSHEY_DUPLEX, .5, (255,255,255), thickness=1)

    def extract(self, bag_file, topics, tmp_dir, output_dir, product_factory):
        tmp_video_file = tmp_dir + "/output.avi"
        video_file = output_dir + "/output.mp4"

        if os.path.exists(tmp_video_file):
            os.remove(tmp_video_file)

        frame_rate = self.config('frame_rate')
        frame_height = self.config('frame_height')
        frame_width = self.config('frame_width')

        # TODO: Include fingerprints
        name = os.path.basename(bag_file)
        generation_time = str(datetime.datetime.today())

        logo = None
        overlay = None
        if self.config('logo'):
            logo_file = self._resource_directory + "/" + self.config('logo')
            logo = cv2.imread(logo_file, cv2.IMREAD_UNCHANGED)
            logo_height, logo_width = logo.shape[:2]
            overlay = np.zeros((frame_height, frame_width, 4), dtype="uint8")
            overlay[self.config('logo_y'):self.config('logo_y') + logo_height,
            self.config('logo_x'):self.config('logo_x') + logo_width] = logo

        bridge = CvBridge()

        #fourcc = cv2.cv.CV_FOURCC(*'XVID')
        fourcc = cv2.VideoWriter_fourcc(*'X264')
        video_writer = cv2.VideoWriter(tmp_video_file, fourcc, frame_rate, (frame_width, frame_height))
        with rosbag.Bag(bag_file, "r") as bag:
            info = bag.get_type_and_topic_info(topic_filters=[topics['/image']])
            src_number_of_frames = info.topics[topics['/image']].message_count
            msg_type_name = info.topics[topics['/image']].msg_type

            bag_start = bag.get_start_time()
            t_frame_one = 0
            t_offset = 0
            frame_counter = 0
            for topic, msg, t in bag.read_messages(topics=[topics['/image']]):
                frame_counter += 1

                if t_frame_one == 0:
                    t_frame_one = t
                    t_offset = t.to_sec() - bag_start;

                cv_img = None
                if msg_type_name == "sensor_msgs/CompressedImage":
                    str_msg = msg.data
                    buf = np.ndarray(shape=(1, len(str_msg)),
                                      dtype=np.uint8, buffer=msg.data)
                    cv_img = cv2.imdecode(buf, cv2.IMREAD_COLOR)
                else:
                    cv_img = bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

                height, width = cv_img.shape[:2]

                if frame_counter % (frame_rate * 5) == 0:
                    self._logger.info("%f%%" % (float(frame_counter) / float(src_number_of_frames) * 100.0))

                frame_text = name + " | " + generation_time
                self.write_text(cv_img, frame_text, self.config('text_x'), self.config('text_y'))

                frame_time_topic = "%07.3f +%.3f | %s" % (t.to_sec() - t_frame_one.to_sec(), t_offset, topics['/image'])
                self.write_text(cv_img, frame_time_topic, 10, frame_height - 10)

                # cv2.imshow('image', cv_img)
                # cv2.waitKey(0)

                if overlay is None:
                    video_writer.write(cv_img)
                else:
                    video_writer.write(blend_transparent(cv_img, overlay))

        video_writer.release()

        self._logger.info("Starting transcode to web friendly format...")

        # Transcode video for web usage (opencv does not like h.264, so we use ffmpeg again)
        ffmpeg_cmd = "ffmpeg -i %s -movflags +faststart %s" % (tmp_video_file, video_file)
        ffmpeg = Command(ffmpeg_cmd)
        ffmpeg.run()
        ffmpeg.join()

        if os.path.exists(tmp_video_file):
            os.remove(tmp_video_file)

        # Reverse topics
        product_topics = {}
        for k in topics: product_topics[topics[k]] = k

        # Register the product
        product = product_factory.new() # type: Product
        product.set_type("video")
        product.set_title("Raw Camera")
        product.set_topics(product_topics)
        product.add_file("video.mp4", "output.mp4", mime="video/mp4")

        return [product]


plugin = VideoExtractorPlugin
