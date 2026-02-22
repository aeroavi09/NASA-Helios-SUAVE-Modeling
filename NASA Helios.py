# nasa_helios.py 
# ----------------------------------------------------------------------
#   Imports
# ----------------------------------------------------------------------
import os
import sys
import subprocess

#set path to the folder of where i have open vsp SET TO YOUR OWN PATH
vsp_main = r'C:\VSP39'
vsp_engine = r'C:\VSP39\python\openvsp\openvsp'
if os.path.exists(vsp_main):
    os.add_dll_directory(vsp_main)
    if vsp_engine not in sys.path:
        sys.path.insert(0, vsp_engine)
try:
    import _vsp as vsp
    vsp.VSPRenew()
    print("Vsp works")

except Exception as e:
    print(f"VSP Error: {e}")

# General Python Imports
import numpy as np
# Numpy is a commonly used mathematically computing package. It contains many frequently used
# mathematical functions and is faster than native Python, especially when using vectorized
# quantities.
import matplotlib.pyplot as plt
# Matplotlib's pyplot can be used to generate a large variety of plots. Here it is used to create
# visualizations of the aircraft's performance throughout the mission.

# SUAVE Imports
import SUAVE
assert SUAVE.__version__=='2.5.2', 'These tutorials only work with the SUAVE 2.5.2 release'
from SUAVE.Core import Data, Units 
from SUAVE.Methods.Propulsion import propeller_design
from SUAVE.Methods.Geometry.Two_Dimensional.Planform import segment_properties
from SUAVE.Plots.Performance import *
from SUAVE.Components.Energy.Networks.Solar import Solar
from SUAVE.Methods.Propulsion import propeller_design
from SUAVE.Methods.Power.Battery.Sizing import initialize_from_mass
import time

from SUAVE.Input_Output.OpenVSP import write, get_vsp_measurements
from SUAVE.Input_Output.OpenVSP.vsp_read import vsp_read

#from SUAVE.Methods.Geometry.Two_Dimensional.Planform import process_main_wing_geometry as process_wing

from SUAVE.Plots.Geometry import plot_vehicle

from copy import deepcopy

output_name = "nasa_helios_.vsp3" #name of file in openvsp
plane_name = 'NASA Helios'

def main():
    vehicle = vehicle_setup()
    
    vsp_write_read(vehicle)
    
    plot_vehicle(vehicle)
    
    # Setup analyses and mission
    analyses = base_analysis(vehicle)
    analyses.finalize()
    mission  = mission_setup(analyses,vehicle)
    
    # evaluate
    results = mission.evaluate()
    
    plot_mission(results)
    
    results = mission.evaluate()
    return

