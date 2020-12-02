Emulica is a software library to build simulation models of production and logistic systems, with 
an accent on control system design. The goal is to create a a model of the physical system, to test the control (or supervision) system agains this model. If the emulated system is sufficiently detailed, the control system can indifferently be connected to the real or emulated system.

Tutorial and documentation can be found at
https://emulica.readthedocs.io/en/develop/


The dependencies have been reduced as much as possible; but there are still a number
of requirements to meet:
 - simpy, since its the discrete event sytem that is used to make simulations run
 - matplotlib if you want to plot results
 - twisted to run the emulation model as a server
 
