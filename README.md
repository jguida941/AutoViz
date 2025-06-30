<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">

</head>
<body>

  <h1>AutoViz</h1>
  <p>
    🚀 A Zero-Code Auto-Visual Analytics Tool — Built with PyQt6, Matplotlib, and Pandas
  </p>
  <p>
    AutoViz is a sleek, fast, fully functional data visualization and regression dashboard built in just over an hour.
    It provides non-technical users the ability to upload CSVs, generate charts, run regression analysis, and explore key metrics
    without writing a single line of code.
  </p>
  <p><strong>License:</strong> Creative Commons BY-NC 4.0</p>

  <div class="section">
    <h2>Features</h2>
    <ul>
      <li>📂 Drag & Drop CSV Import</li>
      <li>📊 Live Bar, Line, and Pie Chart Generator</li>
      <li>🧠 Smart Axis Detection from CSV Headers</li>
      <li>📉 On-Click OLS Regression (scikit-learn / statsmodels)</li>
      <li>📋 Auto-computed Summary Stats & Memory Usage</li>
      <li>🌒 Modern Dark UI with Neon Highlights</li>
      <li>🧠 No Code Required — Works Right Out of the Box</li>
    </ul>
  </div>

  <div class="section">
    <h2>Installation</h2>
    <pre><code>git clone https://github.com/jguida941/AutoViz.git
cd AutoViz
pip install -r requirements.txt
python AutoViz.py</code></pre>
  </div>

  <div class="section">
    <h2>Usage</h2>
    <ol>
      <li>Launch the app (<code>AutoViz.py</code>)</li>
      <li>Use the sidebar to load your CSV file</li>
      <li>Choose the chart type and axes via dropdown</li>
      <li>Click Generate Plot</li>
      <li>Optionally, run regression via the Run OLS button</li>
      <li>Use the Export tab to save outputs or analysis logs</li>
    </ol>
    <p>✅ Works with any well-formed CSV (e.g. finance, marketing, engineering logs, etc.)</p>
  </div>

  <div class="section">
    <h2>🍎 Example CSV</h2>
    <p>Here’s a sample format your CSV could follow:</p>
    <pre><code>Department,Month,Revenue,Expenses,Profit
Sales,Jan,100000,60000,40000
Sales,Feb,110000,65000,45000
Marketing,Jan,50000,40000,10000
Marketing,Feb,70000,50000,20000
Engineering,Jan,120000,70000,50000
Engineering,Feb,130000,80000,50000</code></pre>
  </div>

  <div class="section">
    <h2>🛠 Planned Features</h2>
    <ul>
      <li>Auto-update headers when switching datasets</li>
      <li>Forecasting module (e.g. ARIMA / Exponential Smoothing)</li>
      <li>Plugin system for custom chart types</li>
      <li>Session autosave & live theme switching</li>
    </ul>
  </div>

  <div class="section">
    <h2>🤝 Contributing</h2>
    <p>
      Pull requests are welcome! For major changes, please open an issue first to discuss what you would like to change or add.
    </p>
  </div>

  <div class="section">
    <h2>🛡 License</h2>
    <p>
      Creative Commons Attribution-NonCommercial 4.0 International<br>
      <a href="https://creativecommons.org/licenses/by-nc/4.0/">https://creativecommons.org/licenses/by-nc/4.0/</a>
    </p>
    <p>You are free to:</p>
    <ul>
      <li>Share — copy and redistribute the material in any medium or format</li>
      <li>Adapt — remix, transform, and build upon the material</li>
    </ul>
    <p>Under the following terms:</p>
    <ul>
      <li>Attribution — You must give appropriate credit, provide a link to the license, and indicate if changes were made</li>
      <li>NonCommercial — You may not use the material for commercial purposes</li>
    </ul>
    <p>No additional restrictions — You may not apply legal terms or technological measures that legally restrict others from doing anything the license permits.</p>
  </div>

  <div class="section">
    <h2>👁️‍🗨️ About</h2>
    <p>
      Built by @jguida941 as a proof-of-concept to replace tedious data automation and analysis scripts.<br>
      If AutoViz helped you or inspired you, give it a ⭐️!
    </p>
  </div>

</body>
</html>
