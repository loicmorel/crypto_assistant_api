## Context

[PPT Project link](https://www.dropbox.com/s/7oqlknt9iaku6dw/LeWagon-pitch-deck_v5.pptx?dl=0)

[Miro Architecture board](https://miro.com/app/board/uXjVODfwoRg=/?share_link_id=766671325540)

[Trello Tasks follow-up](https://trello.com/invite/b/EhHUxGbL/f390f26395ea05627748dcf8ceb297db/project-tasks)

Welcome to our Le Wagon bootcamp project: **a smart and friendly spot crypto portfolio digital assistant**
The goal of this project is to leverage our knoledge on machine learning and deep learning to create a strategic model that succeed to over-perform the BUY&HOLD strategy.
- Recurring analysis of coins in our portfolio
- Change dynamically the ponderation of the assets in the portfolio (every minutes/hours/days…)
- Bring new highly potential assets to mitigate the risk with a balanced the portfolio

The financial services industry becomes the perfect playing field for machine learning technologies. We dedicate to develop applications of deep learning in finance, study the causal relationship between the data, and make progress on related computer science theory.
Candlestick pattern recognition is an indicator that traders often judge with news, fundamentals, and technical indicators. However, even today, most traders decide by using their vision and experience. [ref](https://jfin-swufe.springeropen.com/articles/10.1186/s40854-020-00187-0)

👉 **We do not invest any money here... this project is a study without initial investement and based on historical data. Our metrics are based on performance values across a period of time that we will simulate based on real data**

The input for the user's portfolio have two modes:
- custom: custom portfolio where the user provides the portfolio ponderation.
- guided: the model identify the best assets and allocation across current avalable coins

The output for the user have two modes:
- prediction: the model provide the best predition current for assets allocation based on historical data analysis.
- backtesting: the model is tested across a window period of time (from start-ts to end-ts)

**So what can we do?**

We can try to developp our model by leveraging the ohlcv data and identify paterns to detect trends reversal. Some direction to look at:
- Encoding candlesticks as images for pattern classification using CNN to detect trends reversal
- Analyse correlations between tokens to keep your risk low with a balanced portfolio
- Analyse historical data and identify paterns to find the next crypto gem
- Improve ohlcv initial data by adding some basics technical analysis, market cap, interest rates, crypto Fear & Greed Index, google trend, ...
- Crypto is driven by the community. Not earnings reports, management, or borders. Improve the model by incorporate some Sentiment analysis from Twitter
- ...

**Related studies:**
- [Financial Vision](https://github.com/pecu/FinancialVision)
- [Advanced candlesticks for machine learning (i): tick bars](https://towardsdatascience.com/advanced-candlesticks-for-machine-learning-i-tick-bars-a8b93728b4c5)
- [Financial Vision Based Reinforcement Learning Trading Strategy](https://arxiv.org/pdf/2202.04115.pdf)

## Setup

Setup a new environement:
```bash
pyenv install 3.8.12
pyenv virtualenv 3.8.12 crypto_assistant
pyenv activate crypto_assistant
pyenv versions
```

Install project package:
```bash
git clone https://github.com/loicmorel/crypto_assistant
cd crypto_assistant/
```

Install requirements:
```bash
make install_requirements
```

Copy the default-config.yml to config.yml
```bash
cp conf/default_config.yml conf/config.yml
```
🚨 and adjust those parameters:
- profile_config:
  - pseudo: name
  - email: xxx@xxx.xxx
- exchanges:
  - binance:
    - enabled: false
    - commission_buy: x.xx
    - commission_sell: x.xx
    - public_key: 'XXX'
    - secret_key: 'XXX'

Install the package as a shortcut (dev)
```bash
pip install -e .
```

Make commands:
```bash
# activate crypto_assistant virtual environment
pyenv activate crypto_assistant

# install requirements (select the good one)
make install_requirements_amd64
make install_requirements_for_macosm1

# Project usage
make set_google_credentials
make get_all_data
make run_notebook
make run_locally
make run_api

# Docker
make docker_build
make docker_run
```
