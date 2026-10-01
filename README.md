# Trans-Boundary Smog Prediction

Predicting composite smog spikes in Pakistani Punjab cities using upwind
cross-border crop fires (NASA VIIRS) and weather data (Open-Meteo).

## Project structure
```
Data Science Project/
├── SmogPrediction.ipynb
├── Project_Proposal.pdf
├── requirements.txt
├── README.md
└── Dataset/
    ├── India/      (Air Quality, NASA, Weather)
    └── Pakistan/   (Air Quality, NASA, Weather)
```

## Returning to the project (my own setup)
1. Open a terminal in the project folder.
2. Activate the environment:
```
   venv\Scripts\activate.bat
```
3. Open `SmogPrediction.ipynb` and select the kernel **Python (smog-venv)**.
4. If you install a new package, update the requirements file:
```
   pip freeze > requirements.txt
```

## Running the project from a fresh clone
1. Clone the repository:
```
   git clone <repo-url>
   cd "Data Science Project"
```
2. Create and activate a virtual environment:
```
   python -m venv venv
   venv\Scripts\activate.bat        (Windows)
   source venv/bin/activate         (Mac/Linux)
```
3. Install dependencies:
```
   pip install -r requirements.txt
```
4. Add the data: place the raw files in `Dataset/` using the structure above
   (data is not included in the repo because of file size; see the data
   sources below).
5. Register the kernel and open the notebook:
```
   python -m ipykernel install --user --name=smog-venv --display-name "Python (smog-venv)"
   jupyter notebook SmogPrediction.ipynb
```
   Select the kernel **Python (smog-venv)** and run all cells from top to bottom.

## Data sources
- Air quality and weather: Open-Meteo (hourly, 2022-2024)
- Fire hotspots: NASA VIIRS FIRMS