def vehicle_setup():
    
    vehicle                                     = SUAVE.Vehicle() #repeatable
    vehicle.tag                                 = plane_name #repeatable
    
    #this is the fuel and mass stuff
    vehicle.mass_properties.max_takeoff         = 2048 * Units.pounds
    vehicle.mass_properties.takeoff             = 2048 * Units.pounds
    vehicle.mass_properties.max_zero_fuel       = 1322 * Units.pounds
    
    #maximum g-load, based on FAA regulations for civil aircraft regulations
    vehicle.envelope.ultimate_load              = 2.5
    vehicle.envelope.limit_load                 = 2.5
    
    #wing area and number of passengers
    vehicle.reference_area                      = 1976 * Units.feet**2
    vehicle.passengers                          = 0
    
    # from solar uav tutorial      
    vehicle.envelope.maximum_dynamic_pressure = 0.5*1.225*(12.07**2.) #Max q
    
    
    #------------------------
    # main wing 
    #------------------------
    
    wing                                        = SUAVE.Components.Wings.Main_Wing() #repeatable
    wing.tag                                    = 'main_wing' #repeatable
    wing.sweeps.quarter_chord                   = 0.0 * Units.deg
    wing.thickness_to_chord                     = 0.15
    wing.areas.reference                        = 1976 * Units.feet**2
    wing.spans.projected                        = 247 * Units.feet
    wing.chords.root                            = 8 * Units.feet
    wing.chords.tip                             = 8 * Units.feet
    wing.taper                                  = wing.chords.tip/wing.chords.root #repeatable, try not to
    wing.aspect_ratio                           = wing.spans.projected **2 / wing.areas.reference #repeatable
    wing.twists.root                            = 0.0 * Units.degrees
    wing.twists.tip                             = 5.0 * Units.degrees
    wing.areas.wetted                           = 2.0 * wing.areas.reference
    wing.areas.exposed                          = 0.9 * wing.areas.wetted
    wing.areas.affected                         = 0.9 * wing.areas.wetted    
    wing.twists.root                            = 0.0 * Units.degrees
    wing.origin                                 = [[0 * Units.feet, 0 * Units.feet, -0 * Units.feet]] #x,y,z
    wing.vertical                               = False
    wing.symmetric                              = True
    wing.high_lift                              = False
    wing.dynamic_pressure_ratio                 = 1.0
    
    # wing segments ------------
    
    #root
    segment                                     = SUAVE.Components.Wings.Segment()#repeatable
    segment.tag                                 = 'root' #repeatable
    segment.percent_span_location               = 0.0
    segment.twist                               = 0.0 * Units.deg
    segment.root_chord_percent                  = 1.0
    segment.thickness_to_chord                  = 0.12
    segment.dihedral_outboard                   = 0 * Units.deg
    segment.sweeps.quarter_chord                = 0 * Units.deg
    airfoil = SUAVE.Components.Airfoils.Airfoil()
    airfoil.coordinate_file = './Airfoils/sd6080.txt'
    segment.append_airfoil(airfoil)
    wing.append_segment(segment) #repeatable
    
    #break
    segment                                     = SUAVE.Components.Wings.Segment()#repeatable
    segment.tag                                 = 'break' #repeatable
    segment.percent_span_location               = 0.652
    segment.twist                               = 0.0 * Units.deg
    segment.root_chord_percent                  = 1
    segment.thickness_to_chord                  = 0.12
    segment.dihedral_outboard                   = 10 * Units.deg
    segment.sweeps.quarter_chord                = 0 * Units.deg
    airfoil = SUAVE.Components.Airfoils.Airfoil()
    airfoil.coordinate_file = './Airfoils/sd6080.txt'
    segment.append_airfoil(airfoil)
    wing.append_segment(segment) #repeatable
        
    #tip
    segment                                     = SUAVE.Components.Wings.Segment()#repeatable
    segment.tag                                 = 'tip' #repeatable
    segment.percent_span_location               = 1.0
    segment.twist                               = 5.0 * Units.deg
    segment.root_chord_percent                  = 1
    segment.thickness_to_chord                  = 0.115
    segment.dihedral_outboard                   = 0 * Units.deg
    segment.sweeps.quarter_chord                = 0 * Units.deg
    airfoil = SUAVE.Components.Airfoils.Airfoil()
    airfoil.coordinate_file = './Airfoils/sd6080.txt'
    segment.append_airfoil(airfoil)
    wing.append_segment(segment) #repeatable
    
    
    wing                                        = segment_properties(wing)
    wing                                        = SUAVE.Methods.Geometry.Two_Dimensional.Planform.wing_planform(wing)
    
    vehicle.append_component(wing)
    
    #------------------------
    # vertical stabilizer pylon
    #------------------------
    
    wing                                        = SUAVE.Components.Wings.Vertical_Tail() #repeatable
    wing.tag                                    = 'vertical_stabilizer_1' #repeatable
    wing.sweeps.quarter_chord                   = 44.427 * Units.deg
    wing.thickness_to_chord                     = 0.16662
    wing.areas.reference                        = 37.837 * Units.feet**2
    wing.spans.projected                        = 4.698 * Units.feet
    wing.chords.root                            = 8.0538 * Units.feet
    wing.chords.tip                             = 8.0538 * Units.feet
    wing.taper                                  = wing.chords.tip/wing.chords.root #repeatable, try not to
    wing.aspect_ratio                           = wing.spans.projected **2 / wing.areas.reference #repeatable
    wing.twists.root                            = 0.0 * Units.degrees
    wing.twists.tip                             = 0.0 * Units.degrees
    wing.areas.wetted                           = 2.0 * wing.areas.reference
    wing.areas.exposed                          = 0.8 * wing.areas.wetted
    wing.areas.affected                         = 0.6 * wing.areas.wetted    
    wing.twists.root                            = 0.0 * Units.degrees
    wing.origin                                 = [[-4.698 * Units.feet, 0 * Units.feet, -4.698 * Units.feet]] #x,y,z
    wing.vertical                               = True
    wing.symmetric                              = False
    wing.t_tail                                 = False
    wing.high_lift                              = False
    wing.dynamic_pressure_ratio                 = 1.0
    
    wing                                        = SUAVE.Methods.Geometry.Two_Dimensional.Planform.wing_planform(wing)
    
    vehicle.append_component(wing)
    
    #------------------------
    # vertical stabilizer pylon 2
    #------------------------
    
    wing                                        = SUAVE.Components.Wings.Vertical_Tail() #repeatable
    wing.tag                                    = 'vertical_stabilizer_2' #repeatable
    wing.sweeps.quarter_chord                   = 44.427 * Units.deg
    wing.thickness_to_chord                     = 0.16662
    wing.areas.reference                        = 2*37.837 * Units.feet**2 #because its symmetric
    wing.spans.projected                        = 2*4.698 * Units.feet #because its symmetric
    wing.chords.root                            = 8.0538 * Units.feet
    wing.chords.tip                             = 8.0538 * Units.feet
    wing.taper                                  = wing.chords.tip/wing.chords.root #repeatable, try not to
    wing.aspect_ratio                           = wing.spans.projected **2 / wing.areas.reference #repeatable
    wing.twists.root                            = 0.0 * Units.degrees
    wing.twists.tip                             = 0.0 * Units.degrees
    wing.origin                                 = [[-4.698 * Units.feet, 40.269 * Units.feet, -4.698 * Units.feet]] #x,y,z
    wing.vertical                               = True
    wing.symmetric                              = True
    wing.t_tail                                 = False
    wing.high_lift                              = False
    wing.dynamic_pressure_ratio                 = 1.0
    
    wing                                        = SUAVE.Methods.Geometry.Two_Dimensional.Planform.wing_planform(wing)
    
    vehicle.append_component(wing)
    
    #------------------------
    # vertical stabilizer pylon 3
    #------------------------
    
    wing                                        = SUAVE.Components.Wings.Vertical_Tail() #repeatable
    wing.tag                                    = 'vertical_stabilizer_3' #repeatable
    wing.sweeps.quarter_chord                   = 44.427 * Units.deg
    wing.thickness_to_chord                     = 0.16662
    wing.areas.reference                        = 2*37.837 * Units.feet**2 #because its symmetric
    wing.spans.projected                        = 2*4.698 * Units.feet #because its symmetric
    wing.chords.root                            = 8.0538 * Units.feet
    wing.chords.tip                             = 8.0538 * Units.feet
    wing.taper                                  = wing.chords.tip/wing.chords.root #repeatable, try not to
    wing.aspect_ratio                           = wing.spans.projected **2 / wing.areas.reference #repeatable
    wing.twists.root                            = 0.0 * Units.degrees
    wing.twists.tip                             = 0.0 * Units.degrees
    wing.origin                                 = [[-4.698 * Units.feet, (2*40.269) * Units.feet, -4.698 * Units.feet]] #x,y,z
    wing.vertical                               = True
    wing.symmetric                              = True
    wing.t_tail                                 = False
    wing.high_lift                              = False
    wing.dynamic_pressure_ratio                 = 1.0
    
    wing                                        = SUAVE.Methods.Geometry.Two_Dimensional.Planform.wing_planform(wing)
    
    vehicle.append_component(wing)
    
    #-----------------
    # build network
    #-----------------
    
    net = Solar()
    net.number_of_engines = 14
    
    # Component 1 the Sun
    sun = SUAVE.Components.Energy.Processes.Solar_Radiation()
    net.solar_flux = sun
        
    # Component 2 the solar panels
    panel = SUAVE.Components.Energy.Converters.Solar_Panel()
    panel.area                                  = 2000 *Units.feet**2
    panel.efficiency                            = 0.19
    net.solar_panel                             = panel
    
    # Component 3 the ESC
    esc = SUAVE.Components.Energy.Distributors.Electronic_Speed_Controller()
    esc.efficiency                              = 0.95 # Gundlach for brushless motors
    net.esc                                     = esc
    
    # Component 5 the Propeller
    # Design the Propeller
    
    prop_locations = [
        [-1.34* Units.feet, -13.423* Units.feet, 0],
        [-1.34* Units.feet, -13.423*2* Units.feet, 0],
        [-1.34* Units.feet, -13.423*4* Units.feet, 0],
        [-1.34* Units.feet, -13.423*5* Units.feet, 0],
        [-1.34* Units.feet, -13.423*6.5* Units.feet, 1.3423* Units.feet],
        [-1.34* Units.feet, -13.423*7.5* Units.feet, 1.3423*2.5* Units.feet],
        [-1.34* Units.feet, -13.423*8.5* Units.feet, 1.3423*4.25* Units.feet],
        [-1.34* Units.feet, 13.423* Units.feet, 0],
        [-1.34* Units.feet, 13.423*2* Units.feet, 0],
        [-1.34* Units.feet, 13.423*4* Units.feet, 0],
        [-1.34* Units.feet, 13.423*5* Units.feet, 0],
        [-1.34* Units.feet, 13.423*6.5* Units.feet, 1.3423* Units.feet],
        [-1.34* Units.feet, 13.423*7.5* Units.feet, 1.3423*2.5* Units.feet],
        [-1.34* Units.feet, 13.423*8.5* Units.feet, 1.3423*4.25* Units.feet]
    ]
    
        # design ONCE before the loop
    prop_template = SUAVE.Components.Energy.Converters.Propeller()
    prop_template.number_of_blades      = 2.0
    prop_template.freestream_velocity   = 75.9968 * Units['m/s']
    prop_template.angular_velocity      = 700 * Units['rpm']
    prop_template.tip_radius            = (79/2) * Units.inches
    prop_template.hub_radius            = 4 * Units.inches
    prop_template.design_Cl             = 0.7
    prop_template.design_altitude       = 70000 * Units.feet
    prop_template.design_power          = 1500 * Units.watts
    prop_template.design_thrust         = None
    prop_template.airfoil_geometry      = ['./Airfoils/sd6080.txt']
    prop_template.airfoil_polars        = [[     
            './Airfoils/Polars/xf-sd6080-il-50000.txt',
            './Airfoils/Polars/xf-sd6080-il-100000.txt',
            './Airfoils/Polars/xf-sd6080-il-200000.txt',
            './Airfoils/Polars/xf-sd6080-il-500000.txt',
            './Airfoils/Polars/xf-sd6080-il-1000000.txt' ]]
    prop_template.airfoil_polar_stations = [0] * 20
    
    print("Designing propeller...")
    prop_template = propeller_design(prop_template)
    print("Done.")
    
    # then in the loop just copy and set origin
    for i, location in enumerate(prop_locations):
        prop = deepcopy(prop_template)
        prop.tag    = f'propeller_{i+1}'
        prop.origin = [location]
        net.propellers.append(prop)
    
        motor = SUAVE.Components.Energy.Converters.Motor()
        motor.tag              = f'motor_{i+1}'
        motor.resistance       = 0.006
        motor.no_load_current  = 2.5  * Units.ampere
        motor.speed_constant   = 700  * Units['rpm']
        motor.propeller_radius = prop_template.tip_radius
        motor.propeller_Cp     = prop_template.design_power_coefficient
        motor.gear_ratio       = 12.
        motor.gearbox_efficiency = .98
        motor.expected_current = 60.
        net.motors.append(motor)
        
    #everything past here is NOT within the for loop! if it is it will have an infinite loop of death
    # Component 6 the Payload
    payload = SUAVE.Components.Energy.Peripherals.Payload()
    payload.power_draw           = 100. * Units.watts 
    payload.mass_properties.mass = 726 * Units.pounds
    net.payload                  = payload
    
    # Component 7 the Avionics
    avionics = SUAVE.Components.Energy.Peripherals.Avionics()
    avionics.power_draw = 50. * Units.watts
    net.avionics        = avionics      

    # Component 8 the Battery
    bat = SUAVE.Components.Energy.Storages.Batteries.Constant_Mass.Lithium_Ion()
    bat.mass_properties.mass = 95.0 * Units.kg
    bat.specific_energy      = 800. * Units.Wh/Units.kg
    bat.max_voltage          = 130.0
    initialize_from_mass(bat)
    net.battery              = bat
   
    #Component 9 the system logic controller and MPPT
    logic = SUAVE.Components.Energy.Distributors.Solar_Logic()
    logic.system_voltage  = 120.0
    logic.MPPT_efficiency = 0.95
    net.solar_logic       = logic
    
    # add the solar network to the vehicle
    vehicle.append_component(net)  
    
    return vehicle

