import traci
import logging


class IntersectionController():

    def __init__(self, intersection, zip=True):
        self.name = intersection
        self.zip = zip
        lanes = traci.trafficlights.getControlledLanes(intersection)
        self.lanesServed = set(lanes)
        self.platoons = []
        self.gapAtJunction = 0.2

    def addPlatoon(self, platoon):
        """
        Adds a platoon to this intersection controller
        """
        self.platoons.append(platoon)

    def _getPlatoonLanePosition(self, platoon):
        """
        Gets a platoon's lane position in relation to this intersection
        (gives 0 if the platoon is on an edge not controlled by this controller)
        """
        if platoon.getLane() in self.lanesServed:
            return platoon.getLanePosition()
        return 0

    def findAndAddReleventPlatoons(self, platoons):
        """
        Finds platoons in the given list that can be managed by this controller, then
        adds them
        """
        def platoonPosition(platoon):
            return self._getPlatoonLanePosition(platoon)

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
        for v in platoon.getAllVehicles():
            traci.vehicle.setSpeedMode(v, 31)

    def updatePlatoonSpeed(self, platoon, reservedTime):
        """
        Takes a platoon and the time the junction has been reserved for and changes
        its speed accordingly.
        Returns the updated junction reservation time.
        """
        distanceToTravel = self._getPlatoonLanePosition(platoon)
        platoonCurrentSpeed = platoon.getCurrentSpeed()
        # If we are in the last 20 metres, we assume no more vehicles will join the platoon
        # and then set the speed to be constant. This is because if we did not speed tends
        # towards 0 (as the distance we give is to the junction and not to the end of the platoon's
        # route.
        if distanceToTravel > 20:
            speed = distanceToTravel / (reservedTime or 1)
            speed = max([speed, platoon.getAcceleration()])
            # If we're above the max speed, we use that instead
            if speed >= platoonCurrentSpeed:
                platoon.removeTargetSpeed()
            else:
                platoon.setTargetSpeed(speed)
        else:
            platoon.setTargetSpeed(platoon.getCurrentSpeed())

        # If this platoon is the first to post a reservation, the distance to the junction needs to be included
        if reservedTime == 0:
            lenThruJunc = self._getPlatoonLanePosition(platoon) + platoon.getLength()
        else:
            lenThruJunc = platoon.getLength()

        # Only add reservation time if the platoon is approaching the junction (and hasn't past it)
        # This deals with the case of one vehicle in the platoon having passed through but the others haven't.
        if platoon.getLane() in self.lanesServed:
            return self.gapAtJunction + reservedTime + (lenThruJunc / (platoonCurrentSpeed or 1))
        return 0

    def update(self):
        """
        Performs various functions to update the junction's state.
        1. Ensures that all vehicles being managed by the junction, have thier automatic
           stopping behaviour deactived (otherwise they are too cautious at the intersection)
        2. Removes platoons that are no longer in the sphere of influence of the function
        3. Updates the speed of all platoons being managed by the controller.

        """
        reservedTime = 0
        for p in self.platoons:
            for v in p.getAllVehicles():
                traci.vehicle.setSpeedMode(v, 0)
            # Do we need to remove any platoons from our control?
            if all([l not in self.lanesServed for l in p.getLanesOfAllVehicles()]):
                self.removePlatoon(p)
            # Update the speeds of the platoon
            else:
                reservedTime = self.updatePlatoonSpeed(p, reservedTime)
        self.logIntersectionStatus(reservedTime)

    def logIntersectionStatus(self, reservation=None):
        """
        A function that logs the status of this intersection.
        """
        if self.platoons:
            logging.info("------------%s Information------------", self.name)
            for p in self.platoons:
                logging.info("Platoon: %s, Target: %s, Current: %s ", p.getID(), p.getTargetSpeed(), p.getCurrentSpeed())
            if reservation:
                logging.info("Total time reserved: %s", reservation)