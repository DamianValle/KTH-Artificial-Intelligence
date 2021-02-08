Artificial Intelligence DD2424

Fishing derby: Hidden Markov Models
===

# Objective
The objective of this assignment is to implement Hidden Markov Models (HMM) in order to guess the type of fishes present in the sea.

The solution should be efficient, with a time limit per cycle of 5 seconds. 
The graphical interface spends 0.5 seconds per cycle and waits for player's response if the solution takes longer time.

# Given code
The skeleton provided includes an implementation of the KTH Fishing Derby.
The file player.py is provided, and it is necessary to complete it to solve the game. 

# Instructions
Program a solution in the file player.py by implementing the provided methods.
It is possible to submit the solution in different files if in the end player.py imports them without errors.

# Installation
The code runs in Python 3.6.

You should start with a clean virtual environment and install the requirements for the code to run.

In UNIX, in the skeleton directory, run:

```
$ sudo pip install virtualenvwrapper
$ . /usr/local/bin/virtualenvwrapper.sh
$ mkvirtualenv -p /usr/bin/python3.6 fishingderby
(fishingderby) $ pip install -r requirements.txt
```

In Windows, in the skeleton directory, run:

```
$ pip install virtualenvwrapper-win
```

And then close and open a new terminal.

```
$ mkvirtualenv -p C:\Users\<YourWindowsUser>\AppData\Local\Programs\Python\Python36\bin\python.exe fishingderby
(fishingderby) $ pip install -r requirements_win.txt
```

To run the GUI, in the skeleton's directory, run in the terminal:

```
(fishingderby) $ python main.py < sequences.json
```

# Note

Kattis uses PyPy compiler to run the solutions, which is different from the standard CPython that is used to run this skeleton, 
which unfortunately cannot be run with PyPy. 

You should expect that pure python code might run significantly faster on Kattis than code that uses numpy 
(which does not get compiled well with PyPy).
