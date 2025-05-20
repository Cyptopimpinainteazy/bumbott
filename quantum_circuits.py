"""
Quantum Trading Circuits - Advanced Pattern Detection Module

This module provides specialized quantum circuits designed to detect and predict
various market patterns using quantum computing principles.
"""
from qiskit import QuantumCircuit, QuantumRegister, ClassicalRegister
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('logs/quantum_circuits.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('quantum_circuits')

class QuantumTradingCircuits:
    """Collection of quantum circuits optimized for different trading patterns"""
    
    @staticmethod
    def encode_price_data(price_data, num_qubits=4):
        """
        Encode normalized price data into quantum amplitudes
        
        Args:
            price_data: List of normalized price points (-1 to 1 range)
            num_qubits: Number of qubits to use for encoding
            
        Returns:
            QuantumCircuit with encoded price data
        """
        if len(price_data) > 2**num_qubits:
            logger.warning(f"Data truncated: {len(price_data)} points > {2**num_qubits} capacity")
            price_data = price_data[-(2**num_qubits):]
            
        # Create circuit
        qc = QuantumCircuit(num_qubits)
        
        # Normalize if not already in -1 to 1 range
        if max(price_data) > 1 or min(price_data) < -1:
            max_val = max(max(price_data), abs(min(price_data)))
            price_data = [p/max_val for p in price_data]
        
        # Encode each price point
        for i, price in enumerate(price_data):
            if i >= num_qubits:
                break
                
            # Map from -1,1 to 0,π for rotation angle
            angle = (price + 1) * np.pi/2
            qc.ry(angle, i)
            
        return qc
    
    @staticmethod
    def mean_reversion_circuit(overbought_probability, volatility=0.5, num_qubits=3):
        """
        Create circuit for mean-reversion strategy
        
        Args:
            overbought_probability: Float between 0-1 indicating overbought condition
            volatility: Market volatility normalized between 0-1
            num_qubits: Number of qubits to use
        
        Returns:
            QuantumCircuit for mean reversion analysis
        """
        # Create quantum and classical registers
        qr = QuantumRegister(num_qubits, 'q')
        cr = ClassicalRegister(num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Encode overbought condition in first qubit
        # High value = overbought, Low value = oversold
        overbought_angle = overbought_probability * np.pi
        qc.ry(overbought_angle, 0)
        
        # Encode volatility in second qubit
        # Higher volatility increases probability of mean reversion
        volatility_angle = volatility * np.pi
        qc.ry(volatility_angle, 1)
        
        # Create entanglement
        qc.cx(0, 1)  # Correlation between overbought and volatility
        
        # Add interference for market regime detection
        qc.h(2)
        qc.cx(1, 2)
        qc.t(2)
        qc.cx(0, 2)
        qc.tdg(2)
        qc.cx(1, 2)
        qc.h(2)  # Interference pattern to detect regime
        
        # Measure all qubits
        qc.measure(range(num_qubits), range(num_qubits))
        
        return qc
    
    @staticmethod
    def momentum_circuit(trend_strength, volatility, recent_divergence=0, num_qubits=4):
        """
        Create circuit for momentum/trend following strategy
        
        Args:
            trend_strength: Float between -1 and 1 (negative=downtrend, positive=uptrend)
            volatility: Market volatility normalized between 0-1
            recent_divergence: Divergence from trend (-1 to 1, 0=no divergence)
            num_qubits: Number of qubits to use
            
        Returns:
            QuantumCircuit for momentum analysis
        """
        qr = QuantumRegister(num_qubits, 'q')
        cr = ClassicalRegister(num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Qubit 0: Encode trend strength
        # Map trend from -1,1 to 0,π
        trend_angle = (trend_strength + 1) * np.pi/2
        qc.ry(trend_angle, 0)
        
        # Qubit 1: Encode volatility
        volatility_angle = volatility * np.pi
        qc.ry(volatility_angle, 1)
        
        # Qubit 2: Encode recent price divergence from trend
        divergence_angle = (recent_divergence + 1) * np.pi/2
        qc.ry(divergence_angle, 2)
        
        # Create entanglement pattern for trend analysis
        qc.cx(0, 1)  # Entangle trend with volatility
        qc.cx(0, 2)  # Entangle trend with divergence
        
        # Add interference in output qubit
        qc.h(3)
        qc.cx(0, 3)
        qc.t(3)
        qc.cx(1, 3)
        qc.cx(2, 3)
        qc.tdg(3)
        qc.h(3)
        
        # Measure all qubits
        qc.measure(range(num_qubits), range(num_qubits))
        
        return qc
        
    @staticmethod
    def breakout_detection_circuit(price_range, volume_increase, volatility_spike, num_qubits=4):
        """
        Create circuit for breakout pattern detection
        
        Args:
            price_range: Normalized price range/channel width (0-1)
            volume_increase: Volume spike relative to average (0-1)
            volatility_spike: Volatility increase relative to average (0-1)
            num_qubits: Number of qubits to use
            
        Returns:
            QuantumCircuit for breakout detection
        """
        qr = QuantumRegister(num_qubits, 'q')
        cr = ClassicalRegister(num_qubits, 'c')
        qc = QuantumCircuit(qr, cr)
        
        # Qubit 0: Encode price range/channel width
        # Narrow range = higher breakout probability
        narrow_range_prob = 1 - price_range  # Invert: narrower range = higher value
        qc.ry(narrow_range_prob * np.pi, 0)
        
        # Qubit 1: Encode volume increase
        qc.ry(volume_increase * np.pi, 1)
        
        # Qubit 2: Encode volatility spike
        qc.ry(volatility_spike * np.pi, 2)
        
        # Create entanglement for breakout pattern
        qc.cx(0, 1)  # Entangle price range with volume
        qc.cx(1, 2)  # Entangle volume with volatility
        
        # Interference pattern for breakout detection
        qc.h(3)  # Output qubit in superposition
        qc.cx(0, 3)
        qc.cx(1, 3)
        qc.cx(2, 3)
        qc.h(3)
        
        # Measure all qubits
        qc.measure(range(num_qubits), range(num_qubits))
        
        return qc
