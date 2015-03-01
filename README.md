# elec-temp

Grabs electricity usage data from my [United Illuminating account scraper](https://github.com/langelgjm/energy-usage) and temperature data from my [outdoor temperature monitor](https://github.com/langelgjm/imp-temp-and-light), groups the time series temperature data by day, then fits a second-order polynomial to the data and plots the results on [Plotly](https://plot.ly/~langelgjm/271/electricity-usage-mean-outdoor-temperature-updated-daily/).

Illustrates a simple use of pandas and numpy.
