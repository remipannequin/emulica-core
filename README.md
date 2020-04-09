Emulica is a software library to build simulation models of production and logistic systems, with 
an accent on control system design. 

To sum the approach up, it offers modules that
emulate the behaviour of physical elements, but remove any kind of control from these
elements, so that the control designer is able to face a realistic chalenge. An emulation
model can mimic a real system, and the control system can indifferently be connected
to the real or emulated system.

Tutorial and documentation can be found at
https://emulica.readthedocs.io/en/develop/


The dependencies have been reduced as much as possible; but there are still a number
of requirements to meet:
 - simpy (of course)
 - matplotlib with to get plotting
 - twisted to run the emulation model as a server



