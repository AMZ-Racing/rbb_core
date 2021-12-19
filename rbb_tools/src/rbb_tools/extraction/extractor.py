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
import importlib
import os
import shutil
import traceback
import zipfile

import rosbag
import yaml

from rbb_tools.common.logging import Logger
from rbb_tools.common.shell import Command
from rbb_tools.extraction.registry import ProductFactory


class AbstractExtractionPlugin(object):

    def __init__(self, configuration, logger, resource_directory):
        self._configuration = configuration
        self._logger = logger
        self._resource_directory = resource_directory

    def check_topics(self, topics):
        raise NotImplementedError

    def extract(self, bag_file, topics, tmp_dir, output_dir, product_factory):
        raise NotImplementedError

    def get_default_configuration(self):
        return {}

    def config(self, key):
        keys = key.split(".")

        # Value is in the user supplied configuration?
        node = self._configuration
        if node:
            user_supplied = True
            for k in keys:
                if k in node:
                    node = node[k]
                else:
                    user_supplied = False
                    break

            if user_supplied:
                return node

        # Value is in the default configuration?
        node = self.get_default_configuration()
        if node:
            default_supplied = True
            for k in keys:
                if k in node:
                    node = node[k]
                else:
                    default_supplied = False
                    break

            if default_supplied:
                return node

        return None

    def get_plugin_meta_data(self):
        raise NotImplementedError

    def get_plugin_name_version(self):
        return "%s v%s" % (self.get_plugin_meta_data()['name'], self.get_plugin_meta_data()['version'])


class AbstractMatchingRule(object):

    def __init__(self, configuration, logger):
        pass

    def match(self, topics_and_types):
        raise NotImplementedError("Abstract")

    def get_mappings(self):
        raise NotImplementedError("Abstract")

    def to_string(self):
        return "AbstractMatchingRule"


class ExtractionProductGenerator:

    def __init__(self, plugin, rule, topics):
        self._plugin = plugin
        self._rule = rule
        self._topics = topics

    def get_topic_mapping(self):
        return self._topics

    def get_rule(self):
        return self._rule

    def get_plugin(self):
        return self._plugin

    def generate(self, output_folder, temporary_folder):
        pass


class ExtractionRule:

    def __init__(self, name, matching_rules, plugin):
        self._name = name
        self._matching_rules = matching_rules
        self._plugin = plugin

    def get_name(self):
        return self._name

    def get_rules(self):
        return self._matching_rules

    def get_plugin(self):
        return self._plugin

    def get_product_generators(self, topics_and_types):
        products_generators = []

        for rule in self._matching_rules:
            if rule.match(topics_and_types):
                for mapping in rule.get_mappings():
                    products_generators.append(ExtractionProductGenerator(
                        self._plugin,
                        self._name,
                        mapping
                    ))

        return products_generators


