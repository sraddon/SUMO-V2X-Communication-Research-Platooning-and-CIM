import logging
import traci
from sumolib import checkBinary


# Check SUMO has been set up properly
sumoBinary = checkBinary("sumo-gui")

# Set up logger
logging.basicConfig(format='%(asctime)s %(message)s')
root = logging.getLogger()
root.setLevel(logging.DEBUG)

# Start Simulation and step through
traci.start([sumoBinary, "-c", "NormalIntersection.sumocfg",
             "--step-length", "0.1", "--start", "--quit-on-end"])
step = 0
while step < 5000:
    traci.simulationStep()
    step += 1

traci.close()
