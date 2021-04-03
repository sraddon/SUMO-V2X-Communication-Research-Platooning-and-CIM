from scenario_manager import runScenario, SCENARIO_NUMBER_CONFIGS, SCENARIO_LOCATION_CONFIG

import sys
import logging

numOfSteps = None
mapName = None
scenarioNum = None

# Check if we've passed any arguments on the command line

if len(sys.argv) > 1:
    logging.info("Found arguments %s passed in", sys.argv)
    mapName = sys.argv[1]
    scenarioNum = int(sys.argv[2])
    if sys.argv[3]:
        numOfSteps = int(sys.argv[3])
        
if not mapName:
    mapName = input("Please enter map name, available maps are: %s: " % ", ".join( SCENARIO_LOCATION_CONFIG.keys()))
if not scenarioNum:
    scenarioNum = int(input("Please enter scenario number, available numbers are: %s: " % ", ".join( str(n) for n in SCENARIO_NUMBER_CONFIGS.keys())))

if numOfSteps:
    runScenario(mapName, scenarioNum, numOfSteps)
runScenario(mapName, scenarioNum)