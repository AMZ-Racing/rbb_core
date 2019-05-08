#!/usr/bin/env python
import yaml
import os

print('Simulator example script')

example_output = {
    'title': 'Autonomous simulation',
    'repetitions': {
        '1': {
            'bag': None,
            'pass': True,
            'duration': 10.0,
            'results': {
                'some-interesting-value': 123.0
            }
        },
        '2': {
            'bag': None,
            'pass': False,
            'duration': 10.0,
            'results': {
                'some-interesting-value': -123.0
            }
        }
    }
}

with open(os.environ.get('SIMULATOR_OUTPUT') + '/output.yaml', 'w') as outfile:
    yaml.dump(example_output, outfile, default_flow_style=False)

exit(0)
