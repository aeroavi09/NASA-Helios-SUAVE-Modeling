# NASA-Helios-SUAVE-Modeling

The objective was to accurately model and predict high fidelity flight characteristics of a HALE (High Altitude Long Endurance) aircraft with the SUAVE network.

Utilized class based engineering and OpenVSP for validation.
Implemented a constant-speed 14-propeller model
Implemented a Solar energy network with a electric brushless motor configuration

<img src="Helios Plots/Helios Left Iso.png" width="75%" height="75%">
Performance plots can be found in Helios Plots folder

Flight plan: 50000ft cruise, descent to 25000ft at a constant speed

Measurements derived from NASA Facts Helios Prototype, Helios MIB

The Helios aircraft used the S6078 airfoil, but it's polars and dimensions were not easily found, so the SD6080, which is similar in performance. 
Used airfoiltool.com for polar generation
