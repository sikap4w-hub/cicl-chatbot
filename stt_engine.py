"""
stt_engine.py
-------------
Taglish speech-to-text (SOP 1), gamit ang Whisper-small (Hugging Face
`transformers` "automatic-speech-recognition" pipeline) -- parehong
modelo at `generate_kwargs` na ginamit na sa test_whisper.py/baseline_wer.py
habang sinusukat ang baseline Word Error Rate. Dati, hiwalay lang itong
mga script na pinapatakbo nang manu-mano (offline, para sa WER
measurement); dito, sa `/api/stt` endpoint sa main.py, unang isinama ito
sa aktwal na web app para magamit ng totoong mic button sa chat.

Parehong "lazy-load" na pattern gaya ng gemini_engine.py: hindi agad
lino-load ang malaking modelo (~1GB pababain sa unang run, at
nangangailangan ng ilang segundo ng GPU/CPU time para i-initialize) sa
sandaling mag-start ang server -- sa UNANG aktwal na request pa lang sa
/api/stt ito lino-load, tapos nire-reuse na ang parehong pipeline object
sa lahat ng susunod na request (kaya isang beses lang ang mabigat na
startup cost, hindi paulit-ulit bawat tanong).
"""
import os
import time

MODEL_NAME = os.environ.get("STT_MODEL", "openai/whisper-small")
# Bilang default, "tagalog" ang language -- ito rin ang ginamit sa
# baseline_wer.py habang sinusukat ang WER. Gumagana pa rin ito nang
# maayos sa code-switched/Taglish speech (hindi lang purong Tagalog),
# dahil ang totoong layunin ng SOP1 ay Taglish, hindi purong isang wika.
STT_LANGUAGE = os.environ.get("STT_LANGUAGE", "tagalog")

_pipe = None
_init_error = None
_init_attempted = False


def get_pipeline():
    """
    Ibinabalik ang naka-cache nang Whisper pipeline, o sinusubukang i-load
    ito sa unang pagkakataong tawagin. Kapag nabigo ang pag-load (hal.
    walang torch/transformers na naka-install, walang internet para sa
    unang download, atbp.), hindi na ito muling sinusubukang i-load sa
    bawat request (mabagal at magpaparepeat lang ng parehong error) --
    sapat na ang _init_error na naka-cache para ipaliwanag sa user.
    """
    global _pipe, _init_error, _init_attempted
    if _init_attempted:
        return _pipe
    _init_attempted = True
    try:
        import torch
        from transformers import pipeline

        cuda_ok = torch.cuda.is_available()
        device = 0 if cuda_ok else -1
        # Diagnostic print -- lumalabas ito sa terminal kung saan tumatakbo
        # ang `uvicorn`. Kung "CPU" ang nakalagay dito kahit may GPU naman
        # ang laptop, malamang na hindi CUDA-enabled ang naka-install na
        # torch build (hal. na-install gamit ang default `pip install torch`
        # na kadalasang CPU-only sa Windows) -- ito ang PINAKAKARANIWANG
        # dahilan kung bakit "mabagal" ang transcription: CPU fallback
        # silently, walang error, pero mas mabagal ng ilang beses kaysa GPU.
        print(
            f"[stt_engine] Device: {'GPU (' + torch.cuda.get_device_name(0) + ')' if cuda_ok else 'CPU'} "
            f"-- kung CPU ito kahit may GPU ang makina, tingnan kung CUDA build "
            f"ang naka-install na torch (torch.cuda.is_available() == False)."
        )
        load_start = time.monotonic()
        _pipe = pipeline(
            task="automatic-speech-recognition",
            model=MODEL_NAME,
            device=device,
            generate_kwargs={
                "language": STT_LANGUAGE,
                "task": "transcribe",
                # NOTE: sinubukan muna dito ang "num_beams": 1 para pilitin
                # ang greedy decoding, pero pinalabas nito ng transformers
                # ang isang deprecation warning (nag-co-conflict sa sarili
                # nitong generation_config) -- at based sa aktwal na
                # sinukat na 1.7s per-request sa GPU, hindi naman ito
                # kailangan, kaya inalis na lang. Ang totoong bottleneck
                # (kung meron man) ay malamang CPU fallback (walang CUDA
                # build ng torch), hindi ang beam search settings -- tingnan
                # ang "Device:" print sa itaas.
                "condition_on_prev_tokens": False,
            },
        )
        print(f"[stt_engine] Na-load ang {MODEL_NAME} sa {time.monotonic() - load_start:.1f}s "
              f"(isang beses lang ito -- nire-reuse na ang model sa susunod na mga request).")
    except Exception as e:  # noqa: BLE001 -- sinadya, kahit anong klaseng
        # pagkakamali sa pag-load (missing package, walang GPU/CUDA driver,
        # walang internet, sirang cache) ay dapat maging malinaw na error
        # message sa user sa halip na 500 crash ang buong request.
        _init_error = str(e)
        _pipe = None
    return _pipe


def transcribe(audio_path: str) -> dict:
    """
    Tumatanggap ng path sa isang 16kHz mono WAV file (dapat na-convert na
    via ffmpeg bago ito tawagin -- tingnan ang `/api/stt` sa main.py, na
    kumukuha ng raw na audio mula sa browser at kino-convert muna gamit
    ang parehong hakbang na ginagamit ng convert_audio.py). Nagbabalik ng
    dict:
      - {"text": "..."} kapag matagumpay
      - {"error": "..."} kapag may problema (hindi ma-load ang modelo,
        walang malinaw na narinig sa audio, atbp.)
    Sinadyang hindi nag-raise ng exception papunta sa API layer -- parehong
    istilo ng error-signalling na ginagamit na ng gemini_engine.respond()
    (laging may malinaw, Taglish na paliwanag ang user sa halip na generic
    server error).
    """
    pipe = get_pipeline()
    if pipe is None:
        return {
            "error": (
                "Hindi ma-initialize ang speech-to-text ("
                + (_init_error or "hindi alam ang dahilan")
                + "). I-type na lang muna ang tanong sa ngayon."
            )
        }
    try:
        start = time.monotonic()
        result = pipe(audio_path)
        elapsed = time.monotonic() - start
        print(f"[stt_engine] Na-transcribe sa {elapsed:.1f}s.")
        text = (result.get("text") or "").strip()
        if not text:
            return {
                "error": "Walang malinaw na narinig sa recording. Subukan ulit, "
                         "o i-type na lang ang tanong."
            }
        return {"text": text}
    except Exception as e:  # noqa: BLE001 -- tingnan ang paliwanag sa itaas
        return {"error": f"May problema sa pagproseso ng audio: {e}"}
