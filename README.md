# Greek News Sites Performance Benchmark

This repository contains a comprehensive benchmark dataset and analysis of website performance for Greek news portals. We analyze key metrics such as median load time, 90th percentile load time, average load time, total data size, and request count to evaluate user experience and site efficiency.

## Dataset

- **greek_news_sites_benchmark_results.csv**: Raw benchmark data collected from multiple Greek news websites, including the following columns:
  - `site`: Domain name of the news site.
  - `average_load_ms`: Average page load time in milliseconds.
  - `median_load_ms`: Median page load time reflecting typical user experience.
  - `p90_load_ms`: 90th percentile load time indicating tail latency for slower users.
  - `total_data_bytes`: Total amount of data loaded per page in bytes.
  - `request_count`: Number of requests made to load the page.

## Analysis & Visualizations

- **Performance quadrant charts** separating sites by median and 90th percentile load time.
- Visualizations incorporating load size categories to highlight “heavy” pages that may impact speed.
- Insights on top-performing sites delivering fast and consistent experiences.
- Identification of potential bottlenecks caused by large data payloads.

## Usage

- Load the CSV dataset in Python or your preferred data tool for exploration.
- Use provided Python visualization scripts to generate quadrant plots with optional load size indicators.
- Customize bins, colors, and other parameters as needed to fit your analysis.

## How to Run

1. Clone this repository.
2. Install the required Python libraries (e.g., pandas, matplotlib).
3. Run the analysis and visualization scripts using the dataset CSV file.
4. Modify parameters or data paths if necessary.

## Contributing

Contributions are welcome! Feel free to fork the repo, make changes, and submit pull requests with improvements, additional analyses, or updated data.

## License

This project is provided for informational and educational purposes. See LICENSE for details.

---

*For questions or support, please open an issue in this repository.*
