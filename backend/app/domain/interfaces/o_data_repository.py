from typing import List, Dict, Any

class ODataRepository:
    def save(self, data: List[Dict[str, Any]]) -> None:
        raise NotImplementedError("This method should be overridden by subclasses")
