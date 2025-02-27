# Heat Map Confusion Repository

This repository is based on the paper "[HMC: Robust Privacy Protection of Mobility Data against Multiple Re-Identification Attacks](https://hal.science/hal-01954041)" by Mohamed Maouche, Sonia Ben Mokhtar, and Sara Bouchenak.

## Structure

The main program is located in the **Heat Map Confusion** folder. It contains the necessary files for performing Heat Map Creation and Heat Map Alteration. Additionally, it is possible to execute AP-Attacks. Mobility Trace Reconstruction is currently still in progress (WIP - Work in Progress).

### Folder Structure:

- **data**:
  - **profiles_pickl_epsilon_1**: Contains profiles with epsilon 1 in Pickle format.
  - **profiles_pickl_epsilon_2**: Contains profiles with epsilon 2 in Pickle format.
  - **profiles_pickl_epsilon_1_5**: Contains profiles with epsilon 1.5 in Pickle format.
  - **profiles_txt**: Contains profiles in text format.
- **notebooks**:
  - **HMC.ipynb**: Jupyter Notebook that includes the implementation and execution of the HMC process.
- **output**:
  - **AP-Attack**: Contains outputs of the AP scenario for different epsilon values (Epsilon1, Epsilon2, Epsilon15).
- **src**:
  - **ap_attack.py**: Script for executing AP attacks.
  - **data_loader.py**: Loads and processes the required data.
  - **distance.py**: Computes distances, likely for attacks or mobility analyses.
  - **heatmap.py**: Contains functions for creating and modifying heatmaps.
  - **helper.py**: Helper functions for various tasks.
  - **hmc.py**: The main implementation of the Heat Map Confusion (HMC) algorithm.
  - **main.py**: The main script to run the program.
  - **mobility_trace_reconstruction.py**: Script for reconstructing mobility traces, currently still in progress.
  - **split_dataframe.py**: Helper functions for splitting DataFrames.
- **.gitignore**: Specifies files and directories to ignore in version control.
- **README.md**: The file you are currently reading.
- **requirements.txt**: Lists the required Python libraries.

## Functionality

The **HMC** program (Heat Map Confusion) is fully functional and allows for the creation and modification of heat maps as well as the execution of AP-Attacks. The Mobility Trace Reconstruction feature is still under development.

## Installation

To install the required dependencies, run the following command:

```bash
pip install -r requirements.txt
```

## Author

Christian Dürr | Etou11
