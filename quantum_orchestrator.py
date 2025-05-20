"""
Quantum Orchestrator - IBM Quantum Integration for BumBot Trading

This module provides optimized quantum circuit execution for trading signal generation
with built-in cost optimization and resource management.
"""
from qiskit import QuantumCircuit, transpile
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Options
from dotenv import load_dotenv
import os
import time
import json
import logging
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/quantum.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('quantum')

class QuantumOrchestrator:
    """Manages quantum task routing, execution and cost optimization"""
    
    def __init__(self):
        load_dotenv()
        self.providers = {
            "ibm": {
                "token": os.getenv("IBM_QUANTUM_TOKEN"),
                "available": True,
                "cost_per_hour": 0.0,  # Free tier
                "max_qubits": 127,
                "queue_time_mins": 5
            }
        }
        
        # Initialize usage tracking
        self.usage = {provider: {"credits": 0, "jobs": 0} for provider in self.providers}
        
        # Cache for IBM Quantum service
        self._ibm_service = None
        
        # Job history for optimization
        self.job_history = []
        
        # Save usage data to file
        self._init_usage_tracking()
        
    def _init_usage_tracking(self):
        """Initialize usage tracking from file if exists"""
        usage_file = 'logs/quantum_usage.json'
        if os.path.exists(usage_file):
            try:
                with open(usage_file, 'r') as f:
                    self.usage = json.load(f)
                logger.info(f"Loaded usage data from {usage_file}")
            except Exception as e:
                logger.error(f"Error loading usage data: {str(e)}")
        
    def _save_usage(self):
        """Save usage data to file"""
        try:
            with open('logs/quantum_usage.json', 'w') as f:
                json.dump(self.usage, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving usage data: {str(e)}")
    
    def _get_ibm_service(self):
        """Get or initialize IBM Quantum service"""
        if self._ibm_service is None:
            token = self.providers["ibm"]["token"]
            if not token:
                raise ValueError("No IBM Quantum token found")
                
            logger.info("Initializing IBM Quantum service")
            self._ibm_service = QiskitRuntimeService(channel="ibm_quantum", token=token)
            
        return self._ibm_service
    
    def select_provider(self, circuit_size, urgency=0.5, budget=1.0):
        """Select optimal quantum provider based on circuit and parameters"""
        # Currently only IBM is available, but this function is designed
        # to accommodate future quantum providers (Google, AWS, etc.)
        return "ibm"
    
    def _select_ibm_backend(self, circuit_qubits, simulator_allowed=True):
        """Select appropriate IBM Quantum backend"""
        service = self._get_ibm_service()
        backends = service.backends()
        
        if not backends:
            raise ValueError("No backends available for this account")
            
        # Filter for specific criteria
        suitable_backends = []
        
        for backend in backends:
            # Skip if simulator is not allowed and backend is a simulator
            if not simulator_allowed and 'simulator' in backend.name.lower():
                continue
                
            # Check if backend has enough qubits
            # This simplified check would need more detailed constraints in production
            suitable_backends.append(backend)
            
        if not suitable_backends:
            if simulator_allowed:
                raise ValueError(f"No backends with {circuit_qubits} qubits available")
            else:
                # Try again but allow simulators
                return self._select_ibm_backend(circuit_qubits, True)
                
        # For now, just return the first suitable backend
        # In production, would implement more sophisticated selection
        return suitable_backends[0]
    
    def execute_circuit(self, circuit, shots=1000, simulator_allowed=True):
        """Execute quantum circuit and return results"""
        try:
            # Select the backend
            backend = self._select_ibm_backend(circuit.num_qubits, simulator_allowed)
            logger.info(f"Selected backend: {backend.name}")
            
            # Configure execution options - handle different API versions
            try:
                # Try newer Options API format
                options = Options()
                try:
                    # First try execution.shots (older format)
                    options.execution = {"shots": shots}
                except (AttributeError, TypeError):
                    try:
                        # Then try direct dictionary assignment
                        options = {"shots": shots}
                    except Exception:
                        # Finally try the newest format with resilience
                        options = Options(resilience_level=1)
                        options.update({"shots": shots})
                        
                logger.info(f"Configured quantum execution with {shots} shots")
            except Exception as e:
                logger.warning(f"Error configuring options: {str(e)}")
                # Fall back to default options
                options = None
            
            # Submit job to IBM
            service = self._get_ibm_service()
            
            try:
                # Try different ways to initialize Sampler based on API version
                if options is None:
                    sampler = Sampler(backend=backend)
                else:
                    sampler = Sampler(backend=backend, options=options)
                    
                # Handle different run API patterns
                try:
                    # Newer versions require list of circuits
                    job = sampler.run([circuit])
                    logger.info("Using new Sampler API with circuit list")
                except TypeError:
                    try:
                        # Older versions might use different patterns
                        job = sampler.run(circuit)
                        logger.info("Using old Sampler API with single circuit")
                    except Exception as e2:
                        logger.error(f"Error running sampler with single circuit: {str(e2)}")
                        raise
            except Exception as e:
                logger.error(f"Error initializing Sampler: {str(e)}")
                raise
            job_id = job.job_id()
            
            logger.info(f"Submitted job {job_id} to {backend.name}")
            
            # Monitor job status
            status = job.status()
            logger.info(f"Initial status: {status}")
            
            start_time = datetime.now()
            while status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
                time.sleep(5)
                status = job.status()
                # Log status changes
                elapsed = (datetime.now() - start_time).total_seconds()
                logger.info(f"Job {job_id} status after {elapsed:.1f}s: {status}")
                
                # Timeout after 10 minutes
                if elapsed > 600:
                    logger.warning(f"Job {job_id} timed out after 10 minutes")
                    break
            
            # Process results if job completed
            if status == 'COMPLETED':
                result = job.result()
                quasi_dists = result.quasi_dists[0]
                
                # Update usage stats
                self.usage["ibm"]["jobs"] += 1
                self._save_usage()
                
                # Save job history
                self.job_history.append({
                    "job_id": job_id,
                    "backend": backend.name,
                    "circuit_qubits": circuit.num_qubits,
                    "shots": shots,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                })
                
                # Return execution results
                return {
                    "provider": "ibm",
                    "backend": backend.name,
                    "probabilities": quasi_dists,
                    "job_id": job_id,
                    "execution_time": (datetime.now() - start_time).total_seconds(),
                    "timestamp": datetime.now().isoformat()
                }
            else:
                error_msg = f"Job failed with status: {status}"
                logger.error(error_msg)
                return {"error": error_msg, "job_id": job_id}
                
        except Exception as e:
            logger.error(f"Error executing quantum circuit: {str(e)}")
            return {"error": str(e)}
            
    def create_bell_circuit(self):
        """Create a simple Bell state circuit"""
        qc = QuantumCircuit(2)
        qc.h(0)
        qc.cx(0, 1)
        qc.measure_all()
        return qc
    
    def create_momentum_circuit(self, trend_value, volatility_value):
        """Create momentum-based trading circuit parametrized by trend and volatility"""
        import numpy as np
        
        # Create a 3-qubit circuit for trend, volatility, and prediction
        qc = QuantumCircuit(3)
        
        # Encode market trend in first qubit using rotation
        trend_angle = np.pi * trend_value  # Scale between 0 and π
        qc.rx(trend_angle, 0)
        
        # Encode volatility in second qubit
        volatility_angle = np.pi * volatility_value  # Scale between 0 and π
        qc.ry(volatility_angle, 1)
        
        # Create entanglement between qubits
        qc.cx(0, 1)
        qc.cx(1, 2)
        
        # Apply Hadamard to create superposition in prediction qubit
        qc.h(2)
        
        # Measure all qubits
        qc.measure_all()
        
        return qc
    
    def create_price_prediction_circuit(self, historical_data):
        """
        Create quantum circuit for price prediction based on historical data
        
        Args:
            historical_data: List of normalized price movements (-1 to 1 scale)
        """
        import numpy as np
        
        # Number of data points to encode (use most recent)
        n_points = min(4, len(historical_data))
        data = historical_data[-n_points:]
        
        # Create circuit with qubits for each data point plus one for output
        n_qubits = n_points + 1
        qc = QuantumCircuit(n_qubits)
        
        # Encode historical data points using rotation gates
        for i, value in enumerate(data):
            # Scale values to rotation angles
            angle = np.pi * (value + 1) / 2  # Scale from -1...1 to 0...π
            qc.ry(angle, i)
        
        # Create entanglement pattern (simplistic model)
        for i in range(n_points):
            qc.cx(i, n_points)
        
        # Add some interference
        qc.h(n_points)
        
        # Measure only the prediction qubit
        qc.measure(n_points, 0)
        
        return qc
        
    def interpret_momentum_results(self, result):
        """Interpret results from momentum circuit for trading signals"""
        if not result or "error" in result:
            return {"error": "Invalid quantum result"}
            
        probabilities = result.get("probabilities", {})
        
        # Analyze measurement outcomes
        # For 3 qubits: states |000⟩ and |111⟩ indicate strong signals
        # States are represented as strings of their decimal values
        
        # Strong uptrend signals: |000⟩ and |111⟩ (0 and 7)
        buy_signal = probabilities.get("0", 0) + probabilities.get("7", 0)
        
        # Strong downtrend signals: |011⟩ and |100⟩ (3 and 4)
        sell_signal = probabilities.get("3", 0) + probabilities.get("4", 0)
        
        # Other states suggest holding
        hold_signal = 1.0 - buy_signal - sell_signal
        
        return {
            "buy": buy_signal,
            "sell": sell_signal,
            "hold": hold_signal,
            "recommended_action": "BUY" if buy_signal > 0.5 else "SELL" if sell_signal > 0.5 else "HOLD",
            "confidence": max(buy_signal, sell_signal, hold_signal),
            "quantum_result": result
        }

# Simple test function
if __name__ == "__main__":
    orchestrator = QuantumOrchestrator()
    print("Creating Bell circuit...")
    bell_circuit = orchestrator.create_bell_circuit()
    print("Executing quantum circuit (this may take a few minutes)...")
    result = orchestrator.execute_circuit(bell_circuit)
    print(f"Result: {json.dumps(result, indent=2)}")
