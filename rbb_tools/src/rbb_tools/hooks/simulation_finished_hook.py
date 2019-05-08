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
import logging
import base64
import json
from rbb_client.rest import RESTClientObject


class SimulationFinishedHook():
    _hooks = []

    @classmethod
    def trigger(cls, api, sim, manifest):
        for hook in cls._hooks:
            hook.trigger(api, sim, manifest)

    @classmethod
    def register(cls):
        if cls != SimulationFinishedHook:
            if not hasattr(cls, "_registered"):
                cls._registered = True
                cls._hooks.append(cls)


class NotifyJenkinsOnSimulationFinished(SimulationFinishedHook):

    @classmethod
    def trigger(cls, api, sim, manifest):
        if sim.on_complete_action and "jenkins_callback" in sim.on_complete_action:
            logging.info("Submitting simulation status to Jenkins...")
            jc = sim.on_complete_action['jenkins_callback']

            config_registry = api.get_configuration_key("secret.jenkins")
            if not 'secret' in config_registry or not 'jenkins' in config_registry['secret']:
                logging.error("Missing Jenkins credentials in system configuration")
                return

            user = config_registry['secret']['jenkins']['user']
            password = config_registry['secret']['jenkins']['password']

            if not user or not password:
                logging.error("!!! Cannot callback to jenkins, server username and/or password not set!")
                return

            cls.report(api, sim, manifest, jc, user, password)


    @classmethod
    def report(cls, api, sim, manifest, jc, user, password):
        user_and_password = user + ":" + password
        basic_auth_header = base64.b64encode(user_and_password)
        client = RESTClientObject()

        crumb_url = jc[
                        'jenkins_url'] + "crumbIssuer/api/xml?xpath=concat(//crumbRequestField,\":\",//crumb)"
        response = client.request("GET", crumb_url,
                                  headers={"Authorization": "Basic %s" % basic_auth_header})
        crumb = response.data.split(":")
        logging.info("Got jenkins crumb '%s'" % repr(crumb))

        json_parameter = {
            "parameter": {
                "name": "Successful",
                "value": True if manifest['pass'] else False
            }
        }
        parameters = {
            'name': 'Successful',
            'proceed': 'Proceed',
            'json': json.dumps(json_parameter)
        }

        response = client.request("POST", jc['input_url'],
                                  post_params=parameters,
                                  headers={
                                      crumb[0]: crumb[1],
                                      "Authorization": "Basic %s" % basic_auth_header,
                                      'Content-Type': 'application/x-www-form-urlencoded'
                                  })

        logging.info("Jenkins server responded with code: %d" % response.status)


NotifyJenkinsOnSimulationFinished.register()