def configs_setup(vehicle):
    
    # ------------------------------------------------------------------
    #   Initialize Configurations
    # ------------------------------------------------------------------
    
    configs = SUAVE.Components.Configs.Config.Container()
    
    base_config = SUAVE.Components.Configs.Config(vehicle)
    base_config.tag = 'base'
    configs.append(base_config)
    
    # ------------------------------------------------------------------
    #   Cruise Configuration
    # ------------------------------------------------------------------
    
    config = SUAVE.Components.Configs.Config(base_config)
    config.tag = 'cruise'
    
    configs.append(config)
    
    return configs

def analyses_setup(configs):
    
    analyses = SUAVE.Analyses.Analysis.Container()
    
    # build a base analysis for each config
    for tag,config in configs.items():
        analysis = base_analysis(config)
        analyses[tag] = analysis
    
    return analyses

def base_analysis(vehicle):

    # ------------------------------------------------------------------
    #   Initialize the Analyses
    # ------------------------------------------------------------------     
    analyses = SUAVE.Analyses.Vehicle()
    
    # ------------------------------------------------------------------
    #  Basic Geometry Relations
    sizing = SUAVE.Analyses.Sizing.Sizing()
    sizing.features.vehicle = vehicle
    analyses.append(sizing)
    
    # ------------------------------------------------------------------
    #  Weights
    weights = SUAVE.Analyses.Weights.Weights_UAV()
    weights.settings.empty = \
        SUAVE.Methods.Weights.Correlations.Human_Powered.empty
    weights.vehicle = vehicle
    analyses.append(weights)
    
    # ------------------------------------------------------------------
    #  Aerodynamics Analysis
    
    # Calculate extra drag from landing gear:
    
    mb_wheel_width  = 3. * Units.inches #mountain bike wheels
    mb_wheel_height = 29. * Units.inches
    scooter_gear_height  = .100 * Units.meters #scooter wheels
    scooter_gear_height   = .024 * Units.meters
    
    total_wheel       = 10*mb_wheel_width*mb_wheel_height + scooter_gear_height*scooter_gear_height
    
    drag_area = .5 * total_wheel  #only half of the wheels are wetted
    
    aerodynamics = SUAVE.Analyses.Aerodynamics.Fidelity_Zero()
    aerodynamics.geometry = vehicle
    aerodynamics.settings.drag_coefficient_increment =  1.0*drag_area/vehicle.reference_area
    analyses.append(aerodynamics)
    
    # ------------------------------------------------------------------
    #  Energy
    energy = SUAVE.Analyses.Energy.Energy()
    energy.network = vehicle.networks #what is called throughout the mission (at every time step))
    analyses.append(energy)
    
    # ------------------------------------------------------------------
    #  Planet Analysis
    planet = SUAVE.Analyses.Planets.Planet()
    analyses.append(planet)
    
    # ------------------------------------------------------------------
    #  Atmosphere Analysis
    atmosphere = SUAVE.Analyses.Atmospheric.US_Standard_1976()
    atmosphere.features.planet = planet.features
    analyses.append(atmosphere)   
    
    # done!
    return analyses    

