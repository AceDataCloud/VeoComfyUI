"""Veo nodes for ComfyUI."""

from .nodes import (AceVeoEditObjects, AceVeoExtend, AceVeoGet1080p,
                    AceVeoImageToVideo, AceVeoIngredientsToVideo,
                    AceVeoLoadVideo, AceVeoReshoot, AceVeoRetrieve,
                    AceVeoRetrieveBatch, AceVeoTextToVideo, AceVeoUpsample)

NODE_CLASS_MAPPINGS = {
    "AceVeoTextToVideo": AceVeoTextToVideo,
    "AceVeoImageToVideo": AceVeoImageToVideo,
    "AceVeoIngredientsToVideo": AceVeoIngredientsToVideo,
    "AceVeoGet1080p": AceVeoGet1080p,
    "AceVeoExtend": AceVeoExtend,
    "AceVeoEditObjects": AceVeoEditObjects,
    "AceVeoReshoot": AceVeoReshoot,
    "AceVeoUpsample": AceVeoUpsample,
    "AceVeoRetrieve": AceVeoRetrieve,
    "AceVeoRetrieveBatch": AceVeoRetrieveBatch,
    "AceVeoLoadVideo": AceVeoLoadVideo,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "AceVeoTextToVideo": "Veo Text to Video (Ace Data Cloud)",
    "AceVeoImageToVideo": "Veo Image to Video (Ace Data Cloud)",
    "AceVeoIngredientsToVideo": "Veo Ingredients to Video (Ace Data Cloud)",
    "AceVeoGet1080p": "Veo Get 1080p (Ace Data Cloud)",
    "AceVeoExtend": "Veo Extend Video (Ace Data Cloud)",
    "AceVeoEditObjects": "Veo Edit Objects (Ace Data Cloud)",
    "AceVeoReshoot": "Veo Reshoot Video (Ace Data Cloud)",
    "AceVeoUpsample": "Veo Upsample Video (Ace Data Cloud)",
    "AceVeoRetrieve": "Veo Retrieve Task (Ace Data Cloud)",
    "AceVeoRetrieveBatch": "Veo Retrieve Tasks (Ace Data Cloud)",
    "AceVeoLoadVideo": "Veo Load Video (Ace Data Cloud)",
}

__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
