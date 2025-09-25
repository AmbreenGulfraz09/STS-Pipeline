# vad_config.py
from pipecat.audio.vad.silero import SileroVADAnalyzer, VADParams
from pipecat.transports.base_transport import TransportParams
from pipecat.audio.turn.smart_turn.local_smart_turn_v3 import LocalSmartTurnAnalyzerV3
from loguru import logger


def create_transport_params(using_turn_detection: bool = True):
    """
    Returns TransportParams configured with Silero VAD + Local Smart Turn detection (v3).
    """
    # VAD parameters tuned for quicker response
    vad_params = VADParams(
        confidence=0.7,
        start_secs=0.1,
        stop_secs=0.2 if using_turn_detection else 0.1,
        min_volume=0.6,
    )

    turn_analyzer = None
    if using_turn_detection:
        turn_analyzer = LocalSmartTurnAnalyzerV3(
            smart_turn_model_path=None, 
            sample_rate=16000,
            params=None,
        )
        
    return TransportParams(
        audio_in_enabled=True,
        audio_out_enabled=True,
        vad_analyzer=SileroVADAnalyzer(params=vad_params),
        turn_analyzer=turn_analyzer,
    )
