from sumolib import checkBinary
import traci


class SimulationManager():

    def __init__(self):
        self.stoppedCarsByLane = dict()
        self.activePlatoons = dict()
        self.laneNodeConnections = dict()
        for lane in traci.lane.getIDList():
            self.laneNodeConnections[lane] = traci.lane.getLinkNumber(lane)

    def createPlatoon(self, vehicleIDs):
        # A function to create a platoon of vehicles
        # out of a given list of vehicles
        for vehicle in vehicleIDs:
            traci.vehicle.setTau(vehicle, 0)
            traci.vehicle.setSpeedFactor(vehicle, 1)
            traci.vehicle.setMinGap(vehicle, 1)
            traci.vehicle.setImperfection(vehicle, 0)

    def disbandPlatoon(self, vehicleIDs):
        # A function to remove a list of vehicles from their respective platoon
        for vehicle in vehicleIDs:
            traci.vehicle.setTau(vehicle, 1)
            traci.vehicle.setSpeedFactor(vehicle, 0.9)
            traci.vehicle.setMinGap(vehicle, 2.5)
            traci.vehicle.setImperfection(vehicle, 0.5)

    def handleSimulationStep(self):
        # Handles a single step of the simulation
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
                for lane in [l for l in self.stoppedCarsByLane.keys() if (l not in processedLanes and self.laneNodeConnections[l] > 1)]:
                    if vehicleID in self.stoppedCarsByLane[lane]:
                        self.createPlatoon(self.stoppedCarsByLane[lane])
                        processedLanes.add(lane)
                        self.stoppedCarsByLane[lane].remove(vehicleID)


# Check SUMO has been set up properly
sumoBinary = checkBinary("sumo-gui")

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
