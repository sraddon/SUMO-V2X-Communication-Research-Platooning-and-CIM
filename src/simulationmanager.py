from intersectionController import IntersectionController
from platoon import Platoon
from vehicle import Vehicle
from simlib import flatten

import traci

class SimulationManager():

    def __init__(self, pCreation=True, iCoordination=True, iZipping=True, maxVehiclesPerPlatoon=0):
        self.intersections = []
        self.platoons = list()
        self.platoonCreation = pCreation
        self.vehicles = list()
        self.maxStoppedVehicles = dict()
        self.maxVehiclesPerPlatoon = maxVehiclesPerPlatoon
        if iCoordination:
            for intersection in traci.trafficlights.getIDList():
                controller = IntersectionController(intersection, iZipping)
                self.intersections.append(controller)

    def createPlatoon(self, vehicles):
        # Creates a platoon with the given vehicles
        platoon = Platoon(vehicles, maxVehicles=self.maxVehiclesPerPlatoon)
        self.platoons.append(platoon)

    def getActivePlatoons(self):
        # Gets all active platoons
        return [p for p in self.platoons if p.isActive()]

    def getAllVehiclesInPlatoons(self):
        # Gets all vehicles in every active platoon
        return flatten(p.getAllVehiclesByName() for p in self.getActivePlatoons())

    def getAverageLengthOfAllPlatoons(self):
        if self.platoons:
            count = 0
            length = len(self.platoons)
            for platoon in self.platoons:
                if platoon._disbandReason != "Merged" and platoon._disbandReason != "Reform required due to new leader":
                    count = count + platoon.getNumberOfVehicles()
                else:
                    length = length - 1
            return count/length

    def getPlatoonByLane(self, lane):
        # Gets platoons corresponding to a given lane
        return [p for p in self.getActivePlatoons() if lane == p.getLane()]

    def getPlatoonByVehicle(self, v):
        return [p for p in self.getActivePlatoons() if v in p.getAllVehiclesByName()]

    def getReleventPlatoon(self, vehicle):
        # Returns a single platoon that is most relevent to the given
        # vehicle by looking to see if the car in front is part of a platoon
        # It also checks that the platoon is heading in the right direction
        leadVeh = vehicle.getLeader()
        if leadVeh and leadVeh[1] < 10:
            possiblePlatoon = self.getPlatoonByVehicle(leadVeh[0])
            if possiblePlatoon:
                if possiblePlatoon[0].checkVehiclePathsConverge([vehicle]) and vehicle not in possiblePlatoon[0].getAllVehicles() and possiblePlatoon[0].canAddVehicles([vehicle]):
                    return possiblePlatoon[0]

    def handleSimulationStep(self):
        allVehicles = traci.vehicle.getIDList()
        # Check mark vehicles as in-active if they are outside the map
        stoppedCount = dict()
        for v in self.vehicles:
            if v.getName() not in allVehicles:
                v.setInActive()
            # Get information concerning the number of vehicles queueing on each lane
            if v.isActive() and v.getSpeed() == 0:
                lane = v.getEdge()
                if lane in stoppedCount:
                    stoppedCount[lane] = stoppedCount[lane] + 1
                else:
                    stoppedCount[lane] = 1

        # Gather statistics for amount of vehicles stopped per lane
        for lane in stoppedCount:
            if lane in self.maxStoppedVehicles:
                if stoppedCount[lane] > self.maxStoppedVehicles[lane]:
                    self.maxStoppedVehicles[lane] = stoppedCount[lane]
            else:
                self.maxStoppedVehicles[lane] = stoppedCount[lane]

        # Update all platoons active status
        for p in self.getActivePlatoons():
            p.updateIsActive()

        if self.platoonCreation:
            # See whether there are any vehicles that are not
            # in a platoon that should be in one
            vehiclesNotInPlatoons = [v for v in allVehicles if v not in self.getAllVehiclesInPlatoons()]

            for vehicleID in vehiclesNotInPlatoons:
                vehicle = Vehicle(vehicleID)
                self.vehicles.append(vehicle)
                vehicleLane = vehicle.getLane()
                # If we're not in a starting segment (speed starts as 0)
                possiblePlatoon = self.getReleventPlatoon(vehicle)
                if possiblePlatoon:
                    possiblePlatoon.addVehicle(vehicle)
                else:
                    self.createPlatoon([vehicle, ])

        # If we're doing intersection management, update each controller and add any new platoons into their
        # control
        if self.intersections:
            for inControl in self.intersections:
                inControl.removeIrreleventPlatoons()
                inControl.findAndAddReleventPlatoons(self.getActivePlatoons())
                inControl.update()

        if self.platoonCreation:
            # Handles a single step of the simulation
            # Update all active platoons in the scenario
            for platoon in self.getActivePlatoons():
                platoon.update()
                if platoon.canMerge() and platoon.isActive():
                    lead = platoon.getLeadVehicle().getLeader()
                    if lead:
                        leadPlatoon = self.getPlatoonByVehicle(lead[0])
                        if leadPlatoon and leadPlatoon[0].canAddVehicles(platoon._vehicles):
                            leadPlatoon[0].mergePlatoon(platoon)