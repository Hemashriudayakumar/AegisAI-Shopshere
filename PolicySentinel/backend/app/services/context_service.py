import json
import datetime
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from app.models.context import ConversationContextModel
from app.schemas.context import ConversationContext

class ContextService:
    @staticmethod
    def _model_to_schema(model: ConversationContextModel) -> ConversationContext:
        previous_refunds = []
        if model.previous_refunds:
            try:
                previous_refunds = json.loads(model.previous_refunds)
            except Exception:
                previous_refunds = []

        order_lookups = {}
        if model.order_lookups:
            try:
                order_lookups = json.loads(model.order_lookups)
            except Exception:
                order_lookups = {}

        return ConversationContext(
            conversation_id=model.conversation_id,
            customer_id=model.customer_id,
            customer_verified=bool(model.customer_verified),
            verified_at=model.verified_at,
            previous_refunds=previous_refunds,
            complaint_count=int(model.complaint_count or 0),
            order_lookups=order_lookups,
            last_updated_at=model.last_updated_at or datetime.datetime.now(datetime.timezone.utc),
        )

    @staticmethod
    def load_context(
        db: Session,
        conversation_id: str,
        customer_id: Optional[str] = None
    ) -> ConversationContext:
        """Loads existing conversation context or creates and persists a new one."""
        model = db.query(ConversationContextModel).filter(
            ConversationContextModel.conversation_id == conversation_id
        ).first()

        if model:
            # If customer_id changed or was provided, update it
            if customer_id and model.customer_id != customer_id:
                model.customer_id = customer_id
                model.last_updated_at = datetime.datetime.now(datetime.timezone.utc)
                db.commit()
                db.refresh(model)
            return ContextService._model_to_schema(model)

        # Create new context record
        now = datetime.datetime.now(datetime.timezone.utc)
        new_model = ConversationContextModel(
            conversation_id=conversation_id,
            customer_id=customer_id or "CUST-10",
            customer_verified=False,
            verified_at=None,
            previous_refunds="[]",
            complaint_count=0,
            order_lookups="{}",
            last_updated_at=now,
        )
        db.add(new_model)
        db.commit()
        db.refresh(new_model)
        return ContextService._model_to_schema(new_model)

    @staticmethod
    def save_context(
        db: Session,
        context: ConversationContext
    ) -> ConversationContext:
        """Upserts a ConversationContext schema back to the database."""
        model = db.query(ConversationContextModel).filter(
            ConversationContextModel.conversation_id == context.conversation_id
        ).first()

        now = datetime.datetime.now(datetime.timezone.utc)
        if not model:
            model = ConversationContextModel(
                conversation_id=context.conversation_id,
                customer_id=context.customer_id,
                customer_verified=context.customer_verified,
                verified_at=context.verified_at,
                previous_refunds=json.dumps(context.previous_refunds),
                complaint_count=context.complaint_count,
                order_lookups=json.dumps(context.order_lookups),
                last_updated_at=now,
            )
            db.add(model)
        else:
            model.customer_id = context.customer_id
            model.customer_verified = context.customer_verified
            model.verified_at = context.verified_at
            model.previous_refunds = json.dumps(context.previous_refunds)
            model.complaint_count = context.complaint_count
            model.order_lookups = json.dumps(context.order_lookups)
            model.last_updated_at = now

        db.commit()
        db.refresh(model)
        return ContextService._model_to_schema(model)

    @staticmethod
    def update_context_for_refund(
        db: Session,
        context: ConversationContext,
        order_id: str,
        amount: float
    ) -> ConversationContext:
        """Records a successful refund in the conversation context history."""
        context.previous_refunds.append({
            "order_id": order_id,
            "amount": float(amount),
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        })
        return ContextService.save_context(db, context)

    @staticmethod
    def increment_complaints(
        db: Session,
        context: ConversationContext,
        count: int = 1
    ) -> ConversationContext:
        """Increments unresolved/escalated complaints counter."""
        context.complaint_count += count
        return ContextService.save_context(db, context)

    @staticmethod
    def update_order_lookup(
        db: Session,
        context: ConversationContext,
        order_id: str,
        lookup_data: Dict[str, Any]
    ) -> ConversationContext:
        """Records verified order status lookups in context."""
        context.order_lookups[order_id] = lookup_data
        return ContextService.save_context(db, context)

    @staticmethod
    def set_verification(
        db: Session,
        context: ConversationContext,
        is_verified: bool
    ) -> ConversationContext:
        """Updates the persistent customer identity verification state."""
        context.customer_verified = is_verified
        if is_verified and not context.verified_at:
            context.verified_at = datetime.datetime.now(datetime.timezone.utc)
        elif not is_verified:
            context.verified_at = None
        return ContextService.save_context(db, context)

context_service = ContextService()
