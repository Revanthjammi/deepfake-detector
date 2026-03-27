"""
Ensemble voting system for better accuracy
"""

import numpy as np
from collections import Counter
import statistics


class EnsembleVoter:
    """
    Enhanced ensemble voting with multiple strategies
    """
    
    def __init__(self, weights=None):
        self.weights = weights or {
            'swinv2': 0.35,
            'efficientnet': 0.30,
            'xception': 0.25,
            'vit': 0.10
        }
        self.history = []
    
    def weighted_vote(self, predictions):
        """
        Weighted average voting
        """
        if not predictions:
            return 0.5
        
        total_weight = 0
        weighted_sum = 0
        
        for model_name, pred in predictions.items():
            weight = self.weights.get(model_name, 0.25)
            weighted_sum += pred * weight
            total_weight += weight
        
        if total_weight == 0:
            return 0.5
        
        return weighted_sum / total_weight
    
    def majority_vote(self, predictions):
        """
        Majority voting (each model gets 1 vote)
        """
        votes = []
        for model_name, pred in predictions.items():
            votes.append(1 if pred > 0.5 else 0)
        
        if not votes:
            return 0.5
        
        majority = sum(votes) / len(votes)
        return majority
    
    def consensus_vote(self, predictions):
        """
        Consensus voting - require all models to agree
        """
        if not predictions:
            return 0.5
        
        all_fake = all(pred > 0.5 for pred in predictions.values())
        all_real = all(pred < 0.5 for pred in predictions.values())
        
        if all_fake:
            return 0.95
        elif all_real:
            return 0.05
        else:
            # Use weighted vote if no consensus
            return self.weighted_vote(predictions)
    
    def confidence_based_vote(self, predictions, confidences):
        """
        Vote based on model confidence
        """
        if not predictions:
            return 0.5
        
        weighted_sum = 0
        total_confidence = 0
        
        for model_name, pred in predictions.items():
            conf = confidences.get(model_name, 0.5)
            # High confidence models get more weight
            weighted_sum += pred * conf
            total_confidence += conf
        
        if total_confidence == 0:
            return 0.5
        
        return weighted_sum / total_confidence
    
    def adaptive_vote(self, predictions, confidences, history=None):
        """
        Adaptive voting based on historical performance
        """
        # Start with weighted vote
        base_score = self.weighted_vote(predictions)
        
        # Adjust based on historical accuracy
        if history and len(history) > 10:
            # Calculate recent model accuracy
            model_accuracy = {}
            for model_name in predictions.keys():
                recent_predictions = [h.get(model_name, 0.5) for h in history[-20:]]
                if recent_predictions:
                    model_accuracy[model_name] = np.mean(recent_predictions)
            
            # Adjust weights based on accuracy
            adjusted_weights = self.weights.copy()
            for model_name in predictions.keys():
                if model_name in model_accuracy:
                    # Higher accuracy = higher weight
                    adjusted_weights[model_name] = self.weights[model_name] * (0.5 + model_accuracy[model_name])
            
            # Normalize weights
            total = sum(adjusted_weights.values())
            if total > 0:
                for k in adjusted_weights:
                    adjusted_weights[k] /= total
            
            # Recalculate with adjusted weights
            weighted_sum = 0
            for model_name, pred in predictions.items():
                weighted_sum += pred * adjusted_weights.get(model_name, 0.25)
            
            base_score = weighted_sum
        
        return base_score
    
    def get_confidence(self, predictions, method='weighted'):
        """
        Calculate confidence level based on model agreement
        """
        if not predictions:
            return 0.0
        
        pred_list = list(predictions.values())
        
        # Standard deviation (lower = higher agreement)
        std_dev = np.std(pred_list)
        
        # Agreement = 1 - normalized std
        agreement = 1.0 - min(1.0, std_dev * 2)
        
        # Mean prediction strength
        mean_strength = np.mean([abs(p - 0.5) * 2 for p in pred_list])
        
        # Combined confidence
        confidence = (agreement * 0.6) + (mean_strength * 0.4)
        
        return confidence
    
    def record_prediction(self, model_name, prediction, actual=None):
        """
        Record prediction for future adaptation
        """
        self.history.append({
            'model': model_name,
            'prediction': prediction,
            'actual': actual,
            'timestamp': time.time()
        })
        
        # Keep only last 1000 predictions
        if len(self.history) > 1000:
            self.history = self.history[-1000:]


# Create global ensemble
ensemble = EnsembleVoter()