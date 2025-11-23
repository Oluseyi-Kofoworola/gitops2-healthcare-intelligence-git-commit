# filepath: tests/load/locustfile.py
"""
Locust Load Testing Configuration for GitOps 2.0 Healthcare Platform

Usage:
    locust -f tests/load/locustfile.py --host=http://localhost:8080

Scenarios:
- Authentication load testing
- Payment transaction processing
- PHI encryption/decryption
- Medical device monitoring
- Synthetic data generation
"""

import json
import time
import random
from locust import HttpUser, task, between, SequentialTaskSet


class HealthcareWorkflow(SequentialTaskSet):
    """Sequential workflow simulating a complete healthcare interaction"""
    
    def __init__(self, parent):
        super().__init__(parent)
        self.token = None
        self.patient_id = None
        self.device_id = None
        self.encrypted_data = None
        self.key_id = None
    
    @task
    def authenticate(self):
        """Step 1: Authenticate healthcare provider"""
        response = self.client.post(
            "http://localhost:8080/api/v1/login",
            json={
                "username": "admin",
                "password": "admin123"
            },
            name="Auth: Login"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.token = data.get("token")
    
    @task
    def generate_patient(self):
        """Step 2: Generate synthetic patient data"""
        response = self.client.get(
            "http://localhost:8085/api/v1/generate/patient",
            name="Synthetic: Generate Patient"
        )
        
        if response.status_code == 200:
            patient = response.json()
            self.patient_id = f"PT-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
    
    @task
    def encrypt_phi(self):
        """Step 3: Encrypt patient PHI"""
        if not self.patient_id:
            return
        
        response = self.client.post(
            "http://localhost:8083/api/v1/phi/encrypt",
            json={
                "data": f"Patient medical record for {self.patient_id}",
                "patient_id": self.patient_id,
                "data_type": "medical_record"
            },
            name="PHI: Encrypt"
        )
        
        if response.status_code == 200:
            data = response.json()
            self.encrypted_data = data.get("encrypted_data")
            self.key_id = data.get("key_id")
    
    @task
    def register_device(self):
        """Step 4: Register medical device"""
        if not self.patient_id:
            return
        
        self.device_id = f"DEVICE-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        self.client.post(
            "http://localhost:8084/api/v1/devices",
            json={
                "device_id": self.device_id,
                "device_type": random.choice(["MRI", "CT_Scanner", "X-Ray", "ECG"]),
                "manufacturer": "Siemens",
                "model": "Test Model",
                "serial_number": f"SN-{self.device_id}",
                "location": "ICU-Floor-2",
                "status": "active"
            },
            name="Device: Register"
        )
    
    @task
    def update_device_metrics(self):
        """Step 5: Update device metrics"""
        if not self.device_id:
            return
        
        self.client.post(
            f"http://localhost:8084/api/v1/devices/{self.device_id}/metrics",
            json={
                "temperature": random.uniform(20.0, 25.0),
                "power_usage": random.uniform(10.0, 20.0),
                "cpu_usage": random.uniform(30.0, 70.0),
                "memory_usage": random.uniform(40.0, 80.0),
                "network_rx": random.randint(100000, 1000000),
                "network_tx": random.randint(50000, 500000)
            },
            name="Device: Update Metrics"
        )
    
    @task
    def process_payment(self):
        """Step 6: Process payment transaction"""
        if not self.token or not self.patient_id:
            return
        
        self.client.post(
            "http://localhost:8081/api/v1/transactions",
            json={
                "amount": random.uniform(100.0, 5000.0),
                "currency": "USD",
                "patient_id": self.patient_id,
                "transaction_id": f"TXN-{int(time.time() * 1000)}",
                "payment_method": random.choice(["credit_card", "insurance", "debit_card"]),
                "compliance_tags": {
                    "hipaa": "true",
                    "encrypted_phi": self.key_id or "N/A"
                }
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="Payment: Process Transaction"
        )


class AuthServiceUser(HttpUser):
    """Load test user focusing on authentication service"""
    wait_time = between(1, 3)
    host = "http://localhost:8080"
    
    @task(10)
    def login(self):
        """Simulate user login"""
        self.client.post(
            "/api/v1/login",
            json={
                "username": f"user{random.randint(1, 100)}",
                "password": "password123"
            },
            name="Auth: Login"
        )
    
    @task(5)
    def health_check(self):
        """Check service health"""
        self.client.get("/health", name="Auth: Health")
    
    @task(2)
    def metrics(self):
        """Fetch Prometheus metrics"""
        self.client.get("/metrics", name="Auth: Metrics")


class PaymentGatewayUser(HttpUser):
    """Load test user focusing on payment gateway"""
    wait_time = between(2, 5)
    host = "http://localhost:8081"
    
    def on_start(self):
        """Get authentication token"""
        response = self.client.post(
            "http://localhost:8080/api/v1/login",
            json={"username": "admin", "password": "admin123"}
        )
        if response.status_code == 200:
            self.token = response.json().get("token")
        else:
            self.token = None
    
    @task(10)
    def create_transaction(self):
        """Create payment transaction"""
        if not self.token:
            return
        
        self.client.post(
            "/api/v1/transactions",
            json={
                "amount": random.uniform(50.0, 2000.0),
                "currency": "USD",
                "patient_id": f"PT-{random.randint(1000, 9999)}",
                "transaction_id": f"TXN-{int(time.time() * 1000)}",
                "payment_method": random.choice(["credit_card", "insurance", "cash"])
            },
            headers={"Authorization": f"Bearer {self.token}"},
            name="Payment: Create Transaction"
        )
    
    @task(5)
    def list_transactions(self):
        """List transactions"""
        if not self.token:
            return
        
        self.client.get(
            "/api/v1/transactions",
            headers={"Authorization": f"Bearer {self.token}"},
            name="Payment: List Transactions"
        )
    
    @task(2)
    def health_check(self):
        """Check service health"""
        self.client.get("/health", name="Payment: Health")


class PHIServiceUser(HttpUser):
    """Load test user focusing on PHI encryption service"""
    wait_time = between(1, 2)
    host = "http://localhost:8083"
    
    @task(10)
    def encrypt_phi(self):
        """Encrypt PHI data"""
        self.client.post(
            "/api/v1/phi/encrypt",
            json={
                "data": f"Patient SSN: {random.randint(100000000, 999999999)}",
                "patient_id": f"PT-{random.randint(1000, 9999)}",
                "data_type": "demographics"
            },
            name="PHI: Encrypt"
        )
    
    @task(5)
    def anonymize_phi(self):
        """Anonymize PHI data"""
        self.client.post(
            "/api/v1/phi/anonymize",
            json={
                "data": f"Patient Name: John Doe, SSN: {random.randint(100000000, 999999999)}",
                "patient_id": f"PT-{random.randint(1000, 9999)}"
            },
            name="PHI: Anonymize"
        )
    
    @task(2)
    def health_check(self):
        """Check service health"""
        self.client.get("/health", name="PHI: Health")


class MedicalDeviceUser(HttpUser):
    """Load test user focusing on medical device service"""
    wait_time = between(2, 4)
    host = "http://localhost:8084"
    
    @task(10)
    def register_device(self):
        """Register new medical device"""
        device_id = f"DEVICE-{int(time.time() * 1000)}-{random.randint(1000, 9999)}"
        
        self.client.post(
            "/api/v1/devices",
            json={
                "device_id": device_id,
                "device_type": random.choice(["MRI", "CT_Scanner", "X-Ray", "ECG", "Ventilator"]),
                "manufacturer": random.choice(["Siemens", "GE Healthcare", "Philips"]),
                "model": f"Model-{random.randint(100, 999)}",
                "serial_number": f"SN-{device_id}",
                "location": f"Floor-{random.randint(1, 5)}",
                "status": "active"
            },
            name="Device: Register"
        )
    
    @task(15)
    def update_metrics(self):
        """Update device metrics"""
        # Use a device from the simulator
        device_id = random.choice(["MRI-001", "CT-001", "XRAY-001"])
        
        self.client.post(
            f"/api/v1/devices/{device_id}/metrics",
            json={
                "temperature": random.uniform(20.0, 25.0),
                "power_usage": random.uniform(10.0, 20.0),
                "cpu_usage": random.uniform(30.0, 70.0),
                "memory_usage": random.uniform(40.0, 80.0),
                "network_rx": random.randint(100000, 1000000),
                "network_tx": random.randint(50000, 500000)
            },
            name="Device: Update Metrics"
        )
    
    @task(5)
    def list_devices(self):
        """List all devices"""
        self.client.get("/api/v1/devices", name="Device: List")
    
    @task(2)
    def health_check(self):
        """Check service health"""
        self.client.get("/health", name="Device: Health")


class SyntheticPHIUser(HttpUser):
    """Load test user focusing on synthetic PHI generation"""
    wait_time = between(1, 3)
    host = "http://localhost:8085"
    
    @task(10)
    def generate_patient(self):
        """Generate synthetic patient"""
        self.client.get("/api/v1/generate/patient", name="Synthetic: Patient")
    
    @task(5)
    def generate_batch(self):
        """Generate batch of patients"""
        self.client.get(
            f"/api/v1/generate/batch?count={random.randint(5, 20)}",
            name="Synthetic: Batch"
        )
    
    @task(2)
    def health_check(self):
        """Check service health"""
        self.client.get("/health", name="Synthetic: Health")


class CompleteWorkflowUser(HttpUser):
    """User simulating complete healthcare workflow"""
    wait_time = between(3, 7)
    tasks = [HealthcareWorkflow]
    host = "http://localhost:8080"
