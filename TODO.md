# TODO (Stock Data Prediction)

## App Config Layout

## App Layouts

### Modules
I recommend starting with the historical dashboard first since the realtime we
may have to query differently.

- stock-data-site/dashboards/historical_dash.py
- stock-data-site/dashboards/realtime_dash.py

### TODO
- Set dropdown options
  * Stock Symbols
  * open, close, high, low, volume
- Query for select options
  * update_trend on line 58 just returns dummy data
  * Get actual data from the SQL database:
    - You can query the FlaskSQLALchemy model StockPriceDay or StockPriceMinute
      * <http://flask.pocoo.org/docs/0.12/patterns/sqlalchemy/>
    - Alternatively write a raw SQL with Pandas
      * <https://pandas.pydata.org/pandas-docs/stable/generated/pandas.read_sql_query.html>
- Find a way to run periodic updates for the realtime
  * Check out the Plotly Dash documentation for this one
  * I once sorta hacked it by having the page refresh every 5 seconds and it
    was pretty smooth
- We might need to have the realtime data in a JSON so it might be good to know
  how to read JSON and return the data that way.
- Adjust the overall appearance of the layout
  * On line 28 theres a layout defined where you can make changes to the app's
    appearance
  * <https://dash.plot.ly/getting-started>
  * If there's an error the entire layout won't generate
  * Add any fields you might think is useful
    - Date filters maybe?

## Site Appearance

### Modules
- stock-data-site/templates/home.html
- stock-data-site/assets/css/bootstrap.min.css
- stock-data-site/assets/img/banner.jpg

### TODO
- Change use a different bootstrap since this one sucks
  * Maybe there's a Rutgers bootstrap we can use?
- Update the home.html file
  * This one is from my last class just as a placeholder
  * Pay attention to the tags `{% extends "base.html" %}...{% block body %}...{% endblock %}`
    - These are Jinja2 template tags and they define the theme of the site so
      only change what's in the block body tags
      * Navbar
      * CSS
      * JS Libraries
  * You can probably find some generater and paste the content
  * The banner is left over and needs to be changed

## Machine Learning

### Note
- Update the stock-data-pull repo for this one since it's not related to the
  site and needs to be run separately
  * The site VM isn't powerful enough to run Sklearn

### TODO
- Find out if we can use exising libraries.
  * Sklearn is usually what people use for Python machine-learning
- Know Bay, Neural, and SVM
  * Just learn how to use these libraries or your own code so we can generate
    stock predictions
  * Our input data will be:
    - Volume
    - High
    - Low
    - Close
    - Open
    - Twitter Data?
      * Discussed in another section
      * We need to figure out how to collect and store this
- For historical data we can probably just schedule this to run periodically
  and store to SQL
  * Know how to insert and update records
  * Create your own db table for predictions
    - Make sure we can show these predictions side by side with our collected
      data
      * Our data has a dateid and symbol so we need to match this
      * For Realtime
        - Minute level so take the max dateid and +1 minute per prediction
      * For Historical
        - Day level so take the max dateid and +1 day per prediction
- Data Normalization
  - Find how to normalize our data so each input value is fair
- Realtime
  * What **might** work best is to have something in the background
    periodically getting new data and **feeding** it as input
  * Save results to JSON for fast retrieval for site
- Weighting
  * Weight each perdiction alogrithm generated values based on error or chose
    the best

## Data Collection

### Note
- Update the stock-data-pull repo for this one since it's not related to the
  site and needs to be run separately
  * The site VM isn't powerful enough to run Sklearn

### TODO
- Twitter
  * Create a module for collecting number of relevant tweets for a company
  * Create an SQL table to store historical results
  * Realtime **might** have to stored as a JSON
  * We need something along the lines of tweets per day and tweets per minute
    or some hourly interval
  * You may need to manipulate the Twitter data to feed it the machine learning
    process
- Stock
  * Realtime for stock **might** need to be stored as a JSON
- Work with the machine learning person to let them know what the Twitter data
  looks like
