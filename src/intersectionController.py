import traci
import logging
from src.simlib import flatten


class IntersectionController():

    def __init__(self, intersection, zip=True):
        self.name = intersection
        self.zip = zip
        lanes = traci.trafficlights.getControlledLanes(intersection)
        self.lanesServed = set(lanes)
        self.platoons = []

    def addPlatoon(self, platoon):
        """
        Adds a platoon to this intersection controller
        """
        self.platoons.append(platoon)

    def _getLanePosition(self, v):
        """
        Gets a platoon's lane position in relation to this intersection
        (gives 0 if the platoon is on an edge not controlled by this controller)
        """
        if v.isActive():
            if v.getLane() in self.lanesServed:
                return v.getLanePositionFromFront()
        return 0

    def findAndAddReleventPlatoons(self, platoons):
        """
        Finds platoons in the given list that can be managed by this controller, then
        adds them
        """
        def platoonPosition(platoon):
            return self._getLanePosition(platoon)

        platoons.sort(key=platoonPosition)
        for p in platoons:
            if p.getLane() in self.lanesServed and p not in self.platoons:
                self.addPlatoon(p)

    def removePlatoon(self, platoon):
        """
        Removes a platoon from this controller and then resets its behaviour to default
        """
        self.platoons.remove(platoon)
        # Resume normal speed behaviour
        platoon.removeTargetSpeed()
        platoon.setPlatoonSpeedMode(31)

    def getAllVehicles(self):
        def vehiclePosition(vehicle):
            return self._getLanePosition(vehicle)

        v = flatten([p.getAllVehicles() for p in self.platoons])
        v.sort(key=vehiclePosition)
        return v

    def getNewPlatoonSpeed(self, platoon, reservedTime):
        """
        Takes a platoon and the time the junction has been reserved for and changes
        its speed accordingly.
        Returns the updated junction reservation time.
        """
        distanceToTravel = self._getLanePosition(platoon)
        platoonCurrentSpeed = platoon.getSpeed()
        # If we are in the last 20 metres, we assume no more vehicles will join the platoon
        # and then set the speed to be constant. This is because if we did not speed tends
        # towards 0 (as the distance we give is to the junction and not to the end of the platoon's
        # route.
        if distanceToTravel > 20:
            platoon.setPlatoonSpeedMode(23)
            speed = distanceToTravel / (reservedTime or 1)
            speed = max([speed, platoon.getAcceleration()])
            # If we're above the max speed, we use that instead
            if speed >= platoonCurrentSpeed:
                speed = -1
        elif platoonCurrentSpeed == 0:
            speed = -1
        else:
            platoon.setPlatoonSpeedMode(22)
            speed = platoonCurrentSpeed
        return speed

    def getNewVehicleSpeed(self, vehicle, reservedTime):
        distanceToTravel = vehicle.getLanePositionFromFront()
        currentSpeed = vehicle.getSpeed()
        # If we are in the last 20 metres, we assume no more vehicles will join the platoon
        # and then set the speed to be constant. This is because if we did not speed tends
        # towards 0 (as the distance we give is to the junction and not to the end of the platoon's
        # route.
        if distanceToTravel > 20:
            vehicle.setSpeedMode(23)
            speed = distanceToTravel / (reservedTime or 1)
            speed = max([speed, vehicle.getAcceleration()])
            # If we're above the max speed, we use that instead
            if speed >= currentSpeed:
                speed = -1
        elif currentSpeed == 0:
            speed = -1
        else:
            vehicle.setSpeedMode(22)
            speed = currentSpeed
        return speed

    def calculateNewReservedTime(self, v, reservedTime):
        # If this platoon is the first to post a reservation, the distance to the junction needs to be included
        speed = v.getSpeed()
        if reservedTime == 0:
            lenThruJunc = self._getLanePosition(v) + v.getLength()
        else:
            lenThruJunc = v.getLength()
        return reservedTime + (lenThruJunc / (speed or 1))

    def update(self):
        """
        Performs various functions to update the junction's state.
        1. Ensures that all vehicles being managed by the junction, have thier automatic
           stopping behaviour deactived (otherwise they are too cautious at the intersection)
        2. Removes platoons that are no longer in the sphere of influence of the function
        3. Updates the speed of all platoons being managed by the controller.
        """
        if len(self.platoons) > 1:
            reservedTime = 0
            if self.zip:
                for p in self.platoons:
                    if all([l not in self.lanesServed for l in p.getLanesOfAllVehicles()]):
                        self.removePlatoon(p)
                    p._manualControl = True
                for v in self.getAllVehicles():
                    speed = self.getNewVehicleSpeed(v, reservedTime)
                    v.setSpeed(speed)
                    reservedTime = self.calculateNewReservedTime(v, reservedTime)

            for p in self.platoons:
                # Do we need to remove any platoons from our control?
                if all([l not in self.lanesServed for l in p.getLanesOfAllVehicles()]):
                    self.removePlatoon(p)
                # Update the speeds of the platoon if it has not passed the junction
                elif p.getLane() in self.lanesServed:
                    speed = self.getNewPlatoonSpeed(p, reservedTime)
                    if speed == -1:
                        p.removeTargetSpeed()
                    else:
                        p.setTargetSpeed(speed)
                    reservedTime = self.calculateNewReservedTime(p, reservedTime)

    def logIntersectionStatus(self, reservation=None):
        """
        A function that logs the status of this intersection.
        """
        if self.platoons:
            logging.info("------------%s Information------------", self.name)
            for p in self.platoons:
                logging.info("Platoon: %s, Target: %s, Current: %s ", p.getID(), p.getTargetSpeed(), p.getSpeed())
            if reservation:
                logging.info("Total time reserved: %s", reservation)