# Contributing

This is a research project repository. If you find a bug or have a suggestion,
please open an issue on GitHub describing the problem and steps to reproduce it.

Pull requests for documentation improvements or bug fixes are welcome.

## Setting up locally

```bash
git clone https://github.com/TasMumu/bangladesh-agri-research.git
cd bangladesh-agri-research
pip install -r requirements.txt
```

Note: running the data ingestion notebooks requires external credentials
(Google Earth Engine, Copernicus CDS). The dashboard runs from the pre-computed
DuckDB file only.
