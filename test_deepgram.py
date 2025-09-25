import os
from dotenv import load_dotenv
from loguru import logger

from pipecat.frames.frames import LLMRunFrame, TranscriptionFrame
from pipecat.pipeline.pipeline import Pipeline
from pipecat.pipeline.runner import PipelineRunner
from pipecat.pipeline.task import PipelineParams, PipelineTask
from pipecat.processors.aggregators.openai_llm_context import OpenAILLMContext
from pipecat.runner.types import RunnerArguments
from pipecat.runner.utils import create_transport
from pipecat.services.deepgram.stt import DeepgramSTTService
from pipecat.services.deepgram.tts import DeepgramTTSService
from pipecat.services.openai.llm import OpenAILLMService
from pipecat.transports.base_transport import BaseTransport
from pipecat.audio.filters.aic_filter import AICFilter
from pipecat.audio.filters.koala_filter import KoalaFilter
from vad_config import create_transport_params
from pipecat.audio.interruptions.min_words_interruption_strategy import MinWordsInterruptionStrategy

import mimetypes
mimetypes.add_type("application/javascript", ".js")
mimetypes.add_type("text/css", ".css")

load_dotenv(override=True)

async def run_bot(transport: BaseTransport, runner_args: RunnerArguments):
    logger.info("Starting bot")

    # Deepgram STT with interim results + VAD tuning
    stt = DeepgramSTTService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),
        model="nova-3-conversational",   # "nova-3-general" 
        interim_results=True,
        punctuate=True,
        vad_events=True,
        utterance_end_ms=300,
        filters=[
            KoalaFilter(access_key=os.getenv("Koala_API_KEY")),  
            AICFilter(),     
        ],
    )

    # Deepgram TTS
    tts = DeepgramTTSService(
        api_key=os.getenv("DEEPGRAM_API_KEY"),  # default model:"aura-2-helena-en"
        voice="aura-2-andromeda-en",
        stream=True,
    )

    # OpenAI LLM  -- default model: gpt-4.1
    llm = OpenAILLMService(api_key=os.getenv("OPENAI_API_KEY"), model="gpt-4o-mini", stream=True)   
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI interviewer conducting a interview for a candidate applying to an AI role. "
                "Your output will be converted to audio so don't include special characters in your answers. "
                "Respond to what the user said in a professional and thoughtful way. you are encouraged to generate shorter and more concise answers"
            ),
        },
    ]
    
    context = OpenAILLMContext(messages)  
    context_aggregator = llm.create_context_aggregator(context)

    pipeline = Pipeline(
        [
            transport.input(),
            stt,
            context_aggregator.user(),
            llm,
            tts,
            transport.output(),
            context_aggregator.assistant(),
        ]
    )

    task = PipelineTask(
        pipeline,
        params=PipelineParams(
            enable_metrics=True,
            enable_usage_metrics=True,
            allow_interruptions=True,
            interruption_strategies=[MinWordsInterruptionStrategy(min_words=2)],
        ),
        idle_timeout_secs=runner_args.pipeline_idle_timeout_secs,
    )

    # --- Event Handlers ---
    @transport.event_handler("on_client_connected")
    async def on_client_connected(transport, client):
        logger.info("Client connected")
        messages.append(
            {
                "role": "system",
                "content": (
                    "Greet the candidate politely and naturally, and introduce yourself as the interviewer."
                    "Then, ask candidate to introduce themselves briefly. and then ask the first interview question."
                    "If the user interrupts you, first address their input, then continue your previous answer naturally."
                ),
            }
        )
        await task.queue_frames([LLMRunFrame()])

    @transport.event_handler("on_client_disconnected")
    async def on_client_disconnected(transport, client):
        logger.info("Client disconnected")
        await task.cancel()

    # log when transcription stops (end of turn)
    @transport.event_handler("on_transcription_stopped")
    async def on_transcription_stopped(transport, client, transcription_frame):
        try:
            text = getattr(transcription_frame, "text", None)
            logger.info(f"User finished turn and stopped speaking. Text: {text}")
        except Exception as exc:
            logger.exception(f"Error handling on_transcription_stopped: {exc}")
    
    @transport.event_handler("on_user_turn_end")
    async def on_user_turn_end(transport, info=None):
        logger.info("User has finished speaking (Smart Turn detected end of turn).")
    
    # continue after user interruption
    @transport.event_handler("on_user_interruption")
    async def on_user_interruption(transport, client, interruption_frame):
        logger.info("User interrupted. Continuing with new input.")
        messages.append(
            {
                "role": "system",
                "content": (
                    "You are an AI interviewer. If the user interrupts you, first address their input, then continue your previous answer naturally."
                ),
            }
        )
        await task.queue_frames([LLMRunFrame()])


    # fallback: detect final transcription frames from pipeline
    @task.event_handler("on_frame_reached_upstream")
    async def on_frame_reached_upstream(frame):
        if isinstance(frame, TranscriptionFrame):
            result = getattr(frame, "result", None)
            is_final = False
            if result:
                is_final = bool(result.get("is_final")) if isinstance(result, dict) else getattr(frame, "is_final", False)
            if is_final:
                logger.info(f"Detected final transcription frame — user finished speaking. Text: {getattr(frame, 'text', None)}")

    runner = PipelineRunner(handle_sigint=runner_args.handle_sigint)
    await runner.run(task)


async def bot(runner_args: RunnerArguments):
    """Main bot entry point compatible with Pipecat Cloud."""
    transport = await create_transport(
        runner_args,
        {
            "webrtc": lambda: create_transport_params(using_turn_detection=True),
            "twilio": lambda: create_transport_params(using_turn_detection=True),
        },
    )
    await run_bot(transport, runner_args)


if __name__ == "__main__":
    from runner import main
    main()
