# CrowdCargo - Community-Powered Ordering & Shipping Platform

## Overview
CrowdCargo is a web-based platform that enables community-based ordering and shipping of goods, particularly focused on Indian products for diaspora communities abroad. The platform aggregates individual orders into group shipments to reduce shipping costs.

## Features
- 🛒 User Order Interface
- ⚖️ Order Aggregation Engine
- 📦 Shipping Plan Selector
- 📊 Live Shipment Tracker
- 🔐 User Account Management

## Tech Stack
- Frontend: Streamlit
- Backend: MongoDB Atlas
- Hosting: Streamlit Community Cloud
- Optional: Twilio/SMTP for notifications

## Setup Instructions

### Prerequisites
- Python 3.8+
- MongoDB Atlas account
- Streamlit account

### Installation
1. Clone the repository:
```bash
git clone https://github.com/yourusername/crowdcargo.git
cd crowdcargo
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
MONGO_URI=your_mongodb_uri
```

### Running the Application
```bash
streamlit run app.py
```

## Project Structure
```
crowdcargo/
├── app.py                 # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                  # Environment variables
├── src/
│   ├── models/           # Data models
│   ├── services/         # Business logic
│   ├── utils/            # Utility functions
│   └── config.py         # Configuration settings
└── tests/                # Test files
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License
MIT License

## Contact
For questions or support, please open an issue in the repository.