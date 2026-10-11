# Privacy

- Paid Veo nodes send prompts, public HTTPS reference image or mask URLs, existing video IDs, model choices, and the ComfyUI process's Ace Data Cloud key to the corresponding `https://api.acedata.cloud/veo/*` endpoint.
- Task lookup sends existing task IDs to `/veo/tasks`; it does not create another generation.
- Load Video downloads completed video from an allowlisted Ace Data Cloud CDN into memory for ComfyUI's native `VIDEO` type.
- This package does not save keys in workflows or logs. Generation and editing may consume Ace Data Cloud Credits; check the current service price first.
