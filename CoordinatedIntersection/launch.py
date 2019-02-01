from sumolib import checkBinary
import traci


class SimulationManager():

    def __init__(self):
        self.stoppedCarsByLane = dict()
        self.activePlatoons = dict()

    def createPlatoon(self, vehicleIDs):
        for vehicle in vehicleIDs:
            traci.vehicle.setTau(vehicle, 0)
            traci.vehicle.setSpeedDev(vehicle, 0)
            traci.vehicle.setMinGap(vehicle, 1)
            traci.vehicle.setImperfection(vehicle, 0)

    def disbandPlatoon(self, vehicleIDs):
        for vehicle in vehicleIDs:
            traci.vehicle.setTau(vehicle, 1)
            traci.vehicle.setSpeedDev(vehicle, 0.1)
            traci.vehicle.setMinGap(vehicle, 2.5)
            traci.vehicle.setImperfection(vehicle, 0.5)

    def handleSimulationStep(self):
        idList = traci.vehicle.getIDList()
        processedLanes = set()
        for vehicleID in idList:
            vehicleSpeed = traci.vehicle.getSpeed(vehicleID)
            vehicleLane = traci.vehicle.getLaneID(vehicleID)

            if vehicleSpeed == 0:
                if vehicleLane in self.stoppedCarsByLane:
                    self.stoppedCarsByLane[vehicleLane].add(vehicleID)
                else:
                    self.stoppedCarsByLane[vehicleLane] = set([vehicleID, ])
            else:
                # If a lane with stopped cars has not already
                # been checked and it is of an appropriate type
                for lane in [l for l in self.stoppedCarsByLane.keys() if (l not in processedLanes and "Traffic" in l)]:
                    if vehicleID in self.stoppedCarsByLane[lane]:
                        self.createPlatoon(self.stoppedCarsByLane[lane])
                        processedLanes.add(lane)
                        self.stoppedCarsByLane[lane].remove(vehicleID)


# Check SUMO has been set up properly
sumoBinary = checkBinary("sumo-gui")
sumoCmd = [sumoBinary, "-c",
           "CoordIntersection.sumocfg", "--step-length", "0.1"]

# Start Simulation and step through
traci.start(sumoCmd)
step = 0
manager = SimulationManager()
while step < 50000:
    manager.handleSimulationStep()
    traci.simulationStep()
    step += 1

traci.close()
