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

from rbb_tools.extraction.extractor import AbstractMatchingRule


class ExactMatchingRule(AbstractMatchingRule):

    def __init__(self, configuration, logger):
        super(ExactMatchingRule, self).__init__(configuration, logger)
        self._topics_and_types = configuration['topics']
        if 'remapping' in configuration:
            self._remapping = configuration['remapping']
        else:
            self._remapping = {}
        self._output = {}
        self._matched = False

    def match(self, topics_and_types):
        self._output = {}
        self._matched = False

        for topic, message_type in self._topics_and_types.iteritems():
            if not topics_and_types.has_key(topic):
                return False
            elif topics_and_types[topic] != message_type and message_type != "*":
                return False

            # Is a remapping defined?
            if self._remapping.has_key(topic):
                self._output[self._remapping[topic]] = topic
            else:
                self._output[topic] = topic

        self._matched = True
        return True

    def get_mappings(self):
        if self._matched:
            return [self._output]
        else:
            return []

    def to_string(self):
        topics = []
        for t in self._topics_and_types:
            if t in self._remapping:
                topics.append("%s (%s) -> %s" % (t, self._topics_and_types[t], self._remapping[t]))
            else:
                topics.append("%s (%s)" % (t, self._topics_and_types[t]))
        return "ExactMatchingRule [%s]" % str.join(", ", topics)


class AllTopicsMatchingRule(AbstractMatchingRule):

    def __init__(self, configuration, logger):
        super(AllTopicsMatchingRule, self).__init__(configuration, logger)
        self._matched = False
        self._output = {}

    def match(self, topics_and_types):
        self._output = {}
        self._matched = True

        for topic, message_type in topics_and_types.iteritems():
            self._output[topic] = topic

        self._matched = True
        return True

    def get_mappings(self):
        if self._matched:
            return [self._output]
        else:
            return []

    def to_string(self):
        return "AllTopicsMatchingRule"
