import datetime
import logging
import subprocess
import time

import target

class Screenshotter(object):
    """
    Implements all screenshot-related logic.
    """

    def __init__(self, config):
        self.config = config
        self.screenshot_filenames = []

    def take_screenshots(self):
        """
        Runs through the process of taking all screenshots.
        """
        images = []
        for image in self.config.get('images'):
            current_target = target.Target(self.config, image)
            try:
                print type(current_target), type(current_target.get('url'))
                self.depict(
                    current_target.get('url'),
                    current_target.get('selector', 'body'),
                    current_target.get('local_filepath'),
                    # Depict's delay argument is defined in milliseconds
                    str(int(current_target.get('page_load_delay', 2)) * 1000)
                )
                images.append({
                    'slug': current_target.get('slug'),
                    'filepath': current_target.get('filepath'),
                    'local_filepath': current_target.get('local_filepath'),
                    'aws_filepath': current_target.get('aws_filepath'),
                    'aws_latest_filepath': current_target.get('aws_latest_filepath'),
                })
            except RuntimeError as e:
                logging.error(e)
        return images

    def depict(self, url, selector, destination, page_load_delay):
        """
        Runs the command-line utility `depict`.
        """
        args = ['depict', url, destination, '-s', selector,
                '--delay', page_load_delay]

        override_css_file = self.config.get('override_css_file')
        if override_css_file:
            args = args + ['--css', override_css_file]

        if self.config.get('wait_for_js_signal', False):
            args = args + ['--call-phantom']

        logging.info('Running shell command: %s' % (args))

        p = subprocess.Popen(args, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE)

        # Wait at most `failure_timeout` seconds for the process to finish
        failure_timeout = self.config.get('failure_timeout', 30)
        deadline = time.time() + failure_timeout
        while time.time() < deadline and p.poll() == None:
            time.sleep(1)

        # If the failure timeout is more than 0 and the process still hasn't
        # finished, terminate it.
        if failure_timeout > 0 and p.poll() == None:
            p.terminate()
            raise RuntimeError('Terminated shell command: %s' % (args))

        out, err = p.communicate()
        if p.returncode != 0:
            raise RuntimeError('depict error: %s' % err)
