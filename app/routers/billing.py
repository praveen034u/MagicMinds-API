"""Billing router for voice subscriptions and Stripe checkout."""
from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import Optional
from pydantic import BaseModel
import os

# Stripe integration (will be imported when stripe is installed)
try:
    import stripe
    STRIPE_AVAILABLE = True
    stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
except ImportError:
    STRIPE_AVAILABLE = False

from ..deps.auth import get_current_user, CurrentUser
from ..deps.db import get_db, set_rls_context
from ..models.parent_profile import ParentProfile
from ..models.voice_subscription import VoiceSubscription
from ..schemas.story import (
    VoiceSubscriptionCreate,
    VoiceSubscriptionResponse
)

router = APIRouter()

class CheckoutRequest(BaseModel):
    """Request to create Stripe checkout session."""
    email: Optional[str] = None
    name: Optional[str] = None

class CheckoutResponse(BaseModel):
    """Response with checkout session URL."""
    url: str

@router.post("/create-checkout", response_model=CheckoutResponse)
async def create_checkout_session(
    checkout_data: CheckoutRequest,
    request: Request,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create a Stripe checkout session for voice cloning subscription."""
    await set_rls_context(db, current_user.sub)
    
    if not STRIPE_AVAILABLE:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Stripe integration not configured"
        )
    
    # Get parent profile
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Use email from request or parent profile
    email = checkout_data.email or parent.email or current_user.email
    name = checkout_data.name or parent.name or email
    
    if not email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is required"
        )
    
    try:
        # Check if a Stripe customer record exists for this email
        customers = stripe.Customer.list(email=email, limit=1)
        
        if customers.data:
            customer_id = customers.data[0].id
        else:
            # Create new customer
            customer = stripe.Customer.create(
                email=email,
                name=name
            )
            customer_id = customer.id
        
        # Get the origin for success/cancel URLs
        origin = request.headers.get("origin", "http://localhost:3000")
        
        # Create subscription checkout session
        # Price ID from edge function: price_1SB4ZHJAv5QFU5rkK7mIII1E
        price_id = os.getenv("STRIPE_PRICE_ID", "price_1SB4ZHJAv5QFU5rkK7mIII1E")
        
        session = stripe.checkout.Session.create(
            customer=customer_id,
            line_items=[
                {
                    "price": price_id,
                    "quantity": 1,
                },
            ],
            mode="subscription",
            success_url=f"{origin}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{origin}/subscription/cancel",
        )
        
        return CheckoutResponse(url=session.url)
        
    except stripe.error.StripeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Stripe error: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating checkout session: {str(e)}"
        )

@router.post("/voice-subscription", response_model=VoiceSubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_voice_subscription(
    subscription_data: VoiceSubscriptionCreate,
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Create or update voice subscription."""
    await set_rls_context(db, current_user.sub)
    
    # Get parent profile
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Check if subscription exists
    result = await db.execute(
        select(VoiceSubscription).where(VoiceSubscription.parent_id == parent.id)
    )
    subscription = result.scalar_one_or_none()
    
    if subscription:
        # Update existing
        subscription.stripe_subscription_id = subscription_data.stripe_subscription_id
        subscription.status = subscription_data.status
        subscription.plan_type = subscription_data.plan_type
    else:
        # Create new
        subscription = VoiceSubscription(
            parent_id=parent.id,
            stripe_subscription_id=subscription_data.stripe_subscription_id,
            status=subscription_data.status,
            plan_type=subscription_data.plan_type
        )
        db.add(subscription)
    
    await db.commit()
    await db.refresh(subscription)
    
    return subscription

@router.get("/voice-subscription", response_model=VoiceSubscriptionResponse)
async def get_voice_subscription(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current voice subscription."""
    await set_rls_context(db, current_user.sub)
    
    # Get parent profile
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Get subscription
    result = await db.execute(
        select(VoiceSubscription).where(VoiceSubscription.parent_id == parent.id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    return subscription

@router.delete("/voice-subscription", status_code=status.HTTP_204_NO_CONTENT)
async def cancel_voice_subscription(
    current_user: CurrentUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Cancel voice subscription."""
    await set_rls_context(db, current_user.sub)
    
    # Get parent profile
    result = await db.execute(
        select(ParentProfile).where(ParentProfile.auth0_user_id == current_user.sub)
    )
    parent = result.scalar_one_or_none()
    
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent profile not found"
        )
    
    # Get subscription
    result = await db.execute(
        select(VoiceSubscription).where(VoiceSubscription.parent_id == parent.id)
    )
    subscription = result.scalar_one_or_none()
    
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found"
        )
    
    # Update status instead of deleting
    subscription.status = "cancelled"
    await db.commit()
