"""Example custom processor that converts text to uppercase."""

from pipecat.frames.frames import Frame, TextFrame
from pipecat.processors.frame_processor import FrameDirection, FrameProcessor


class UppercaseProcessor(FrameProcessor):
    """A simple processor that converts text frames to uppercase.
    
    This is an example processor for demonstrating the pipecat test command.
    """
    
    def __init__(self):
        super().__init__()
    
    async def process_frame(self, frame: Frame, direction: FrameDirection):
        await super().process_frame(frame, direction)
        
        # Only process TextFrames going downstream
        if isinstance(frame, TextFrame) and direction == FrameDirection.DOWNSTREAM:
            # Create a new frame with uppercase text
            uppercase_frame = TextFrame(text=frame.text.upper())
            await self.push_frame(uppercase_frame, direction)
        else:
            # Pass through all other frames unchanged
            await self.push_frame(frame, direction)
