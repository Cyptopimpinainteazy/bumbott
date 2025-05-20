from qiskit import QuantumCircuit
from qiskit_ibm_runtime import QiskitRuntimeService, Sampler, Options
from datetime import datetime
from dotenv import load_dotenv
import os
import time

load_dotenv()

def quantum_trading_signal():
    # Connect using auth token from .env file
    token = os.getenv("IBM_QUANTUM_TOKEN")
    if not token:
        raise ValueError("No IBM_QUANTUM_TOKEN found in .env file")
        
    print("Authenticating with IBM Quantum...")
    service = QiskitRuntimeService(channel="ibm_quantum", token=token)
    
    # Create Bell state circuit
    print("Creating quantum circuit...")
    qc = QuantumCircuit(2)
    qc.h(0)
    qc.cx(0,1)
    qc.measure_all()
    
    try:
        # Find available backend
        print("Finding available quantum computer...")
        backends = service.backends()
        print(f"Available backends: {[b.name for b in backends]}")
        
        # Select appropriate backend
        if not backends:
            raise ValueError("No backends available for this account")
            
        # Try to find a simulator first
        simulator_backends = [b for b in backends if 'simulator' in b.name.lower()]
        if simulator_backends:
            backend = simulator_backends[0]
        else:
            # Fall back to any available backend
            backend = backends[0]
            
        print(f"Selected backend: {backend.name}")
        
        # Configure execution options
        options = Options()
        options.shots = 1000  # Direct assignment of shots
        
        # Submit and monitor job
        print("Submitting quantum job...")
        job = Sampler(backend=backend, options=options).run([qc])  # Note: circuit wrapped in list
        job_id = job.job_id()
        print(f"Job ID: {job_id}")
        
        # Monitor job status
        status = job.status()
        print(f"Initial status: {status}")
        
        while status not in ['COMPLETED', 'FAILED', 'CANCELLED']:
            time.sleep(5)
            status = job.status()
            print(f"Current status: {status}")
        
        if status == 'COMPLETED':
            # Process results
            result = job.result()
            quasi_dists = result.quasi_dists[0]
            print("Quantum calculation complete!")
            
            return {
                'probabilities': quasi_dists,
                'backend': backend.name,
                'timestamp': datetime.now().isoformat(),
                'job_id': job_id
            }
        else:
            return {
                'error': f"Job failed with status: {status}",
                'job_id': job_id
            }
            
    except Exception as e:
        print(f"Error running quantum job: {str(e)}")
        return {'error': str(e)}

if __name__ == "__main__":
    print("Starting quantum trading analysis...")
    result = quantum_trading_signal()
    print("\nQUANTUM RESULT:")
    print(result)
