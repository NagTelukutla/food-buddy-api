from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4

from app.repositories.base_json_repository import BaseJsonRepository


class PaymentRepository(BaseJsonRepository):
    def __init__(self):
        super().__init__("payments.json", {"payments": []})

    def _payments(self) -> List[Dict[str, Any]]:
        return self.read().get("payments", [])

    def _save_all(self, payments: List[Dict[str, Any]]) -> None:
        self.write({"payments": payments})

    def create(self, record: Dict[str, Any]) -> Dict[str, Any]:
        payments = self._payments()
        record["id"] = record.get("id") or f"PAY-{uuid4().hex[:12].upper()}"
        now = datetime.now(timezone.utc).isoformat()
        record.setdefault("created_at", now)
        record.setdefault("updated_at", now)
        payments.append(record)
        self._save_all(payments)
        return record

    def update(self, payment_id: str, updates: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        payments = self._payments()
        for index, payment in enumerate(payments):
            if payment.get("id") == payment_id:
                payments[index] = {
                    **payment,
                    **updates,
                    "id": payment_id,
                    "updated_at": datetime.now(timezone.utc).isoformat(),
                }
                self._save_all(payments)
                return payments[index]
        return None

    def get_by_id(self, payment_id: str) -> Optional[Dict[str, Any]]:
        for payment in self._payments():
            if payment.get("id") == payment_id:
                return payment
        return None

    def get_by_restaurant_order_id(self, restaurant_order_id: str) -> Optional[Dict[str, Any]]:
        matches = [p for p in self._payments() if p.get("restaurant_order_id") == restaurant_order_id]
        if not matches:
            return None
        return sorted(matches, key=lambda p: p.get("created_at", ""), reverse=True)[0]

    def get_by_razorpay_order_id(self, razorpay_order_id: str) -> Optional[Dict[str, Any]]:
        for payment in self._payments():
            if payment.get("razorpay_order_id") == razorpay_order_id:
                return payment
        return None

    def list_all(self, limit: int = 100) -> List[Dict[str, Any]]:
        payments = self._payments()
        return sorted(payments, key=lambda p: p.get("created_at", ""), reverse=True)[:limit]
