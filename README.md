# Glucose measurement visualization

## Usage

### Quickstart

The following code produces a nice looking .pdf-file visualizing your glucose level over a time-span of three months. 

```python
    from cgv import CGV, PDF
    c_g_v = CGV(csv_path="./file/to/data.csv")
    PDF(c_g_v.plot_since_three_month(), name="Your Name")
```

``CGV`` processes the data in the csv-file and builds the plots as pgf's. 
Whereas, ``PDF`` brings all together and produces a nicely looking pdf, using LaTeX under the hood.

