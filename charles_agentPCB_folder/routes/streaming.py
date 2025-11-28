"""
Streaming routes
SSE endpoints for real-time design generation
"""

import asyncio
import json
import logging
import os
import sys
import time
from pathlib import Path
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse

from agents.query_router_agent import QueryRouterAgent
from services.streaming_service import (
    StreamingOrchestrator,
    generate_design_stream,
    refine_design_stream,
    answer_question
)
from api.conversation_manager import ConversationManager
from core.cache import get_cache_manager

logger = logging.getLogger(__name__)

router = APIRouter(tags=["streaming"])

# Initialize conversation manager (singleton)
conversation_manager = ConversationManager()


@router.post("/mcp/component-analysis")
async def component_analysis(request: Request):
    """SSE endpoint for component analysis with query routing."""
    
    body = await request.json()
    query = body.get("query", "")
    provider = body.get("provider", "xai")  # Default to xai - OpenAI support removed
    session_id = body.get("sessionId")  # Conversation session ID
    context_query_id = body.get("contextQueryId")
    context = body.get("context", "")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    # Validate provider - only xai supported
    if provider not in ["xai"]:
        logger.warning(f"[PROVIDER] Invalid provider '{provider}' requested, defaulting to 'xai'")
        provider = "xai"
    
    # Get or create session
    if not session_id:
        session_id = conversation_manager.create_session()
    elif session_id not in conversation_manager.sessions:
        session_id = conversation_manager.create_session(session_id)
    
    # Get existing design state if available
    existing_design_state = conversation_manager.get_design_state(session_id)
    has_existing_design = existing_design_state is not None
    
    # Store original provider to restore later
    original_provider = os.environ.get("LLM_PROVIDER", "xai")
    
    async def event_stream():
        # CRITICAL: Set provider in environment FIRST, before ANY agent creation
        # This must happen before any import or agent instantiation
        os.environ["LLM_PROVIDER"] = provider
        logger.info(f"[PROVIDER] Set LLM_PROVIDER='{provider}' (env now: {os.environ.get('LLM_PROVIDER')})")
        
        # Send immediate update to frontend
        yield f"data: {json.dumps({'type': 'reasoning', 'componentId': 'system', 'componentName': 'System', 'reasoning': f'Initializing with {provider.upper()} provider...', 'hierarchyLevel': 0})}\n\n"
        
        queue = asyncio.Queue()
        
        try:
            # Verify provider is set before creating any agents
            current_provider = os.environ.get("LLM_PROVIDER")
            if current_provider != provider:
                logger.error(f"[PROVIDER] MISMATCH! Expected '{provider}', got '{current_provider}'")
                os.environ["LLM_PROVIDER"] = provider  # Force set again
            
            # Initialize query router (will use provider from environment via lazy init)
            logger.info(f"[PROVIDER] Creating QueryRouterAgent (LLM_PROVIDER={os.environ.get('LLM_PROVIDER')})")
            query_router = QueryRouterAgent()
            
            # Send update
            yield f"data: {json.dumps({'type': 'reasoning', 'componentId': 'router', 'componentName': 'Query Router', 'reasoning': 'Analyzing query intent...', 'hierarchyLevel': 0})}\n\n"
            
            # Classify query intent (will initialize LLM config if needed)
            classification = query_router.classify_query(query, has_existing_design, existing_design_state)
            intent = classification.get("intent", "new_design")
            action_details = classification.get("action_details", {})
            
            # Add message to conversation history
            conversation_manager.add_message(session_id, "user", query, {"classification": classification})
            
            await queue.put({
                "type": "reasoning",
                "componentId": "router",
                "componentName": "Query Router",
                "reasoning": f"Query classified as: {intent} (confidence: {classification.get('confidence', 0):.2f})",
                "hierarchyLevel": 0
            })
            
            # Create orchestrator with cache manager
            # CRITICAL: Provider MUST be set before this point
            logger.info(f"[PROVIDER] Creating StreamingOrchestrator (LLM_PROVIDER={os.environ.get('LLM_PROVIDER')})")
            cache_manager = get_cache_manager()
            orchestrator = StreamingOrchestrator()
            # Inject cache manager into orchestrator's agents
            orchestrator.requirements_agent.cache_manager = cache_manager
            orchestrator.part_search_agent.cache_manager = cache_manager
            orchestrator.compatibility_agent.cache_manager = cache_manager
            logger.info(f"[PROVIDER] Orchestrator created successfully")
            
            # Route based on intent
            if intent == "new_design":
                # Full design generation - start immediately
                logger.info(f"[WORKFLOW] Starting new design generation (provider={os.environ.get('LLM_PROVIDER')})")
                task = asyncio.create_task(generate_design_stream(query, orchestrator, queue))
            elif intent == "refinement":
                # Refine existing design
                task = asyncio.create_task(refine_design_stream(query, orchestrator, queue, existing_design_state, action_details))
            elif intent == "question":
                # Answer question
                question_type = action_details.get("question_type", "general")
                task = asyncio.create_task(answer_question(query, orchestrator, queue, existing_design_state, question_type))
            elif intent == "analysis_request":
                # Run specific analysis (for now, fall back to full generation)
                await queue.put({
                    "type": "reasoning",
                    "componentId": "router",
                    "componentName": "Query Router",
                    "reasoning": f"Running {action_details.get('analysis_type', 'design')} analysis...",
                    "hierarchyLevel": 0
                })
                task = asyncio.create_task(generate_design_stream(query, orchestrator, queue))
            else:
                # Default to new design
                task = asyncio.create_task(generate_design_stream(query, orchestrator, queue))
            
        except ValueError as e:
            # If agent initialization fails (e.g., missing API key), send error
            error_msg = str(e)
            current_provider = os.environ.get("LLM_PROVIDER", "not_set")
            if "API_KEY" in error_msg:
                error_msg = f"XAI_API_KEY not found. Provider was set to '{current_provider}'. Please check your XAI_API_KEY environment variable on Railway."
            logger.error(f"[PROVIDER] Agent initialization failed: {error_msg} (provider={current_provider})")
            await queue.put({
                "type": "error",
                "message": error_msg
            })
            # Restore original provider
            os.environ["LLM_PROVIDER"] = original_provider
            # Yield error and return
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return
        except Exception as e:
            error_msg = str(e)
            current_provider = os.environ.get("LLM_PROVIDER", "not_set")
            logger.error(f"[ERROR] Unexpected error in event_stream: {error_msg} (provider={current_provider})", exc_info=True)
            await queue.put({
                "type": "error",
                "message": f"Unexpected error: {error_msg}"
            })
            os.environ["LLM_PROVIDER"] = original_provider
            yield f"data: {json.dumps({'type': 'error', 'message': error_msg})}\n\n"
            return
        
        try:
            last_heartbeat = time.time()
            heartbeat_interval = 10.0  # Send heartbeat every 10 seconds
            complete_sent = False  # Track if complete event was sent
            last_progress_time = time.time()
            progress_interval = 5.0  # Send progress update every 5 seconds
            
            while True:
                try:
                    # Wait for event with shorter timeout for faster updates
                    timeout = 5.0  # Shorter timeout for more responsive updates
                    event = await asyncio.wait_for(queue.get(), timeout=timeout)
                    
                    # Immediately yield the event
                    event_json = json.dumps(event)
                    yield f"data: {event_json}\n\n"
                    
                    # Flush immediately for live updates
                    import sys
                    if hasattr(sys.stdout, 'flush'):
                        sys.stdout.flush()
                    
                    if event.get("type") == "error":
                        # Don't break on error - let workflow complete unless fatal
                        if event.get("message", "").startswith("Fatal"):
                            complete_sent = True
                            break
                    
                    if event.get("type") == "complete":
                        complete_sent = True
                        logger.info("[STREAM] Complete event received, ending stream")
                        break
                    
                    # Reset heartbeat timer on any event
                    last_heartbeat = time.time()
                    last_progress_time = time.time()
                        
                except asyncio.TimeoutError:
                    current_time = time.time()
                    
                    # Send heartbeat to keep connection alive
                    if current_time - last_heartbeat >= heartbeat_interval:
                        yield f"data: {json.dumps({'type': 'heartbeat', 'message': 'Processing...'})}\n\n"
                        last_heartbeat = current_time
                        if hasattr(sys.stdout, 'flush'):
                            sys.stdout.flush()
                    
                    # Send progress update if task is still running
                    if current_time - last_progress_time >= progress_interval and not task.done():
                        yield f"data: {json.dumps({'type': 'reasoning', 'componentId': 'system', 'componentName': 'System', 'reasoning': 'Still processing...', 'hierarchyLevel': 0})}\n\n"
                        last_progress_time = current_time
                    
                    # Check if task is done
                    if task.done():
                        # Task completed but no complete event? Send one
                        if not complete_sent:
                            try:
                                result = task.result()
                                # Task completed successfully but no complete event was sent
                                logger.warning("[STREAM] Task completed but no complete event received. Sending completion.")
                                yield f"data: {json.dumps({'type': 'complete', 'message': 'Design generation completed.'})}\n\n"
                                complete_sent = True
                                if hasattr(sys.stdout, 'flush'):
                                    sys.stdout.flush()
                            except Exception as e:
                                # Task completed with exception
                                logger.error(f"[STREAM] Task completed with exception: {str(e)}")
                                yield f"data: {json.dumps({'type': 'error', 'message': f'Task error: {str(e)}'})}\n\n"
                                yield f"data: {json.dumps({'type': 'complete', 'message': f'Design generation completed with errors: {str(e)}'})}\n\n"
                                complete_sent = True
                                if hasattr(sys.stdout, 'flush'):
                                    sys.stdout.flush()
                        break
                    # Continue waiting for events
                    continue
                    
        except Exception as e:
            logger.error(f"[STREAM] Event stream error: {str(e)}", exc_info=True)
            if not complete_sent:
                yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"
                yield f"data: {json.dumps({'type': 'complete', 'message': f'Stream ended with error: {str(e)}'})}\n\n"
                complete_sent = True
                if hasattr(sys.stdout, 'flush'):
                    sys.stdout.flush()
        finally:
            # Ensure complete is always sent
            if not complete_sent:
                logger.warning("[STREAM] Stream ending without complete event - sending final complete")
                yield f"data: {json.dumps({'type': 'complete', 'message': 'Stream ended'})}\n\n"
                if hasattr(sys.stdout, 'flush'):
                    sys.stdout.flush()
            
            # Cleanup: cancel task if still running
            if not task.done():
                task.cancel()
                try:
                    await asyncio.wait_for(task, timeout=2.0)
                except (asyncio.CancelledError, asyncio.TimeoutError):
                    pass
            # Restore original provider
            os.environ["LLM_PROVIDER"] = original_provider
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Disable nginx buffering for live updates
            "X-Session-Id": session_id,  # Return session ID in headers
        }
    )

