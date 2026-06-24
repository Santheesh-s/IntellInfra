# IntellInfra

> "A GIS-Integrated NLP-Driven Explainable Al Framework for Intelligent Hardware Asset Management and Operating System Optimization." 

IntellInfra is an intelligent, GIS-enabled Progressive Web App (PWA) designed to help organizations manage computer infrastructure and make informed deployment decisions. Unlike conventional asset management systems, this platform combines Geographic Information Systems (GIS), Natural Language Processing (NLP), Explainable Artificial Intelligence (XAI), and decision-support algorithms to provide intelligent recommendations and transparent infrastructure insights.

---

## 🌟 High-Level Overview

The system allows administrators to interact with the platform using natural language queries instead of manual filtering. For example:
* *"Show all computers in Block C that cannot run Windows 11."* 
* *"Recommend the best operating system for the systems in the Programming Lab."* 

The NLP engine interprets the request, the GIS component identifies the relevant hardware assets on a digital campus map, and the XAI recommendation engine evaluates each system against operating system requirements and organizational needs.

The result is an interactive decision-support platform that not only recommends the most suitable operating systems but also visually displays affected systems on a GIS map and transparently explains the reasoning behind every recommendation.

---

## 🏗️ The Tech Stack (Full Python Architecture)

This architecture utilizes a unified Python backend to seamlessly connect web routing, spatial querying, and complex AI operations into a single robust application.

**Frontend (The User Interface)**
* HTML, CSS, JavaScript .
* Progressive Web App (PWA).
* Interactive dashboards and charts .
* GIS-enabled map visualization (Leaflet.js / ArcGIS) .

**Backend & Intelligence Layer (Python)**
* **Framework:** FastAPI / Django (Handling REST APIs and routing)
* **NLP Processing Engine:** spaCy / HuggingFace (Intent Classification & Entity Extraction)
* **Recommendation Engine:** Scikit-Learn / XGBoost (Multi-Criteria Decision Making)
* **Explainable AI Engine:** SHAP (Shapley Additive Explanations) .
* **Spatial Routing:** GeoAlchemy / SQLAlchemy

**Database Layer**
* PostgreSQL .
* PostGIS Extension .
* Databases: Asset inventory, OS requirements, and Hardware compatibility .

---

## ⚙️ The Complete System Flow

1. **Natural Language Interaction:** The administrator enters a natural language request.
2. **NLP-Based Query Understanding:** The NLP module performs Intent Classification and Entity Extraction . The backend converts these entities into structured database and GIS queries.
3. **GIS-Based Asset Resolution:** The GIS engine queries the database and identifies every computer located within the requested spatial region on the campus map.
4. **Hardware Analysis:** Multi-Criteria Decision Making (MCDM) techniques evaluate hardware compatibility, security requirements, and organizational policies.
5. **Explainable AI Decision Engine:** The XAI engine generates a compatibility score and explains every decision using feature importance values (e.g., deducting percentages for RAM limitations or TPM absence).
6. **GIS Visualization:** Results are displayed on the campus GIS map, utilizing interactive heatmaps to highlight compatible systems, upgrade priorities, and security vulnerability hotspots.

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