class Extractor(object):

    def __init__(self,
                 configuration_file,
                 bag,
                 temp_dir="",
                 output_dir="",
                 dry_run=False,
                 overwrite=False,
                 rules=[],
                 logger=Logger()):

        if not os.path.exists(configuration_file):
            raise RuntimeError("Configuration '%s' does not exist" % (configuration_file))

        if not os.path.isfile(bag):
            raise RuntimeError("Rosbag file '%s' does not exist" % (bag))

        self._configuration = {}

        self._extraction_rules = []
        self._extraction_product_generators = []
        self._products = []
        self._configuration_file = configuration_file
        self._resource_directory = ""
        self._bag = os.path.abspath(bag)
        self._only_rules = rules

        self._topics_and_types = {}
        self._topic_tuples = {}
        self._msg_type_hashes = {}
        self._bag_size = 0
        self._bag_message_count = 0
        self._bag_start = 0
        self._bag_end = 0
        self._data_bag_start = 0
        self._data_bag_end = 0
        self._bag_duration = 0
        self._data_bag_duration = 0
        self._errors = []

        if not temp_dir:
            self._temp_dir = os.getcwd() + "/temp"
        else:
            self._temp_dir = temp_dir

        if not output_dir:
            self._output_dir = os.getcwd() + "/output_" + os.path.basename(bag)
        else:
            self._output_dir = output_dir

        self._dry_run = dry_run
        self._overwrite = overwrite
        self._logger = logger  # type: Logger

        self._create_dirs()
        self._load_configuration()

    def _match(self):
        generator_counter = 1
        self._logger.info("Products that can be generated:")
        for i in range(len(self._extraction_rules)):
            rule = self._extraction_rules[i]

            self._logger.info("- %s (%d/%d)" % (rule.get_name(), i+1, len(self._extraction_rules)))

            product_generators = rule.get_product_generators(self._topics_and_types)
            if len(product_generators) == 0:
                self._logger.info("     None")
            else:
                for product_generator in product_generators:
                    self._logger.info("  %d. %s" % (generator_counter, str(product_generator.get_topic_mapping())))
                    generator_counter += 1
                self._extraction_product_generators += product_generators

    def _generate(self):
        self._logger.info("Starting extraction of products...")
        extraction_id = 0
        for product_generator in self._extraction_product_generators:
            extraction_id += 1
            succeeded = True
            plugin_object = product_generator.get_plugin()
            product_directory = self._output_dir + "/" + str(extraction_id)

            self._logger.info("- Extracting product(s) %d/%d (%s)" % (extraction_id,
                                                       len(self._extraction_product_generators),
                                                       plugin_object.get_plugin_name_version()))

            # Ensure correct topics are matched
            if succeeded:
                if not plugin_object.check_topics(product_generator.get_topic_mapping()):
                    succeeded = False
                    self._logger.failure("  Invalid topic mapping")

            if succeeded:
                if os.path.exists(product_directory) and not self._overwrite:
                    succeeded = False
                    self._logger.failure("  Product directory already exists")

            if self._dry_run:
                self._logger.info("  SKIPPING (dry run)")
                continue

            # Generate product
            if succeeded:
                # Create output directory
                if self._overwrite and os.path.exists(product_directory):
                    shutil.rmtree(product_directory)

                if not os.path.exists(product_directory):
                    os.makedirs(product_directory)
                self._logger.debug("  output: %s" % (product_directory))

                try:
                    products = plugin_object.extract(
                        self._bag,
                        product_generator.get_topic_mapping(),
                        self._temp_dir,
                        product_directory,
                        ProductFactory(self._tag,
                                       product_generator.get_rule(),
                                       plugin_object.get_plugin_name_version(),
                                       product_directory))
                except Exception as e:
                    self._logger.failure("  EXCEPTION '%s'" % repr(e))
                    traceback.print_exc()
                    self._errors.append({
                        'type': 'exception',
                        'tag': self._tag,
                        'rule': product_generator.get_rule(),
                        'plugin': plugin_object.get_plugin_name_version(),
                        'message': traceback.format_exc()
                    })
                    products = None

                if isinstance(products, list):
                    succeeded = True
                    self._products.extend(products)
                    self._logger.info("Generated products:")
                    for p in products:
                        self._logger.info("  - %s: %s" % (p.get_type(), p.get_title()))
                else:
                    succeeded = False

            if succeeded:
                self._logger.info("  SUCCEEDED")
            else:
                self._logger.failure("  FAILED")

        self._products.extend(self._get_error_message_product())

    def _get_error_message_product(self):
        pf = ProductFactory(self._tag, "error-messages", "ATS Errors V1.0", "")
        p = pf.new()
        p.set_type("error-messages")
        p.set_title("Extraction Errors")
        p.set_topics([])
        p.set_data({'errors': self._errors})
        return [p]

    def write_manifest(self, path, server_data={}):
        products = []
        for p in self._products:
            products.append(p.to_dict())

        data = {
            'server_info': {
                'server_url': "",
                'store_name': "",
                'bag_name': "",
            } if not 'server_url' in server_data else server_data,
            'bag_info': {
                'size': 0,
                'start_time': 0,
                'end_time': 0,
                'data_start_time': 0,
                'data_end_time': 0,
                'duration': 0,
                'data_duration': 0,
                'messages': 0,
                'topics': []
            },
            'products': products
        }

        self._fill_manifest_bag_info(data)

        with open(path, 'w') as outfile:
            yaml.safe_dump(data, outfile, default_flow_style=False)

    def _fill_manifest_bag_info(self, data):
        topics = []
        for topic in self._topic_tuples:
            topic_data = {
                'name': topic,
                'msg_type': self._topic_tuples[topic].msg_type,
                'msg_count': self._topic_tuples[topic].message_count,
                'avg_frequency': self._topic_tuples[topic].frequency,
                'msg_type_hash': self._msg_type_hashes[self._topic_tuples[topic].msg_type],
                'msg_definition': ""
            }
            topics.append(topic_data)

        data['bag_info']['topics'] = topics
        data['bag_info']['size'] = self._bag_size
        data['bag_info']['start_time'] = datetime.datetime.fromtimestamp(self._bag_start)
        data['bag_info']['end_time'] = datetime.datetime.fromtimestamp(self._bag_end)
        data['bag_info']['data_start_time'] = datetime.datetime.fromtimestamp(self._bag_start)
        data['bag_info']['data_end_time'] = datetime.datetime.fromtimestamp(self._bag_end)
        data['bag_info']['duration'] = self._bag_duration
        data['bag_info']['data_duration'] = self._data_bag_duration
        data['bag_info']['messages'] = self._bag_message_count

    def _read_bag(self, reindex=True):
        self._topics_and_types = {}

        self._logger.debug("Topics in bag:")
        try:
            with rosbag.Bag(self._bag, 'r') as bag:
                info = bag.get_type_and_topic_info()
                for topic in info.topics:
                    self._logger.debug("- %s: %s" % (topic, info.topics[topic].msg_type))
                    self._topics_and_types[topic] = info.topics[topic].msg_type
                    self._topic_tuples[topic] = info.topics[topic]

                for msg_type in info.msg_types:
                    self._msg_type_hashes[msg_type] = info.msg_types[msg_type]

                self._bag_size = bag.size
                self._bag_message_count = bag.get_message_count()
                self._bag_start = bag.get_start_time()
                self._bag_end = bag.get_end_time()
                self._data_bag_start = bag.get_start_time()
                self._data_bag_end = bag.get_end_time()
                self._bag_duration = self._bag_end - self._bag_start
                self._data_bag_duration = self._data_bag_end - self._data_bag_start
        except rosbag.ROSBagUnindexedException:
            self._logger.warning("Bag is UNINDEXED!")

            if reindex:
                self._logger.info("Attempting bag reindexing using rosbag reindex.")
                reindex_command = Command("rosbag reindex '%s'" % self._bag, None, os.path.dirname(self._bag))
                reindex_command.run()
                if reindex_command.join() == 0:
                    self._logger.info("Bag reindexed!")
                    self._read_bag(reindex=False)
                else:
                    self._logger.failure("Reindex command failed!")


    def run(self, auto_write_manifest=True):
        self._logger.info("Starting extraction '%s' (%s)..." % (self._title, self._tag))
        self._logger.info("Reading bag metadata...")
        self._read_bag()
        self._match()
        self._generate()
        if auto_write_manifest:
            self.write_manifest(self._output_dir + "/manifest.yaml")

    def cleanup(self):
        if os.path.exists(self._temp_dir):
            shutil.rmtree(self._temp_dir)

    def _create_dirs(self):
        if not os.path.exists(self._temp_dir):
            os.makedirs(self._temp_dir)

        if not os.path.exists(self._temp_dir):
            raise RuntimeError("Cannot create temporary directory '%s'" % (self._temp_dir))

        if not os.path.exists(self._output_dir):
            os.makedirs(self._output_dir)

        if not os.path.exists(self._output_dir):
            raise RuntimeError("Cannot create output directory '%s'" % (self._output_dir))

    def _load_configuration(self):
        filename, file_extension = os.path.splitext(self._configuration_file)

        self._logger.debug("Loading configuration %s" % self._configuration_file)

        if file_extension == '.zip':
            self._resource_directory = self._temp_dir + "/config"
            self._logger.debug("Unpacking config archive in: %s" % self._resource_directory)

            if os.path.exists(self._resource_directory):
                shutil.rmtree(self._resource_directory)

            with zipfile.ZipFile(self._configuration_file, 'r') as config_zip:
                config_zip.extractall(self._resource_directory)
            self._configuration_file = self._resource_directory + "/config.yaml"

            if not os.path.isfile(self._configuration_file):
                raise RuntimeError("There is no 'config.yaml' in the provided config archive")
        else:
            self._resource_directory = os.path.dirname(os.path.realpath(self._configuration_file))

        self._logger.debug("Resource directory: %s" % self._resource_directory)

        with open(self._configuration_file, 'r') as stream:
            try:
                self._configuration = yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise RuntimeError("Invalid YAML in configuration file: %s" % str(exc))

        if not self._configuration:
            raise RuntimeError("Error loading configuration or empty configuration file")

        self._title = self._configuration['title']
        self._tag = self._configuration['tag']
        self._description = self._configuration['description']


        self._logger.info("Extraction rules:")
        self._load_rules_from_configuration()

    def _load_rules_from_configuration(self):
        for rule_name in self._configuration['rules']:
            # Only load the specified rules
            if len(self._only_rules) > 0 and not rule_name in self._only_rules:
                continue

            rule_config = self._configuration['rules'][rule_name]

            # Is the plugin available
            try:
                plugin = importlib.import_module(rule_config['plugin'])
            except ImportError as e:
                self._logger.debug("ImportError: %s" % str(e))
                raise RuntimeError("Cannot find plugin '%s' used by rule '%s'" % (rule_config['plugin'], rule_name))

            # Is the plugin correctly defined
            try:
                plugin_class = plugin.plugin
                if not issubclass(plugin_class, AbstractExtractionPlugin):
                    raise RuntimeError("Plugin '%s' is not a subclass of AbstractExtractionPlugin" % rule_config['plugin'])
            except NameError:
                raise RuntimeError("Plugin '%s' has no plugin class defined" % (rule_config['plugin']))

            plugin_object = plugin.plugin(rule_config['config'], self._logger, self._resource_directory)

            # Load the matchers
            matching_rules = []
            for matcher in rule_config['topic_matchers']:
                try:
                    module = str.join(".", matcher['type'].split(".")[:-1])
                    class_name = matcher['type'].split(".")[-1]
                    matcher_module = importlib.import_module(module)
                    matcher_class = getattr(matcher_module, class_name)
                    if not issubclass(matcher_class, AbstractMatchingRule):
                        raise RuntimeError(
                            "Matcher '%s' is not a subclass of AbstractMatchingRule" % matcher['type'])
                except ImportError as e:
                    self._logger.debug("ImportError: %s" % str(e))
                    raise RuntimeError("Cannot find module '%s' for matcher '%s'" % (module, matcher['type']))
                except AttributeError as e:
                    self._logger.debug("AttributeError: %s" % str(e))
                    raise RuntimeError("Module '%s' has no matcher '%s'" % (module, class_name))

                matcher_object = matcher_class(matcher['config'], self._logger)
                matching_rules.append(matcher_object)

            extraction_rule = ExtractionRule(rule_name, matching_rules, plugin_object)
            self._extraction_rules.append(extraction_rule)
            self._logger.info("%d. %s (%s)" %
                              (len(self._extraction_rules), rule_name, plugin_object.get_plugin_name_version()))
            for rule in matching_rules:
                self._logger.info("   - %s" % rule.to_string())
