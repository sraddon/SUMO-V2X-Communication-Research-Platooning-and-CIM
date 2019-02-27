import logging
import traci
from sumolib import checkBinary

def flatten(l):
    # A basic function to flatten a list
    return [item for sublist in l for item in sublist]

def setUpSimulation(configFile):
    # Check SUMO has been set up properly
    sumoBinary = checkBinary("sumo-gui")

    # Set up logger
    logging.basicConfig(format='%(asctime)s %(message)s')
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    # Start Simulation and step through
    traci.start([sumoBinary, "-c", configFile, "--step-length", "0.1", "--collision.action", "none", "--start", "--quit-on-end"])