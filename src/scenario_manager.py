import logging
import traci
from simulationmanager import SimulationManager
from simlib import setUpSimulation

from collections import namedtuple

scenarioNumberConfigTuple = namedtuple("scenarioNumberConfig", "nameModifier enableManager enablePlatoons enableCoordination enableZipping")
scenarioMapConfigTuple = namedtuple("scenarioMapConfig", "mapName defaultTrafficScale")

DEFAULT_OUTPUT_SAVE_LOCATION = "output/additional.xml"

SCENARIO_NUMBER_CONFIGS = {
    1 : scenarioNumberConfigTuple("",        False, False, False, False),
    2 : scenarioNumberConfigTuple("",        True, True, False, False),
    3 : scenarioNumberConfigTuple("_no_TLS", True, True, True, False),
    4 : scenarioNumberConfigTuple("_no_TLS", True, True, True, True),
}
SCENARIO_LOCATION_CONFIG = {
    "Blackwell"    : scenarioMapConfigTuple("BlackwellTunnelNorthApproach", 1),
    "Intersection" : scenarioMapConfigTuple("NormalIntersection", 3),
    "Roundabout"   : scenarioMapConfigTuple("A13NorthCircularRoundabout", 1),
}

def runScenario(mapName, scenarioNum, numOfSteps=5000):
    """ Runs a given scenario using the given scenario name and number.
    """
    logging.info("Starting scenario for (name: %s | number: %s)")
    # Get config information
    scenarioLocationConfig = SCENARIO_LOCATION_CONFIG.get(mapName)
    scenarioNumberConfig = SCENARIO_NUMBER_CONFIGS.get(scenarioNum)
    if not scenarioLocationConfig:
        raise ValueError("Could not find a scenario for the given name %s, available names: %s" % (mapName, SCENARIO_LOCATION_CONFIG.keys()))
    if not scenarioNumberConfig:
        raise ValueError("Could not find a scenario for the given number %s, available numbers: %s" % (scenarioNum, SCENARIO_NUMBER_CONFIGS.keys()))

    baseScenarioName = scenarioLocationConfig.mapName
    logging.info("Got map name %s and number config %s", baseScenarioName, "|".join([" %s: %s " % (key, value) for key, value in scenarioNumberConfig._asdict().items()]))
    mapName = baseScenarioName + scenarioNumberConfig.nameModifier

    # Get location of config files and place to store the output
    currPath = __file__.replace("\\", "/")
    mainProjectDirectory = "/".join(currPath.split("/")[:currPath.split("/").index("src")])
    mapLocation = "{0}/maps/{1}/{1}.sumocfg".format(mainProjectDirectory, mapName)
    outputFileLocation = "{0}/{1}".format(mainProjectDirectory, DEFAULT_OUTPUT_SAVE_LOCATION)

    setUpSimulation(mapLocation, scenarioLocationConfig.defaultTrafficScale, outputFileLocation)
    step = 0
    manager = SimulationManager(scenarioNumberConfig.enablePlatoons, scenarioNumberConfig.enableCoordination, scenarioNumberConfig.enableZipping) if scenarioNumberConfig.enableManager else None
    while step < numOfSteps:
        if manager:
            manager.handleSimulationStep()
        traci.simulationStep()
        step += 1

    # If we have a manager, try to get some stats
    if manager:
        logging.info("Max number of stopped cars: %s", manager.maxStoppedVehicles)
        logging.info("Average length of platoon: %s", manager.getAverageLengthOfAllPlatoons())
    traci.close()