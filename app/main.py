
"""Main app module
"""

import sys
import logging
from typing import Any
from app.config import Config
from app.logs import Logging
from app.exchanges.binance import Binance
from app.data_collection.datamgt import collect_historical_data

# check min. python version
if sys.version_info < (3, 8):
    sys.exit("CryptoPortfolioAssistant requires Python version >= 3.8")


def main():
    """Initializes the application and start the trading loop
    return: None
    """

    global syslog
    return_code: Any = 0

    try:
        pass
        # load settings and create the config object
        config = Config()

        print('project', config.project)
        print('settings', config.settings)
        print('portfolio_config', config.portfolio_config)
        print('profile_config', config.profile_config)
        print('reporting', config.reporting)
        print('exchanges', config.exchanges)
        print('web_scraping', config.web_scraping)
        print('logging', config.logging)

        # instantiate logger
        Logging(config)
        syslog = logging.getLogger('system')

        # TODO: define analysis timestamp

        # TODO: data collection

        # TODO: data analysis and prediction

        # TODO: update portfolio ratios

        # TODO: generate reporting (analysis, performances, pf ratios)

    except SystemExit as err:  # pragma: no cover
        return_code = err
    except KeyboardInterrupt:
        syslog.info('SIGINT received, aborting ...')
        return_code = 0
    except OSError as err:
        syslog.error("OS error: {0}".format(err))
        return_code = -1
    except Exception as err:
        exceptName = type(err).__name__  # returns the name of the exception
        syslog.exception(f'Fatal exception! {exceptName}')
        return_code = -1
    finally:
        syslog.info(f'thx, see you later.. ,exit code {return_code}')
        sys.exit(return_code)


if __name__ == "__main__":
    main()