def mission_setup(analyses,vehicle):
    
    # ------------------------------------------------------------------
    #   Initialize the Mission
    # ------------------------------------------------------------------

    mission = SUAVE.Analyses.Mission.Sequential_Segments()
    mission.tag = 'mission'

    mission.atmosphere  = SUAVE.Attributes.Atmospheres.Earth.US_Standard_1976()
    mission.planet      = SUAVE.Attributes.Planets.Earth()
    
    # unpack Segments module
    Segments = SUAVE.Analyses.Mission.Segments
    
    # base segment
    base_segment = Segments.Segment()   
    base_segment.process.iterate.initials.initialize_battery = SUAVE.Methods.Missions.Segments.Common.Energy.initialize_battery
    
    # ------------------------------------------------------------------    
    #   Cruise Segment: constant speed, constant altitude
    # ------------------------------------------------------------------    
    
    segment = SUAVE.Analyses.Mission.Segments.Cruise.Constant_Mach_Constant_Altitude(base_segment)
    segment.tag = "cruise"
    
    # connect vehicle configuration
    segment.analyses.extend(analyses)
    
    # segment attributes     
    segment.state.numerics.number_control_points = 64
    segment.start_time = time.strptime("12:00:00 Jun 21, 2025", "%H:%M:%S %b %d, %Y")
    segment.altitude       = 50000  * Units.feet 
    segment.air_speed      = 75.9968 * Units['m/s']
    segment.distance       = 300 * Units.miles
    segment.battery_energy = vehicle.networks.solar.battery.max_energy*1.0 #Charge the battery to start
    segment.latitude       = 41.8832   # this defaults to degrees (do not use Units.degrees)
    segment.longitude      = 87.6324 # this defaults to degrees
    
    segment = vehicle.networks.solar.add_unknowns_and_residuals_to_segment(segment,initial_power_coefficient = 0.05)   
    
    mission.append_segment(segment)    
    
    
    # ------------------------------------------------------------------    
    #   Cruise Segment 2, a descent at constant speed
    # ------------------------------------------------------------------    

    segment = Segments.Descent.Constant_Speed_Constant_Rate(base_segment)
    segment.tag = "descend"

    segment.analyses.extend( analyses )
    
    segment.state.numerics.number_control_points    = 64
    segment.altitude_end                            = 25000 * Units.feet
    segment.air_speed                               = 80 * Units['m/s']
    segment.descent_rate                            = 5 * Units.feet
    
    ones_row                                        = segment.state.ones_row  
    segment.state.numerics.number_control_points    = 32  
    segment.state.unknowns.throttle                 = 1.0 * ones_row(1)
    segment = vehicle.networks.solar.add_unknowns_and_residuals_to_segment(segment, initial_power_coefficient=0.05)
    
    segment.process.iterate.conditions.stability    = SUAVE.Methods.skip
    segment.process.finalize.post_process.stability = SUAVE.Methods.skip    

    # add to mission
    mission.append_segment(segment)

    # ------------------------------------------------------------------    
    #   Mission definition complete    
    # ------------------------------------------------------------------
    
    return mission

def missions_setup(base_mission):

    # the mission container
    missions = SUAVE.Analyses.Mission.Mission.Container()
    
    # ------------------------------------------------------------------
    #   Base Mission
    # ------------------------------------------------------------------
    
    missions.base = base_mission
    
    # done!
    return missions

def plot_mission(results,line_style='bo-'):
    
    # Plot Flight Conditions 
    plot_flight_conditions(results, line_style)
    
    # Plot Aerodynamic Forces 
    plot_aerodynamic_forces(results, line_style)
    
    # Plot Aerodynamic Coefficients 
    plot_aerodynamic_coefficients(results, line_style)
    
    # Drag Components
    plot_drag_components(results, line_style)
    
    # Plot Altitude, sfc, vehicle weight 
    plot_altitude_sfc_weight(results, line_style)
    
    # Plot Velocities 
    plot_aircraft_velocities(results, line_style)  

    return

def vsp_write_read(vehicle):
    
    
    #save this vehicle
    write(vehicle, plane_name)
    
    return 

if __name__ == '__main__':
    main()      
    plt.show()
    

