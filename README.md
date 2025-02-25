# image_to_points_for_opentron
To create drawings for Opentrons plating using an image as reference in a python GUI. Created as part of a HTGAA 2025 (MIT) assignment.

# Dependencies
 - tk
 - matplotlib
 - pandas
 - numpy
 - pillow

# How to run
```
python image_to_points.py imagen.png
```

Orient your image as needed and then add as many points (R,G,B,O,Y colors) as you want using the image as reference. Once finished, export your TSV file. You can excecute it using the following code in an Opentron OT-2:

``` python
from opentrons import types
import pandas as pd

# Adjust with my data  <-------------------------------------------
metadata = {
    'protocolName': 'HTGAA Opentrons Lab',
    'author': 'HTGAA',
    'source': 'HTGAA 2025',
    'apiLevel': '2.20'
}

##############################################################################
###   Robot deck setup constants - don't change these
##############################################################################

# These are the modules
TIP_RACK_DECK_SLOT = 9
COLORS_DECK_SLOT = 6
AGAR_DECK_SLOT = 5
PIPETTE_STARTING_TIP_WELL = 'A1'

well_colors = {
    'A1' : 'Red',
    'B1' : 'Green',
    'C1' : 'Orange',
}


def run(protocol):
  ##############################################################################
  ###   Load labware, modules and pipettes
  ##############################################################################
  #This tells where everything is located

  # Tips
  tips_20ul = protocol.load_labware('opentrons_96_tiprack_20ul', TIP_RACK_DECK_SLOT, 'Opentrons 20uL Tips')

  # Pipettes
  pipette_20ul = protocol.load_instrument("p20_single_gen2", "right", [tips_20ul])

  # Modules
  temperature_module = protocol.load_module('temperature module gen2', COLORS_DECK_SLOT)

  # Temperature Module Plate
  temperature_plate = temperature_module.load_labware('opentrons_96_aluminumblock_generic_pcr_strip_200ul',
                                                      'Cold Plate')
  # Choose where to take the colors from
  color_plate = temperature_plate

  # Agar Plate
  agar_plate = protocol.load_labware('htgaa_agar_plate', AGAR_DECK_SLOT, 'Agar Plate')  ## TA MUST CALIBRATE EACH PLATE!
  # Get the top-center of the plate, make sure the plate was calibrated before running this
  center_location = agar_plate['A1'].top()

  pipette_20ul.starting_tip = tips_20ul.well(PIPETTE_STARTING_TIP_WELL)

  ##############################################################################
  ###   Patterning
  ##############################################################################

  ###
  ### Helper functions for this lab
  ###

  # pass this e.g. 'Red' and get back a Location which can be passed to aspirate()
  def location_of_color(color_string):
    for well,color in well_colors.items():
      if color.lower() == color_string.lower():
        return color_plate[well]
    raise ValueError(f"No well found with color {color_string}")

  # For this lab, instead of calling pipette.dispense(1, loc) use this: dispense_and_jog(pipette, 1, loc)
  def dispense_and_jog(pipette, volume, location):
      """
      Dispense and then move up 5mm and back down to shake all dispensed fluid off the tip;
      this also ensures it's not moving laterally before the dispense is done.
      """
      assert(isinstance(volume, (int, float)))
      pipette.dispense(volume, location)
      currLoc = pipette._get_last_location_by_api_version()
      pipette.move_to(currLoc.move(types.Point(z=5)))

  # Read CSV data <----------------------- HERE GOES THE TABLE ---------
  data = pd.read_csv('dots.csv')

  # Process each color in the order defined by well_colors
  for color_name in [well_colors[well] for well in sorted(well_colors.keys())]:
      # Filter data by color
      color_data = data[data['Color'] == color_name]
      if color_data.empty:
          continue
      
      # Create batches of dots with final volume <= 20 uL
      batches = []
      current_batch = []
      current_total = 0
      
      for _, row in color_data.iterrows():
          size = row['Size']
          if current_total + size > 20:
              batches.append(current_batch)
              current_batch = [row]
              current_total = size
          else:
              current_batch.append(row)
              current_total += size
      
      if current_batch:
          batches.append(current_batch)
      
      # Use a new tip for each color
      pipette_20ul.pick_up_tip()
      
      for batch in batches:
          # Compute total volume for each batch
          total_volume = sum(row['Size'] for row in batch)
          
          # Aspirate the necessary volume
          pipette_20ul.aspirate(total_volume, location_of_color(color_name))
          
          # Dispense each batch point
          for point in batch:
              x = point['X']
              y = -point['Y']  # Invertir eje Y si es necesario
              adjusted_location = center_location.move(types.Point(x=x, y=y))
              dispense_and_jog(pipette_20ul, point['Size'], adjusted_location)
      
      # Discard tip when the color is done
      pipette_20ul.drop_tip()

```
# PNG output
![image](https://github.com/elviorodriguez/image_to_points_for_opentron/blob/main/grafico_puntos.png)

# Opentron OT-2 simulation: TrypanOTron
![image](https://github.com/user-attachments/assets/fbf73860-6229-4e35-bead-278e08436684)
