import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    URL_LOGIN = "https://erp.integrens.com:4001/dacta.portalweb/Base/pages/bas/wf_login.html"
    
    # Credentials
    USER = os.getenv("INTEGRENS_USER")
    PASS = os.getenv("INTEGRENS_PASS")
    
    # Paths
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    OUTPUT_DIR = os.path.join(BASE_DIR, "outputs")
    LOG_DIR = os.path.join(OUTPUT_DIR, "logs")
    EVIDENCE_DIR = os.path.join(OUTPUT_DIR, "evidence")
    
    # Ensure directories exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    os.makedirs(LOG_DIR, exist_ok=True)
    os.makedirs(EVIDENCE_DIR, exist_ok=True)

    @staticmethod
    def validate_config():
        if not Config.USER or not Config.PASS:
            raise ValueError("Missing credentials! Please create a .env file with INTEGRENS_USER and INTEGRENS_PASS.")
