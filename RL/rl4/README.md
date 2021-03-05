# REINFORCEMENT LEARNING ASSIGNMENT

## Scenario: 
A sea full of jellyfishes, one king fish and one diver.

## Objective:
Capture the king fish. The diver has to reach the king fish while avoiding the jellyfishes. 

## Specifications:
The assignment consists on finding the best policy (Q-learning e-greedy) to reach the king fish 
without touching the jellyfishes. Touching a jellyfish means a discount in the reward while reaching the 
king fish means a positive reward (usually).
The possible actions of the diver are: up, down, left, right.

# Instalation

##  Ubuntu 16.04 / 18.04 / 20.04

### Requirements:
- Anaconda 3 (recommended), you could also use virtualenv as done in the previous assignments.
- a python 3.6/3.7 blank environment (minimum)


##  Instructions with anaconda (from .yml file) [recommended]

0) Open a terminal and unzip the exercise 
1) Move to the repository path in your system 
```
cd [path_to_the_repository]
```
2) Install the anaconda environment from the yml file 
```
conda env create -f rl.yml
```
3) Load the anaconda environment
```
conda activate rl
```


##  Create the environment with anaconda and a  blank python 3.7 env (from requirements.txt)

0) Open a terminal and unzip the exercise 
1) Move to the repository path in your system 
```
cd [path_to_the_repository]
```
2) Create a python 3.7 blank environment (example in anaconda)
```
conda create -n rl python=3.7
```
3) Load the python environment
```
conda activate rl
```
4) Install the required packages thorough pip
```
pip install -r requirements.txt
```

##  Instructions with virtualenv (from requirements.txt)

0) Open a terminal and unzip the exercise 
1) Move to the repository path in your system 
```
cd [path_to_the_repository]
```
2) Install virtualenv and load your python virtual environment
```
sudo pip install virtualenvwrapper
. /usr/local/bin/virtualenvwrapper.sh
mkvirtualenv -p /usr/bin/python3.6 fishingderby
```
3) Install the required packages thorough pip
```
pip install -r requirements.txt
```

## Windows 10
1) Follow the instructions for installing on Ubuntu (or see Tip below)
2) Install additional requirements
```
pip install kivy.deps.sdl2 kivy.deps.glew --extra-index-url https://kivy.org/downloads/packages/simple/
```

## Windows 10 with virtualenv

In Windows, in the skeleton directory, start a terminal in administrator mode (right click) and run:

```
 >pip install virtualenvwrapper-win
```

Close the terminal, and open a new one in the same directory.
The following command will make a new virtual environment for your project. Replace <path/to/python3.6> with 
the path to your python.exe file. Could be something like C:\Users\<Your Windows User>\AppData\Local\Programs\Python\Python36\python.exe
```
 >mkvirtualenv -p {path to Python Interpreter} fishingderby
```
The next command will install the requirements in the virtual environment. Run it in the same terminal as above. 
```
 (fishingderby) >pip install -r requirements_win.txt
```

Now you have a virtual environment with all you need to run the project. To access the virtual environment anytime, 
open a terminal in the directory of the project and type:
```
 >workon fishingderby
``` 

### Tip
Visual Studio allows for creating virtual environments in which you can easily install the requirements.txt. Use the project properties to set your script arguments.

## To run
1) To run your agent once you completed the exercises, execute the following.
```
python main.py settings.yml
```
It will run the agent with the settings in settings.yml

## Assignment:
In order to accomplish the assignment, the student needs to complete the script player.py and other .yml files. 
The student will be able to test locally their agents by running the default settings.yml file.
Most information of the environment is unknown during testing and evaluation. 
To solve the game the student has to program 2 stages:

1) Exploration: Using Q-learning With e-greedy, the student will explore the environment by sending messages to the game
with the following structure:

    msg = {"action": action_str, "exploration": True}
    
    Where: 
    - action can  be: "up", "down", "left" or "right".
    - exploration: Always True during the exploration stage.
    
    After sending this message, the game will respond with a dictionary-message with the next position of the diver and 
    the reward of the action.
    
2) Playing: After finding a policy (reaching a convergence criteria), you can send a message to the game with the following structure;

    msg = {"policy": policy, "exploration": False}
    
    Where:
    - policy: is a dictionary whose keys are the position (x, y) of the map and the values are the actions
     "up", "down", "left" or "right".
    - exploration: Always False for this stage, so the game will understand you want to play and will start moving the diver in the interface. 
