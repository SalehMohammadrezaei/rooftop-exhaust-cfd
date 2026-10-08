# AIJ UWE Benchmark Dataset – Case H (112C): Wind Tunnel Experiment for Flow and Dispersion around a 1:1:2 Shape Building Model

## Investigators

### Data Collectors

- Ryuichiro Yoshie (Tokyo Polytechnic University, Japan)  
- Takumi Tachibana (Wind Engineering Institute, Japan)

### Dataset Editors and Distributors

- Yoshihide Tominaga (Niigata Institute of Technology, Japan)  
- Hideki Kikumoto (The University of Tokyo, Japan)  
- Tsubasa Okaze (Tokyo Institute of Science, Japan)

### Contact for Questions

Ryuichiro Yoshie  
Email: [yoshie@arch.t-kougei.ac.jp](mailto:yoshie@arch.t-kougei.ac.jp)

---

## Overview

This dataset provides wind tunnel measurement results of wind velocity and gas concentration around a 1:1:2 shape building model with a near-ground point source. The experiment was conducted under neutrally stratified conditions.

---

## Dataset Contents

### File List

- **AF_caseH.csv**  
  Vertical profile of the approaching flow.  
  **Columns:**  
  
  - `x`, `y`, `z` (m): Coordinates  
  - `U`, `V`, `W` (m/s): Mean wind velocity components  
  - `u_rms`, `v_rms`, `w_rms` (m/s): Root-mean-square of velocity fluctuations
  - `uw`, `uv` (m2/s2): Reynolds shear stresses  
  - `k` (m2/s2): Turbulent kinetic energy

- **RS_caseH.csv**  
  Wind and concentration measurements around the building.  
  **Columns:**  
  
  - `No.`: Measurement point ID  
  - `x`, `y`, `z` (m): Coordinates  
  - `U`, `V`, `W` (m/s): Mean wind velocities  
  - `u_rms`, `v_rms`, `w_rms` (m/s): Root-mean-square of velocity fluctuations
  - `k` (m2/s2): Turbulent kinetic energy
  - `<c>` (ppm): Gas concentration  
  - `c_rms` (ppm): Root-mean-square of concentration fluctuations  
  - `-999.9`: Indicates unmeasured values

- **MP-y_caseH.png**  
  Measurement points on the center vertical plane (`y/H = 0`)

- **MP-z_caseH.png**  
  Measurement points on multiple horizontal planes (`z/H = 1/16`, `1/4`, `1/2`)

- **LF_caseH.xlsx**  
  Legacy Excel version of the measurement dataset, provided as per the AIJ guidelines. Also available via: [Guidebook for CFD Predictions of Urban Wind Environment](https://www.aij.or.jp/jpn/publish/cfdguide/index_e.htm)

---

## Experimental Methodology

### Experimental Setup

- Model dimensions: 0.10 m (width, depth), 0.20 m (height)  
- Reynolds number: approx. 43,000 (based on U_H = 3.23 m/s and H = 0.20 m)  
- Tracer source: 4 mm diameter hole on floor, 0.25H from the leeward wall  
- Gas: Ethylene (C2H4), 100% concentration  
- Flow rate: 5.83 × 1e-6 m3/s

### Instrumentation

- Wind velocity:  
  
  - Constant temperature anemometer (DANTEC 90C10)  
  - Split-fiber probe (DANTEC 55R55, 55R56, 55R57)  
  - Sampling rate: 1000 Hz, Duration: 120 s

- Gas concentration:  
  
  - High-speed total hydrocarbon analyzer  
  - Sampling rate: 1000 Hz, Duration: 120 s

### Location

Tokyo Polytechnic University, Atsugi, Japan

---

## Metadata

- **Units:**  
  - Length: meters (m)  
  - Wind speed: meters per second (m/s)  
  - Concentration: parts per million (ppm)
- **File creation date:** 21 April, 2025  
- **Format:** CSV, PNG, XLSX  
- **Missing values:** -999.9  
- **License:** [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)
- **Version:** 1.0
- **Citation requested:** Yoshie, R. (2016). *Wind Tunnel Experiment and Large Eddy Simulation of Pollutant/Thermal Dispersion in Non-isothermal Turbulent Boundary Layer*. Adv Environ Wind Eng, 167–196. https://doi.org/10.1007/978-4-431-55912-2_9

---

## Data Accessibility

- **Repository name:** Zenodo  
- **DOI:** 10.5281/zenodo.15429871
- **URL:** https://zenodo.org/records/15429871

---

## Related Articles

- Yoshie, R. (2016). *Wind Tunnel Experiment and Large Eddy Simulation of Pollutant/Thermal Dispersion in Non-isothermal Turbulent Boundary Layer*. Adv Environ Wind Eng, 167–196. https://doi.org/10.1007/978-4-431-55912-2_9
- Tokyo Polytechnic University, Wind Tunnel Experimental Database of Air Pollution around a Building: Database on Indoor / Outdoor Air Pollution. http://www.wind.arch.t-kougei.ac.jp/info_center/pollution/pollution.html

---

*Note: This dataset is part of the AIJ urban wind environment benchmark project, which aims to support the development and validation of urban flow simulations.*
