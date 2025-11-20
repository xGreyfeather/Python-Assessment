## Programmer Assessment Q4

This repository contains a broken web app built with Dash. Please follow the tasks below.

Tasks:
1. Clone this repo to your machine.
2. Fix missing dependencies and fill authors section in `pyproject.toml`.
3. Fix bugs prevent the app `main.py` from running.
4. Change port the app ruuning on to `10030`.
5. Commit you changes.
6. Update `README.md` with a instruction
   1. Assuming the user has a fresh minimum Linux installation with no python.
   2. Setup python and virtual environment for this app, remember to use the fixed `pyproject.toml`.
   3. How to run this app and how to access it without portforwarding.
7. Push all the changes to your own repository on Github, and provide a link to your own repo in your submission in the last.

Set Up Python:
   Run the following commands:
      sudo apt update
      sudo apt install -y python3 python3-venv python3-pip git

Clone the Respository:
   Run the following commands:
      git clone <YOUR_REPO_URL>.git
      d Assessment-debugging
Install Dependencies:
   Run the following command:
      pip install dash pandas numpy plotly

Run the Application:
   Run the following command:
      python main.py