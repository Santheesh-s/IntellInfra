# IntellInfra

> [cite_start]"A GIS-Integrated NLP-Driven Explainable Al Framework for Intelligent Hardware Asset Management and Operating System Optimization." [cite: 4]

[cite_start]IntellInfra is an intelligent, GIS-enabled Progressive Web App (PWA) designed to help organizations manage computer infrastructure and make informed deployment decisions[cite: 6, 18]. [cite_start]Unlike conventional asset management systems, this platform combines Geographic Information Systems (GIS), Natural Language Processing (NLP), Explainable Artificial Intelligence (XAI), and decision-support algorithms to provide intelligent recommendations and transparent infrastructure insights[cite: 7].

---

## 🌟 High-Level Overview

[cite_start]The system allows administrators to interact with the platform using natural language queries instead of manual filtering[cite: 8, 127]. For example:
* [cite_start]*"Show all computers in Block C that cannot run Windows 11."* [cite: 9]
* [cite_start]*"Recommend the best operating system for the systems in the Programming Lab."* [cite: 11]

[cite_start]The NLP engine interprets the request, the GIS component identifies the relevant hardware assets on a digital campus map, and the XAI recommendation engine evaluates each system against operating system requirements and organizational needs[cite: 12]. 

[cite_start]The result is an interactive decision-support platform that not only recommends the most suitable operating systems but also visually displays affected systems on a GIS map and transparently explains the reasoning behind every recommendation[cite: 13].

---

## 🏗️ The Tech Stack (Full Python Architecture)

This architecture utilizes a unified Python backend to seamlessly connect web routing, spatial querying, and complex AI operations into a single robust application.

**Frontend (The User Interface)**
* [cite_start]HTML, CSS, JavaScript [cite: 17]
* [cite_start]Progressive Web App (PWA) [cite: 18]
* [cite_start]Interactive dashboards and charts [cite: 19, 21]
* [cite_start]GIS-enabled map visualization (Leaflet.js / ArcGIS) [cite: 20]

**Backend & Intelligence Layer (Python)**
* **Framework:** FastAPI / Django (Handling REST APIs and routing)
* **NLP Processing Engine:** spaCy / HuggingFace (Intent Classification & Entity Extraction)
* **Recommendation Engine:** Scikit-Learn / XGBoost (Multi-Criteria Decision Making)
* [cite_start]**Explainable AI Engine:** SHAP (Shapley Additive Explanations) [cite: 110]
* **Spatial Routing:** GeoAlchemy / SQLAlchemy

**Database Layer**
* [cite_start]PostgreSQL [cite: 32]
* [cite_start]PostGIS Extension [cite: 33]
* [cite_start]Databases: Asset inventory, OS requirements, and Hardware compatibility [cite: 34, 35, 36]

---

## ⚙️ The Complete System Flow

1. [cite_start]**Natural Language Interaction:** The administrator enters a natural language request[cite: 46].
2. [cite_start]**NLP-Based Query Understanding:** The NLP module performs Intent Classification and Entity Extraction[cite: 55]. [cite_start]The backend converts these entities into structured database and GIS queries[cite: 63].
3. [cite_start]**GIS-Based Asset Resolution:** The GIS engine queries the database and identifies every computer located within the requested spatial region on the campus map[cite: 65, 78].
4. [cite_start]**Hardware Analysis:** Multi-Criteria Decision Making (MCDM) techniques evaluate hardware compatibility, security requirements, and organizational policies[cite: 91, 92, 94, 95].
5. [cite_start]**Explainable AI Decision Engine:** The XAI engine generates a compatibility score and explains every decision using feature importance values (e.g., deducting percentages for RAM limitations or TPM absence)[cite: 99, 100, 102, 104, 110].
6. [cite_start]**GIS Visualization:** Results are displayed on the campus GIS map, utilizing interactive heatmaps to highlight compatible systems, upgrade priorities, and security vulnerability hotspots[cite: 114, 116, 120, 123, 124].

---

## 🚀 Local Development Setup

This project is optimized for Linux-based development environments (tested on Lubuntu). 

### Prerequisites
* Python 3.10+
* PostgreSQL with PostGIS extension installed
* Git

### Installation Steps

**1. Clone the repository**
Bash
```
git clone [https://github.com/yourusername/IntellInfra.git](https://github.com/yourusername/IntellInfra.git)
cd IntellInfra
```

**2. Set up the Python Virtual Environment**

Bash
```
python3 -m venv venv
source venv/bin/activate
```

**3. Install Dependencies**
Bash
```
pip install -r requirements.txt
```

**4. Database Configuration**
Ensure PostgreSQL is running locally. Create a new database and enable the PostGIS extension:
```
SQL
CREATE DATABASE intellinfra_db;
\c intellinfra_db
CREATE EXTENSION postgis;
Update your .env file with the correct database credentials.
```

**5. Run the Development Server**
Bash
```uvicorn main:app --reload```
