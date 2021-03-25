# Distrib-ToyChord
Implementation of a simple P2P network following a simplified form of the Chord protocol for distributed hash-tables (DHTs).  
This is a required project for the Distributed System course taught at ECE school of the National Technical University of Athens (NTUA).    

## Install Dependencies  
To automatically install the needed dependencies run the following code:  
```
pip3 install -r requirements.txt
```
The code was tested on python versions 3.6.9, 3.6.12.  
## Folder Structure:
* source
  - data -> Data directory. Hosts testcases of write, read queries.  
  - lib.py -> General functions library.    
  - message.py -> Contains code for the message class.
  - node.py -> Contains code for the node class.  

* CLI
  - data -> Data directory. Hosts testcases of write, read queries as well as some of the simulation results.  
  - cli-client -> A [Click](https://click.palletsprojects.com/en/7.x/) based CLI for Chord.  
  - simulator.py -> The simulator class used by the CLI to produce the results found in the data folder.

* instance
  - config.py -> Default server configuration for normal nodes.    
  - configBOOTSTRAP.py -> Default server configuration for bootstrap node.    

## How to run the ToyChord server
To run ToyChord use the following code to export the variables needed for configuring the server:  
```
export FLASK_APP=Distrib-ToyChord/source/
export FLASK_ENV=development
export SET_PORT=[DESIRED_PORT]
```  
Depending on the node's desired mode (normal or bootstrap) run either one of the following commands respectively:  
```
export MODE_CONFIG=normal
```
or  
```
export MODE_CONFIG=boot
```  
Setting the PORT is optional as the default values can be found in the configuration files inside the instance folder.  
The Chord's protocol number of replicas and consistency protocol can be edited in the config.py, configBOOTSTRAP.py files found in the instance folder.    
Finally to get the server going, run the following commands from the directory directly above the ToyChord project:  
```
flask run [--port [DESIRED_PORT]] [--host [PRIVATE IP]]
```  
## Command Line Interface  
The Chord's node methods can be easily accessed via the CLI we developed.  
To run the CLI:  
```
python3 cli-client.py repl
```  
## Collaborators
- Dimitris Galanis ([Github](https://github.com/DominusTea)) [E-mail](mailto:el16088@mail.ntua.gr?subject=[GitHub]%20Distrib%20Project)  
- Ioanna Tasou ([Github](https://github.com/ioannatas)) [E-mail](mailto:el16055@mail.ntua.gr?subject=[GitHub]%20Distrib%20Project)  
- Danae Charitou ([Github](https://github.com/danae-charitou)) [E-mail](mailto:el16045@mail.ntua.gr?subject=[GitHub]%20Distrib%20Project)
