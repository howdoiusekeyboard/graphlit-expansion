"""Backfill citation edges and expand the paper graph.

Fixes citation density by:
1. Fetching references for all existing papers via individual lookups
   (batch API truncates referenced_works to ~8 items)
2. Adding referenced papers not yet in Neo4j (with authors, venues, topics)
3. Creating CITES edges between all papers that exist in the graph

Usage:
    source .env.cloud && python backfill_citations.py
"""

from __future__ import annotations

import asyncio
from typing import Any

from graphlit.clients.openalex import OpenAlexClient
from graphlit.config import get_settings
from graphlit.database.neo4j_client import Neo4jClient
from graphlit.pipeline.mapper import Mapper


async def main() -> None:
    print("=" * 60)
    print("GraphLit Citation Backfill")
    print("=" * 60)

    settings = get_settings()
    mapper = Mapper(settings.expansion)

    async with OpenAlexClient(settings.openalex) as api:
        async with Neo4jClient(settings.neo4j) as db:
            # ---- Phase 1: Inventory ----
            existing_ids = await db.get_all_paper_ids()
            valid_ids = sorted(pid for pid in existing_ids if pid.startswith("W"))
            print(f"\nPhase 1: {len(valid_ids)} papers in database")

            stats = await db.get_graph_stats()
            print(f"  Current citations: {stats['citations']}")

            # ---- Phase 2: Fetch references via individual lookups ----
            # (batch API truncates referenced_works to ~8; singles return full ~50)
            print(f"\nPhase 2: Fetching references for {len(valid_ids)} papers...")
            all_citations: list[tuple[str, str]] = []
            new_paper_ids: set[str] = set()
            fetched_count = 0
            total_refs = 0

            sem = asyncio.Semaphore(settings.expansion.concurrent_fetches)

            async def fetch_single(pid: str) -> tuple[str, dict[str, Any] | None]:
                async with sem:
                    work = await api.get_work(pid)
                return (pid, work)

            # Process in waves of 200 concurrent individual lookups
            wave_size = 200
            for i in range(0, len(valid_ids), wave_size):
                wave = valid_ids[i : i + wave_size]
                tasks = [fetch_single(pid) for pid in wave]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                for res in results:
                    if isinstance(res, BaseException):
                        continue
                    pid, work = res
                    fetched_count += 1
                    if not work:
                        continue
                    ref_ids = mapper.get_reference_ids(work, limit=100)
                    total_refs += len(ref_ids)
                    for ref_id in ref_ids:
                        all_citations.append((pid, ref_id))
                        if ref_id not in existing_ids:
                            new_paper_ids.add(ref_id)

                done = min(i + wave_size, len(valid_ids))
                in_db = sum(1 for _, cited in all_citations if cited in existing_ids)
                print(
                    f"  {done}/{len(valid_ids)} papers | "
                    f"{total_refs} refs total | "
                    f"{in_db} in-DB | "
                    f"{len(new_paper_ids)} new"
                )

            print(f"\n  API returned: {fetched_count}/{len(valid_ids)} papers")
            print(f"  Total references: {total_refs}")
            print(
                f"  References to papers in DB: "
                f"{sum(1 for _, c in all_citations if c in existing_ids)}"
            )
            print(f"  New papers discovered: {len(new_paper_ids)}")

            # ---- Phase 3: Add new referenced papers ----
            room = max(0, settings.expansion.max_papers - len(existing_ids))
            to_add = sorted(new_paper_ids)[:room] if room > 0 else []
            print(f"\nPhase 3: Adding {len(to_add)} new papers (room={room})...")

            added = 0
            for i in range(0, len(to_add), 500):
                wave = to_add[i : i + 500]
                chunks = [wave[j : j + 50] for j in range(0, len(wave), 50)]

                async def fetch_new_chunk(
                    chunk_ids: list[str],
                ) -> list[dict[str, Any]]:
                    async with sem:
                        return await api.get_works_batch(chunk_ids)

                tasks = [fetch_new_chunk(chunk) for chunk in chunks]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                papers_batch: list[dict[str, Any]] = []
                authors_batch: list[dict[str, Any]] = []
                authorships_batch: list[dict[str, Any]] = []
                venues_batch: list[dict[str, Any]] = []
                publications_batch: list[dict[str, Any]] = []
                topics_batch: list[dict[str, Any]] = []
                topic_assignments_batch: list[dict[str, Any]] = []

                for res in results:
                    if isinstance(res, BaseException):
                        continue
                    for work in res:
                        try:
                            oid = mapper.extract_id(work["id"])
                            if not oid.startswith("W"):
                                continue
                            year = work.get("publication_year")
                            if not year:
                                continue

                            paper = mapper.map_paper(work)
                            papers_batch.append(
                                {
                                    "openalex_id": paper.openalex_id,
                                    "doi": paper.doi,
                                    "title": paper.title,
                                    "year": paper.year,
                                    "citations": paper.citations,
                                    "abstract": paper.abstract,
                                }
                            )
                            for author, position in mapper.map_authors(work):
                                authors_batch.append(
                                    {
                                        "openalex_id": author.openalex_id,
                                        "name": author.name,
                                        "orcid": author.orcid,
                                        "institution": author.institution,
                                    }
                                )
                                authorships_batch.append(
                                    {
                                        "paper_id": paper.openalex_id,
                                        "author_id": author.openalex_id,
                                        "position": position,
                                    }
                                )
                            venue = mapper.map_venue(work)
                            if venue:
                                venues_batch.append(
                                    {
                                        "openalex_id": venue.openalex_id,
                                        "name": venue.name,
                                        "venue_type": venue.venue_type,
                                        "publisher": venue.publisher,
                                    }
                                )
                                publications_batch.append(
                                    {
                                        "paper_id": paper.openalex_id,
                                        "venue_id": venue.openalex_id,
                                    }
                                )
                            for topic, score in mapper.map_topics(work):
                                topics_batch.append(
                                    {
                                        "openalex_id": topic.openalex_id,
                                        "name": topic.name,
                                        "level": topic.level,
                                    }
                                )
                                topic_assignments_batch.append(
                                    {
                                        "paper_id": paper.openalex_id,
                                        "topic_id": topic.openalex_id,
                                        "score": score,
                                    }
                                )

                            ref_ids = mapper.get_reference_ids(work, limit=100)
                            for ref_id in ref_ids:
                                all_citations.append((oid, ref_id))
                        except Exception:
                            pass

                bs = settings.expansion.neo4j_batch_size
                if papers_batch:
                    await db.upsert_papers_batch(papers_batch, batch_size=bs)
                    added += len(papers_batch)
                if authors_batch:
                    await db.upsert_authors_batch(authors_batch, batch_size=bs)
                if venues_batch:
                    await db.upsert_venues_batch(venues_batch, batch_size=bs)
                if topics_batch:
                    await db.upsert_topics_batch(topics_batch, batch_size=bs)
                if authorships_batch:
                    await db.create_authorships_batch(authorships_batch, batch_size=bs)
                if publications_batch:
                    await db.create_publications_batch(publications_batch, batch_size=bs)
                if topic_assignments_batch:
                    await db.create_topic_assignments_batch(topic_assignments_batch, batch_size=bs)

                done = min(i + 500, len(to_add))
                print(f"  {done}/{len(to_add)} fetched | {added} papers added to DB")

            # ---- Phase 4: Create citation edges ----
            all_paper_ids = await db.get_all_paper_ids()
            print("\nPhase 4: Creating citation edges...")
            print(f"  Papers in DB now: {len(all_paper_ids)}")

            valid_citations: list[dict[str, str]] = []
            seen: set[tuple[str, str]] = set()
            for citing, cited in all_citations:
                if cited in all_paper_ids and citing != cited:
                    pair = (citing, cited)
                    if pair not in seen:
                        seen.add(pair)
                        valid_citations.append({"citing_id": citing, "cited_id": cited})

            print(f"  Valid citation edges: {len(valid_citations)}")

            if valid_citations:
                bs = settings.expansion.neo4j_batch_size
                await db.create_citations_batch(valid_citations, batch_size=bs)
                print("  Written to Neo4j!")

            # ---- Final stats ----
            final_stats = await db.get_graph_stats()
            print(f"\n{'=' * 60}")
            print("DONE!")
            print(f"  Papers:   {final_stats['papers']}")
            print(f"  Authors:  {final_stats['authors']}")
            print(f"  Venues:   {final_stats['venues']}")
            print(f"  Topics:   {final_stats['topics']}")
            print(f"  Citations: {final_stats['citations']}")
            print(f"{'=' * 60}")
            print("\nNext: python run_community_detection.py")


if __name__ == "__main__":
    asyncio.run(main())
