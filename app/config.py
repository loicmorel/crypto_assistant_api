
"""Load configuration from environment
"""

import os
import yaml

class Config():
    """Parses the environment configuration to create the config objects.
    """

    def __init__(self):
        """Initializes the Configuration class
        """

        with open('./conf/default_config.yml', 'r') as config_file:
            default_config = yaml.load(config_file, Loader=yaml.FullLoader)

        if os.path.isfile('./conf/config.yml'):
            with open('./conf/config.yml', 'r') as config_file:
                user_config = yaml.load(config_file, Loader=yaml.FullLoader)
        else:
            user_config = dict()

        if 'settings' in user_config:
            self.settings = {**default_config['settings'], **user_config['settings']}
        else:
            self.settings = default_config['settings']

        if 'portfolio_config' in user_config:
            self.portfolio_config = {**default_config['portfolio_config'], **user_config['portfolio_config']}
        else:
            self.portfolio_config = default_config['portfolio_config']

        if 'profile_config' in user_config:
            self.profile_config = {**default_config['profile_config'], **user_config['profile_config']}
        else:
            self.profile_config = default_config['profile_config']

        if 'reporting' in user_config:
            self.reporting = {**default_config['reporting'], **user_config['reporting']}
        else:
            self.reporting = default_config['reporting']

        if 'exchanges' in user_config:
            self.exchanges = {**default_config['exchanges'], **user_config['exchanges']}
        else:
            self.exchanges = default_config['exchanges']

        if 'web_scraping' in user_config:
            self.web_scraping = {**default_config['web_scraping'], **user_config['web_scraping']}
        else:
            self.web_scraping = default_config['web_scraping']

        if 'logging' in user_config:
            self.logging = {**default_config['logging'], **user_config['logging']}
        else:
            self.logging = default_config['logging']

        if 'project' in user_config:
            self.project = {**default_config['project'], **user_config['project']}
        else:
            self.project = default_config['project']

    def get_project_config(self, key=None):
        if key == None:
            return self.project
        else:
            # print(key.lower())
            return self.project.get(key.lower(), "config not found...")

if __name__ == "__main__":
    import sys

    config = Config()
    args = sys.argv[1:]

    if len(args) == 1:
        print(config.get_project_config(args[0]))
    elif len(args) > 1:
        print('Error: too much arguments...')
        exit(1)
    else:
        print(config.get_project_config())
