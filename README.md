# TheWikiGameAI

A bot to play The Wiki Game (www.thewikigame.com) using Selenium and a Sentence Transformer based ranker.

## Getting Started

Make sure python 3.8 or higher is installed, create a virtual environment (advisable) and run:

`pip install -r requirements.txt`

Additionally, if you want to use the iddfs strategy, you need to import Wikipedia reference data into a Postgres database.
See https://github.com/colinschepers/wikipedia2pg to do so.

## Running the application

You can start the application using the script `run.py` in the root folder. 
Provide the strategy as parameter, possible strategies are:

- depth_first
- america_first
- mcts
- iddfs

Example:
``
python run.py depth_first
``