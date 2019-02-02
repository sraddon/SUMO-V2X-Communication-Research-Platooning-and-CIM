import logging
import os
import sys
import traci
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from sumolib import checkBinary
from src.simulationmanager import SimulationManager


# Check SUMO has been set up properly
sumoBinary = checkBinary("sumo-gui")

# Set up logger
logging.basicConfig(format='%(asctime)s %(message)s')
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Start Simulation and step through
traci.start([sumoBinary, "-c", "CoordIntersection.sumocfg",
             "--step-length", "0.1"])
step = 0
manager = SimulationManager()
while step < 5000:
    manager.handleSimulationStep()
    traci.simulationStep()
    step += 1

traci.close()
