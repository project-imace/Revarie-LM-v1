"""
consolidation_orchestrator.py
Memory Consolidation – Consolidation Orchestrator.
Coordinates the nightly memory consolidation process: fetches daily sessions,
generates summaries, updates vector embeddings, and schedules decay.
Based on sleep-dependent memory consolidation theories.

Theoretical foundations:
- Stickgold & Walker (2013): Sleep-dependent memory triage.
- McClelland et al. (1995): Complementary learning systems.
- Diekelmann & Born (2010): The memory function of sleep.
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class ConsolidationPhase(Enum):
    FETCH = "fetch"
    SUMMARIZE = "summarize"
    EMBED = "embed"
    UPSERT = "upsert"
    DECAY = "decay"
    COMPLETE = "complete"


@dataclass
class ConsolidationTask:
    participant_id: str
    name: str
    study_group: str
    day_number: int
    session_date: str
    pre_vams: Dict[str, int]
    post_vams: Dict[str, int]
    chat_messages: List[Dict[str, str]]
    phase: ConsolidationPhase = ConsolidationPhase.FETCH
    summary: Optional[str] = None
    embedding: Optional[List[float]] = None
    error: Optional[str] = None
    retry_count: int = 0
    max_retries: int = 3


class ConsolidationOrchestrator:
    """
    Orchestrates the full nightly memory consolidation pipeline.
    """

    def __init__(
        self,
        d1_client,
        vector_store_client,
        embedding_generator,
        llm_client=None,
        decay_scheduler=None,
        max_concurrent: int = 5,
    ):
        self.d1 = d1_client
        self.vector_store = vector_store_client
        self.embedder = embedding_generator
        self.llm = llm_client
        self.decay_scheduler = decay_scheduler
        self.max_concurrent = max_concurrent
        self.semaphore = asyncio.Semaphore(max_concurrent)
        self.stats = {
            "total": 0,
            "succeeded": 0,
            "failed": 0,
            "skipped": 0,
        }

    async def run(self, target_date: Optional[str] = None) -> Dict[str, Any]:
        """
        Run the full consolidation pipeline for a given date (default: yesterday IST).
        """
        if target_date is None:
            ist_now = datetime.utcnow() + timedelta(hours=5, minutes=30)
            target_date = (ist_now - timedelta(days=1)).strftime("%Y-%m-%d")

        logger.info(f"Starting consolidation for {target_date}")

        # Phase 1: Fetch sessions
        tasks = await self._fetch_sessions(target_date)
        self.stats["total"] = len(tasks)
        logger.info(f"Fetched {len(tasks)} sessions")

        if not tasks:
            logger.info("No sessions to consolidate")
            return self.stats

        # Phase 2: Generate summaries
        tasks = await self._process_phase(tasks, ConsolidationPhase.SUMMARIZE)

        # Phase 3: Generate embeddings
        tasks = await self._process_phase(tasks, ConsolidationPhase.EMBED)

        # Phase 4: Upsert to vector store
        tasks = await self._process_phase(tasks, ConsolidationPhase.UPSERT)

        # Phase 5: Apply decay
        if self.decay_scheduler:
            await self._apply_decay()

        self.stats["succeeded"] = sum(1 for t in tasks if t.phase == ConsolidationPhase.COMPLETE)
        self.stats["failed"] = sum(1 for t in tasks if t.error)
        self.stats["skipped"] = sum(1 for t in tasks if t.phase != ConsolidationPhase.COMPLETE and not t.error)

        logger.info(f"Consolidation complete: {self.stats}")
        return self.stats

    async def _fetch_sessions(self, target_date: str) -> List[ConsolidationTask]:
        """Fetch all participant sessions for a given date."""
        try:
            sessions_data = await self.d1.get_sessions_by_date(target_date)
        except Exception as e:
            logger.error(f"Failed to fetch sessions: {e}")
            return []

        tasks = []
        for sess in sessions_data:
            task = ConsolidationTask(
                participant_id=sess["participant_id"],
                name=sess.get("name", ""),
                study_group=sess.get("study_group", "A"),
                day_number=sess["day_number"],
                session_date=sess["session_date_ist"],
                pre_vams=sess.get("pre_vams", {}),
                post_vams=sess.get("post_vams", {}),
                chat_messages=sess.get("chat_messages", []),
            )
            tasks.append(task)
        return tasks

    async def _process_phase(self, tasks: List[ConsolidationTask], phase: ConsolidationPhase) -> List[ConsolidationTask]:
        """Process all tasks through a specific phase concurrently."""
        async def process_one(task: ConsolidationTask) -> ConsolidationTask:
            async with self.semaphore:
                if task.error:
                    return task
                task.phase = phase
                try:
                    if phase == ConsolidationPhase.SUMMARIZE:
                        task.summary = await self._generate_summary(task)
                    elif phase == ConsolidationPhase.EMBED:
                        task.embedding = await self._generate_embedding(task)
                    elif phase == ConsolidationPhase.UPSERT:
                        await self._upsert_vector(task)
                        task.phase = ConsolidationPhase.COMPLETE
                except Exception as e:
                    task.error = str(e)
                    task.retry_count += 1
                    logger.error(f"Failed {phase.value} for {task.participant_id}: {e}")
                return task

        return await asyncio.gather(*[process_one(t) for t in tasks])

    async def _generate_summary(self, task: ConsolidationTask) -> str:
        """Generate a daily summary using LLM."""
        if not self.llm:
            return self._fallback_summary(task)

        convo = "\n".join([f"{msg['role']}: {msg['content']}" for msg in task.chat_messages[:30]])
        
        if task.study_group == "A":
            prompt = f"""You are Samara. Create a warm, personal summary of today's conversation with {task.name}.
Note their emotions and personal details. Use their name.
Conversation:
{convo}
Summary:"""
        else:
            prompt = f"""You are Artery. Create a factual summary of today's interaction.
Be neutral. Omit names and emotions.
Conversation:
{convo}
Summary:"""

        summary = await self.llm.generate(prompt, max_tokens=300)
        return summary.strip()

    def _fallback_summary(self, task: ConsolidationTask) -> str:
        """Fallback summary when LLM is unavailable."""
        if task.study_group == "A":
            return f"{task.name} participated in Day {task.day_number} session."
        else:
            return f"Participant {task.participant_id} completed Day {task.day_number} session."

    async def _generate_embedding(self, task: ConsolidationTask) -> List[float]:
        """Generate vector embedding for summary."""
        return await self.embedder.embed_single(task.summary)

    async def _upsert_vector(self, task: ConsolidationTask):
        """Upsert summary vector to vector store."""
        import hashlib
        vector_id = f"{task.participant_id}_{task.day_number}_summary_{hashlib.md5(task.summary.encode()).hexdigest()[:8]}"
        await self.vector_store.upsert(
            namespace=f"participant_{task.participant_id}",
            vectors=[{
                "id": vector_id,
                "values": task.embedding,
                "metadata": {
                    "participant_id": task.participant_id,
                    "day_number": task.day_number,
                    "memory_type": "daily_summary",
                    "session_date": task.session_date,
                    "study_group": task.study_group,
                }
            }]
        )
        # Also update D1 with summary text
        await self.d1.save_summary(task.participant_id, task.day_number, task.summary)

    async def _apply_decay(self):
        """Apply memory decay to older vectors."""
        if self.decay_scheduler:
            await self.decay_scheduler.apply_decay()
