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
import os
import time

import yaml

from rbb_tools.common.shell import CommandGroup
from rbb_tools.extraction.extractor import AbstractExtractionPlugin
from rbb_tools.extraction.registry import Product


class RvizRecorderPlugin(AbstractExtractionPlugin):

    def __init__(self, configuration, logger, resource_directory):
        super(RvizRecorderPlugin, self).__init__(configuration, logger, resource_directory)

    def check_topics(self, topics):
        return True

    def get_plugin_meta_data(self):
        return {
            'name': 'RViz Recorder',
            'version': '0.0.1'
        }

    def get_default_configuration(self):
        return {
            'height': 1080,
            'width': 1920,
            'margin_left': -20,
            'margin_right': -20,
            'rewrite_rviz_file': True,
            'headless': 'auto',
            'color_depth': 24,
            'title': 'RViz Recording'
        }

    def _rewrite_rviz_file(self, rviz_file, tmp_dir):
        data = None
        with open(rviz_file, 'r') as stream:
            try:
                data = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                self._logger.warning("Cannot rewrite malformed rviz file: %s" % str(exc))
                return rviz_file

        data['Window Geometry']['Height'] = self.config('height')
        data['Window Geometry']['Width'] = self.config('width') - \
                                           self.config('margin_left') - self.config('margin_right')
        data['Window Geometry']['Y'] = 0
        data['Window Geometry']['X'] = self.config('margin_left')
        data['Window Geometry']['Hide Left Dock'] = True
        data['Window Geometry']['Hide Right Dock'] = True
        data['Window Geometry']['Selection']['collapsed'] = True
        data['Window Geometry']['Time']['collapsed'] = False
        data['Window Geometry']['Tool Properties']['collapsed'] = True
        data['Window Geometry']['Views']['collapsed'] = True
        data['Window Geometry']['Displays']['collapsed'] = True

        rewritten_rviz_file = tmp_dir + "/rviz.rviz"
        with open(rewritten_rviz_file, 'w') as outfile:
            yaml.safe_dump(data, outfile, default_flow_style=False)

        return rewritten_rviz_file

    def extract(self, bag_file, topics, tmp_dir, output_dir, product_factory):
        video_file = output_dir + "/output.mp4"
        xdisplay_id = 99

        logo_file = self._resource_directory + "/" + self._configuration['logo']
        font_file = self._resource_directory + "/" + self._configuration['font']

        rviz_file = self._resource_directory + "/" + self._configuration['rviz_file']
        if self.config("rewrite_rviz_file"):
            rviz_file = self._rewrite_rviz_file(rviz_file, tmp_dir)


        # TODO: Output a temporary rviz file that rewrites the configuration to collapse all panels and spawn window at 0,0

        if os.path.exists(video_file):
            return False

        # TODO: Include fingerprints
        name = os.path.basename(bag_file)
        rviz_name = os.path.basename(self._configuration['rviz_file'])
        text = name + " | " + rviz_name + " | " + str(datetime.datetime.today())

        self._logger.info("Video id: " + text)

        xephyr_size = "%dx%d" % (self.config('width'), self.config('height'))
        xephyr_cmd = "Xephyr -ac -nocursor -screen %s -br -reset -terminate :%d" % (xephyr_size, xdisplay_id)

        xvfb_size = "%dx%dx%d" % (self.config('width'), self.config('height'), self.config('color_depth'))
        xvfb_cmd = "Xvfb :%d -screen 0 %s" % (xdisplay_id, xvfb_size)

        roscore_cmd = "roscore"
        rosbag_player_cmd = "rosbag play --clock --hz 1000 -q %s" % (bag_file)

        rviz_splash_option = ""
        if self.config('splash_screen'):
            rviz_splash_option = " -s %s" % (self._resource_directory + "/" + self.config('splash_screen'))

        if os.environ.get('DISPLAY') is not None:
            # We assume hardware acceleration is available and run through VGL
            rviz_vgl_cmd = "vglrun -- rviz -d %s%s" % (rviz_file, rviz_splash_option) #DISPAY
        else:
            # We assume hardware acceleration is NOT available and run directly on Xephyr/Xvfb
            # software acceleration (mesa with llvm) should be isntalled
            rviz_vgl_cmd = "rviz -d %s%s" % (rviz_file, rviz_splash_option) #DISPAY

        ffmpeg_grab_size = "%dx%d" % (self.config('width'), self.config('height'))
        ffmpeg_cmd = "ffmpeg -loglevel warning -video_size %s -framerate 25 -f x11grab -i :%d.0+0,0" \
                     " -i %s -filter_complex \"overlay=%d:%d,drawtext=text=\\'%s\\':x=%d:y=%d:fontfile=%s:fontsize=16:fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2\" " \
                     "-movflags +faststart %s" % (ffmpeg_grab_size, xdisplay_id, logo_file, self._configuration['logo_x'],self._configuration['logo_y'], text, self._configuration['text_x'], self._configuration['text_y'], font_file, output_dir + "/output.mp4")

        self._logger.info(ffmpeg_cmd)

        ##################
        # Run the commands
        ##################
        cmd_group = CommandGroup()
        try:
            roscore = cmd_group.Command(roscore_cmd)

            if os.environ.get('RBB_HEADLESS') == "force":
                # Force headless in server environments
                headless = True
            else:
                headless = self.config('headless')

                if headless == 'auto':
                    headless = os.environ.get('RBB_HEADLESS') == 1

            if headless:
                print ("Running in headless mode! (Xvfb)")
                framebuffer = cmd_group.Command(xvfb_cmd)
            else:
                framebuffer = cmd_group.Command(xephyr_cmd)

            rviz = cmd_group.Command(rviz_vgl_cmd, {'DISPLAY': ":%d.0" % (xdisplay_id)})
            ffmpeg = cmd_group.Command(ffmpeg_cmd)
            rosbag_player = cmd_group.Command(rosbag_player_cmd)
            move_mouse = cmd_group.Command("xdotool mousemove %d %d" % (self.config('width'), self.config('height')), {'DISPLAY': ":%d.0" % (xdisplay_id)})
            rosparam_sim_time = cmd_group.Command("rosparam set use_sim_time true")

            roscore.run()
            framebuffer.run()

            # Make sure they don't directly crash
            time.sleep(1)

            if roscore.is_running() and framebuffer.is_running():
                self._logger.info("Roscore&Xephyr up!")
                rviz.run()
                ffmpeg.run()

                time.sleep(0.5)
                if rviz.is_running() and ffmpeg.is_running():
                    move_mouse.run()
                    rosparam_sim_time.run()
                    self._logger.info("Rviz&ffmpeg up!")
                    rosbag_player.run()

                    while rosbag_player.is_running() and rviz.is_running():
                        time.sleep(1)

                    ffmpeg.send_sigint()
                    ffmpeg.join()

            else:
                self._logger.failure("Couldnt start roscore or xephyr")
        finally:
            cmd_group.ensure_terminated()

        # Register the product
        product = product_factory.new() # type: Product
        product.set_type("video")
        product.set_title(self.config('title'))
        product.set_topics(topics)
        product.add_file("video.mp4", "output.mp4", mime="video/mp4")

        return [product]


plugin = RvizRecorderPlugin
