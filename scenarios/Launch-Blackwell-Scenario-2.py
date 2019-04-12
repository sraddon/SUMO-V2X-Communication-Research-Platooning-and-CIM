import os
import sys
import logging
import traci
sys.path.append(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
from src.simulationmanager import SimulationManager
from src.simlib import setUpSimulation

setUpSimulation("maps/BlackwellTunnelNorthApproach/BlackwellTunnelNorthApproach.sumocfg", 2)
step = 0
manager = SimulationManager(True, False)
maxNumAtTrafficLights = 0
while step < 5000:
    manager.handleSimulationStep()
    traci.simulationStep()
    step += 1

logging.info("Max number of stopped cars: %s", manager.maxStoppedVehicles)

traci.close()
