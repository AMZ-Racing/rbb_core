# Rosbag visualizations
This page describes how to configure the rosbag visualization system. To debug your configuration file it is best
that you install `rbbtools`, see [Installing rbbtools](installing-rbbtools.md)

## The configuration file

The automatic visualization of rosbags is all configured through one single yaml file. Below is an example of this
configuration file. The top contains some meta information. The most important are the extraction rules.

```
title: "Standard test"
# The combination of tag and rule name uniquely identifies your
# extraction products. So that if you rerun the visualization again
# old products can be replaced with new ones.
tag: "standard-test"
description: ""
author: ""

rules:
  rule1:
    plugin: "plugin.module.path"
    config:
      ...
    topic_matchers:
      - type: "rbb_tools.extraction.matchers.ExactMatchingRule"
        config: ...
      
  rule2:
    plugin: "plugin.module.path"
    config:
      ...
    topic_matchers:
      - type: "rbb_tools.extraction.matchers.ExactMatchingRule"
        config: ...
```

Each rule in the configuration file generates a number of *extraction products*, 
these can be videos, data files, picture or any other form of data. All rules are completely separated
and can easily be moved to other configuration files (they cannot depend on each other).

**NOTE** All paths to other files are relative to the location of the configuration file.
this allows easy packaging of a configuration file with the other files that belong to it. (e.g. .rviz files)

### The anatomy of an extraction rule

Extraction rules consist of:

1. A name for the rule (rule1 and rule2 in the example).
2. An extraction plugin and the configuration for this plugin
3. A list of topic matchers and the configuration for these matchers

The topic matchers are used to determine which rules can be used for a given rosbag. They also allow you
to use the same plugin configuration for different set of topics. For example if you record two cameras. You can
match each camera separately and remap them to a topic called `/image`. The plugin will then run twice, one time for
each camera.

### List of extraction plugins

We aim to keep this list up to date ;)

* [**Rviz recorder**](plugins/rviz-recorder.md) *(rbb_tools.plugins.rviz_recorder)* Does exactly what it says on the tin.
* [**Detailed topic info**](plugins/detailed-topic-info.md) *(rbb_tools.plugins.detailed_topic_info)* Draws an image with the publishing intensity of each topic.
* [**Video extractor**](plugins/video-extractor.md) *(rbb_tools.plugins.video_extractor)* Creates a video from a image topic.
* [**Time series**](plugins/time-series.md) *(rbb_tools.plugins.time_series)* Transforms topics into a csv file for plotting.
* [**Matplotlib plotter**](plugins/matplotlib-plotter.md) *(rbb_tools.plugins.matplotlib_plotter)* Plots using matplotlib and saves the plots as pngs.

### List of topic matchers

We aim to keep this list up to date ;)

* **Exact Matching** *(rbb_tools.extraction.matchers.ExactMatchingRule)* Matches exact topic names with possibly exact message types.
* **Match All** *(rbb_tools.extraction.matchers.AllTopicsMatchingRule)* Passes on all topics in the bag directly to plugin.

## Testing a configuration

The configuration can be tested by **running in an empty directory**:

`rbbtools extract PATH_TO_CONFIGURATION_FILE PATH_TO_ROSBAG`

If you only want to test a specific rule you can **run in an empty directory**:

`rbbtools extract --rules RULE_NAME PATH_TO_CONFIGURATION_FILE PATH_TO_ROSBAG`

In both cases the output will be written to the current directory.


If you only want to check if the topics are matched to rules correctly you can run:

`rbbtools extract --dry-run PATH_TO_CONFIGURATION_FILE PATH_TO_ROSBAG`
