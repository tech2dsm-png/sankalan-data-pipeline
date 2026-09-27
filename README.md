Website Analytics Data Engineering Project

This is a website analytics project I built to get hands-on experience with Data Engineering using a real website.

I built the project in two parts. First, I worked with website data using GTM, GA4 and BigQuery for batch analytics. Later, I built a local real-time streaming pipeline using FastAPI, Kafka, Spark and PostgreSQL.

The project also has a Streamlit dashboard for viewing and analyzing the data.

Batch Analytics

The batch pipeline is:

Website → GTM → GA4 → BigQuery → Streamlit

GTM and GA4 collect website activity, and the data is stored in BigQuery.

I use SQL in BigQuery to prepare and analyze the data. The results are shown in the Streamlit dashboard.

The dashboard covers:

Website traffic
Top pages
Devices
Browsers
Traffic sources
User segments
Other website activity
Real-Time Streaming

I also built a local real-time version of the website analytics pipeline.

The flow is:

Website → FastAPI → Kafka → Spark → PostgreSQL → Streamlit

FastAPI receives website events.

Kafka handles the event stream.

Spark processes the streaming data.

PostgreSQL stores the processed data.

The Streamlit dashboard is used to view and analyze the processed data.

The real-time pipeline runs locally on my laptop using Docker.

Project Structure
sankalan-data-pipeline/
│
├── website/
├── dashboard/
├── data-engineering/
│   ├── api/
│   ├── kafka/
│   ├── postgres/
│   ├── spark/
│   ├── scripts/
│   └── docker-compose.yml
│
├── database/
├── Docs/
├── shared/
├── tests/
├── requirements.txt
└── README.md
Technologies Used
Batch Analytics
Google Tag Manager (GTM)
Google Analytics 4 (GA4)
BigQuery
SQL
Real-Time Streaming
Python
FastAPI
Apache Kafka
Apache Spark
PostgreSQL
Docker
Dashboard
Streamlit
What I Worked On

While building the project, I worked on:

Collecting website events
Data preparation and transformation
SQL queries and analysis
Batch processing
Real-time stream processing
REST APIs
Kafka
Spark
PostgreSQL
BigQuery
Streamlit dashboards
Docker
Testing
Running the Project Locally

The real-time pipeline runs locally using Docker.

From the project folder:

D:
cd \sankalan-data-pipeline

Activate the Python environment:

venv\Scripts\activate

Go to the Data Engineering folder:

cd data-engineering

Start the services:

docker compose up -d

Check the running services:

docker compose ps

The FastAPI application is in the api folder, and the Streamlit dashboard is in the dashboard folder.

The project also contains scripts and documentation for running the individual components.

To stop the Docker services:

docker compose down
Why I Built This Project

I wanted to learn Data Engineering by building and running a project instead of only studying individual technologies.

I started with website analytics using GTM, GA4 and BigQuery. After that, I built a local streaming version using FastAPI, Kafka, Spark and PostgreSQL.

Building both versions helped me understand how the same type of website data can be handled through batch processing as well as real-time streaming.

I continue to improve the project as I learn and work with more Data Engineering concepts.