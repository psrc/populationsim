PopulationSim
=============

[![Build Status](https://travis-ci.org/RSGInc/populationsim.svg?branch=master)](https://travis-ci.org/RSGInc/populationsim) [![Coverage Status](https://coveralls.io/repos/RSGInc/populationsim/badge.png?branch=master)](https://coveralls.io/r/RSGInc/populationsim?branch=master)


PopulationSim is an open platform for population synthesis.  It emerged
from Oregon DOT's desire to build a shared, open, platform that could be 
easily adapted for statewide, regional, and urban transportation planning 
needs.  PopulationSim is implemented in the 
[ActivitySim](https://github.com/activitysim/activitysim) framework. 

## Documentation

https://activitysim.github.io/populationsim/

## PSRC Implementation
To run populationsim for PSRC:
- follow general instructions at https://activitysim.github.io/populationsim/getting_started.html
- clone this repository and CD to ./psrc
- settings and controls yaml files are preset in psrc/configs
- change path lines at top of psrc/run_populationsim.py to local working directory (location of the population repo)
`activate popsim
python run_populationsim.py`

After the run is complete, an initial set of outputs is stored in the output folder. 
An addtional script *balance_pop.py* developed by PSRC will further align synthetic population to hit control targets. 
To run this script, update the paths (input_dir and output_dir) to the local directory output folder and run `python balance_pop.py`. The final, ajdusted output will be available in the output directory:
- adjusted_synthetic_households.csv
- adjusted_synthetic_persons.csv
- adjusted_seed_households.csv
- adjusted_seed_persons.csv 

These are the final synthetic population and household files, along with updated PUMS samples that reflected ammendments to the synthetic population records. More explanation of the balancing step is included in the header of the script. 

Final results for 2018 are stored at R:\e2projects_two\SyntheticPopulation_2018\FINAL_adjusted_outputs
