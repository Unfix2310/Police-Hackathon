"""
Entity Resolver Module.
"""
from typing import Optional, Dict, Any, List
import uuid

class EntityResolver:
    """Resolves entities from observations."""
    
    async def resolve_vehicle(self, observation: Any, db: Any) -> Dict[str, Any]:
        """
        Matches vehicle by plate.
        exact=0.95, partial+attrs=0.7, no plate=0.5
        """
        plate = observation.payload.get("plate")
        plate_conf = observation.payload.get("plate_confidence", 0)
        
        if plate and plate_conf > 0.8:
            match = await db.find_exact_plate(plate)
            if match:
                return {"entity_id": match.id, "confidence": 0.95, "method": "EXACT_PLATE"}
                
            candidates = await db.find_partial_plate(plate)
            for cand in candidates:
                if cand.color == observation.payload.get("color") and cand.vehicle_class == observation.payload.get("vehicle_class"):
                    return {"entity_id": cand.id, "confidence": 0.75, "method": "PARTIAL_ATTR"}
                    
        return {"entity_id": f"V-{uuid.uuid4().hex[:8]}", "confidence": 0.5, "method": "NEW_ENTITY"}

    async def resolve_person(self, observation: Any, features: List[float], db: Any) -> Dict[str, Any]:
        """
        Matches person by ReID similarity > 0.75.
        """
        candidates = await db.search_knn(features, top_k=5)
        for cand in candidates:
            if cand.similarity > 0.75:
                # Optionally check feasibility here
                return {"entity_id": cand.id, "confidence": cand.similarity, "method": "REID"}
                
        return {"entity_id": f"P-{uuid.uuid4().hex[:8]}", "confidence": 0.5, "method": "NEW_ENTITY"}
