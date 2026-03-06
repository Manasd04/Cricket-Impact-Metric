# 🏏 Cricket Impact Metric (IM) Framework

**A Context-Aware, Data-Driven Metric for Measuring True Match Output**

## Project Structure

The project is modularized into a clean architecture:

- `data/`: Place your raw CSV dataset files here.
- `src/`: Contains all logic modules:
  - `data_loader.py`
  - `feature_engineering.py`
  - `performance.py`
  - `context_situation.py`
  - `impact_model.py`
  - `rolling_metric.py`
  - `visualization.py`
  - `pipeline.py`
- `visualizations/`: Generated plots are saved here.

## Execution Example

```bash
python main.py --data_dir data/
```
