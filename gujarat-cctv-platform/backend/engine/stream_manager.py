import asyncio
import logging
from typing import Dict, List, Optional
from ai.pipeline import VideoPipeline
from ai.stream_worker import RTSPStreamWorker

logger = logging.getLogger(__name__)

class StreamManager:
    def __init__(self, pipeline: VideoPipeline):
        self.pipeline = pipeline
        self.workers: Dict[str, RTSPStreamWorker] = {}

    async def start_stream(self, camera_id: str, rtsp_url: str, target_fps: int = 2, fallback_url: Optional[str] = None):
        if camera_id in self.workers:
            logger.info(f"Stream for {camera_id} is already running.")
            return

        worker = RTSPStreamWorker(camera_id, rtsp_url, VideoPipeline(), target_fps, fallback_url=fallback_url)
        self.workers[camera_id] = worker
        await worker.start()

    async def stop_stream(self, camera_id: str):
        if camera_id in self.workers:
            await self.workers[camera_id].stop()
            del self.workers[camera_id]
        else:
            logger.warning(f"No active stream worker found for {camera_id}.")

    async def stop_all(self):
        tasks = []
        for worker in self.workers.values():
            tasks.append(worker.stop())
        if tasks:
            await asyncio.gather(*tasks)
        self.workers.clear()

    def get_active_streams(self) -> List[str]:
        return list(self.workers.keys())

# Singleton instance
stream_manager = None

def get_stream_manager(pipeline=None) -> StreamManager:
    global stream_manager
    if stream_manager is None:
        if pipeline is None:
            pipeline = VideoPipeline()
        stream_manager = StreamManager(pipeline)
    return stream_manager
