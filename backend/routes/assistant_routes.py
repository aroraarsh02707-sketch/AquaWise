"""
Conversational AI Assistant REST API Routes (Task 6).

Endpoints:
- POST /api/assistant/chat : Send a message to the AI and get a response.
- GET /api/assistant/conversations : List user's conversations.
- GET /api/assistant/conversations/<id> : Get full message history of a conversation.
"""

from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from backend.models import db, Assessment, ConsumptionBreakdown, AIConversation, AIMessage
from backend.services.ai_service import chat_with_assistant

assistant_bp = Blueprint("assistant", __name__)


def _get_user_context(user_id):
    """Retrieve the user's latest assessment context for the AI."""
    latest_assessment = db.session.query(Assessment)\
        .filter_by(user_id=user_id)\
        .order_by(Assessment.created_at.desc())\
        .first()
    
    if not latest_assessment:
        return None
        
    top_breakdown = db.session.query(ConsumptionBreakdown)\
        .filter_by(assessment_id=latest_assessment.id)\
        .order_by(ConsumptionBreakdown.litres_per_day.desc())\
        .first()
        
    return {
        "user_type": latest_assessment.assessment_type,
        "daily_consumption": round(latest_assessment.daily_consumption, 1),
        "water_saver_score": latest_assessment.water_saver_score,
        "top_category": top_breakdown.category if top_breakdown else None
    }


@assistant_bp.route("/api/assistant/chat", methods=["POST"])
@login_required
def chat():
    data = request.get_json() or {}
    message_text = data.get("message", "").strip()
    conv_id = data.get("conversation_id")

    if not message_text:
        return jsonify({
            "success": False,
            "error": {
                "code": "BAD_REQUEST",
                "message": "Message text is required."
            }
        }), 400

    conversation = None
    if conv_id:
        conversation = db.session.get(AIConversation, conv_id)
        if not conversation:
            return jsonify({
                "success": False,
                "error": {
                    "code": "NOT_FOUND",
                    "message": "Conversation not found."
                }
            }), 404
        if conversation.user_id != current_user.id:
            return jsonify({
                "success": False,
                "error": {
                    "code": "FORBIDDEN",
                    "message": "You do not have permission to access this conversation."
                }
            }), 403
    else:
        # Create a new conversation
        # Truncate title to first ~40 chars of message if too long
        title = (message_text[:37] + "...") if len(message_text) > 40 else message_text
        conversation = AIConversation(user_id=current_user.id, title=title)
        db.session.add(conversation)
        db.session.flush()

    # Load history
    history = []
    if conversation.messages:
        for m in conversation.messages:
            history.append({"role": m.role, "message": m.message})

    user_context = _get_user_context(current_user.id)

    # Call AI Service
    ai_response = chat_with_assistant(
        user_message=message_text,
        conversation_history=history,
        user_context=user_context
    )

    # Save User Message
    user_msg = AIMessage(
        conversation_id=conversation.id,
        role="user",
        message=message_text
    )
    
    # Save Assistant Message
    assistant_msg = AIMessage(
        conversation_id=conversation.id,
        role="assistant",
        message=ai_response["response"]
    )
    
    db.session.add_all([user_msg, assistant_msg])
    # Update conversation timestamp implicitly via onupdate in model if needed, but doing it explicitly guarantees it.
    conversation.updated_at = db.func.now()
    db.session.commit()

    return jsonify({
        "success": True,
        "data": {
            "conversation_id": conversation.id,
            "message": ai_response["response"],
            "source": ai_response.get("source", "ai"),
            "disclaimer": ai_response.get("disclaimer", "")
        }
    }), 200


@assistant_bp.route("/api/assistant/conversations", methods=["GET"])
@login_required
def get_conversations():
    conversations = db.session.query(AIConversation)\
        .filter_by(user_id=current_user.id)\
        .order_by(AIConversation.updated_at.desc())\
        .all()
        
    return jsonify({
        "success": True,
        "data": {
            "conversations": [c.to_dict(include_messages=False) for c in conversations]
        }
    }), 200


@assistant_bp.route("/api/assistant/conversations/<int:conv_id>", methods=["GET"])
@login_required
def get_conversation(conv_id):
    conversation = db.session.get(AIConversation, conv_id)
    if not conversation:
        return jsonify({
            "success": False,
            "error": {
                "code": "NOT_FOUND",
                "message": "Conversation not found."
            }
        }), 404
        
    if conversation.user_id != current_user.id:
        return jsonify({
            "success": False,
            "error": {
                "code": "FORBIDDEN",
                "message": "You do not have permission to access this conversation."
            }
        }), 403
        
    return jsonify({
        "success": True,
        "data": {
            "conversation": conversation.to_dict(include_messages=True)
        }
    }), 200
