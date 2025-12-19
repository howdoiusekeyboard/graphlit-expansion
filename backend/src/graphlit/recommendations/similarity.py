"""Pure similarity calculation functions for recommendation engine.

This module provides mathematical similarity metrics for comparing research papers.
All functions are pure (no I/O) and return scores in [0.0, 1.0] range where:
- 0.0 = completely dissimilar
- 1.0 = identical or maximally similar

These functions are used by the collaborative filtering and content-based
recommendation engines to compute paper similarity scores.

Usage:
    >>> from graphlit.recommendations.similarity import jaccard_similarity
    >>>
    >>> set_a = {"W1", "W2", "W3"}
    >>> set_b = {"W2", "W3", "W4"}
    >>> jaccard_similarity(set_a, set_b)
    0.5
"""

from __future__ import annotations

import math


def jaccard_similarity(set_a: set[str], set_b: set[str]) -> float:
    """Calculate Jaccard similarity coefficient between two sets.

    The Jaccard coefficient measures the overlap between two sets:
    J(A, B) = |A ∩ B| / |A ∪ B|

    This is used to compare papers based on:
    - Citation overlap (papers citing the same references)
    - Author overlap (papers sharing authors)
    - Topic overlap (papers in the same topics)

    Args:
        set_a: First set of elements (paper IDs, author IDs, etc.)
        set_b: Second set of elements

    Returns:
        Jaccard coefficient in [0.0, 1.0] where:
        - 0.0 = no overlap
        - 1.0 = identical sets

    Examples:
        >>> jaccard_similarity({"A", "B", "C"}, {"B", "C", "D"})
        0.5
        >>> jaccard_similarity({"A"}, {"B"})
        0.0
        >>> jaccard_similarity(set(), set())
        0.0
        >>> jaccard_similarity({"A", "B"}, {"A", "B"})
        1.0
    """
    # Handle empty sets
    if not set_a and not set_b:
        return 0.0

    if not set_a or not set_b:
        return 0.0

    intersection = len(set_a & set_b)
    union = len(set_a | set_b)

    if union == 0:
        return 0.0

    return float(intersection) / float(union)


def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    """Calculate cosine similarity between two vectors.

    Cosine similarity measures the angle between two vectors:
    cos(θ) = (A · B) / (||A|| × ||B||)

    This is used to compare papers based on:
    - Topic distribution vectors (weighted topic scores)
    - Citation velocity vectors (temporal citation patterns)
    - Author reputation vectors (h-index proxies)

    Args:
        vec_a: First vector (must be same length as vec_b)
        vec_b: Second vector (must be same length as vec_a)

    Returns:
        Cosine similarity in [0.0, 1.0] where:
        - 0.0 = orthogonal vectors (completely different)
        - 1.0 = parallel vectors (identical direction)

    Raises:
        ValueError: If vectors have different lengths or are empty

    Examples:
        >>> cosine_similarity([1.0, 2.0, 3.0], [1.0, 2.0, 3.0])
        1.0
        >>> cosine_similarity([1.0, 0.0], [0.0, 1.0])
        0.0
        >>> cosine_similarity([1.0, 1.0], [2.0, 2.0])
        1.0
    """
    if not vec_a or not vec_b:
        raise ValueError("Vectors cannot be empty")

    if len(vec_a) != len(vec_b):
        raise ValueError(f"Vectors must have same length: {len(vec_a)} != {len(vec_b)}")

    # Compute dot product
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

    # Compute magnitudes
    magnitude_a = math.sqrt(sum(a * a for a in vec_a))
    magnitude_b = math.sqrt(sum(b * b for b in vec_b))

    # Handle zero vectors
    if magnitude_a == 0.0 or magnitude_b == 0.0:
        return 0.0

    # Cosine similarity
    similarity = dot_product / (magnitude_a * magnitude_b)

    # Clamp to [0.0, 1.0] (should already be in range, but handles floating point errors)
    # Note: We clamp to [0.0, 1.0] instead of [-1.0, 1.0] because we only care about
    # similarity (positive correlation) for recommendations
    return max(0.0, min(1.0, similarity))


def topic_affinity_score(
    topics_a: list[tuple[str, float]],
    topics_b: list[tuple[str, float]],
) -> float:
    """Calculate weighted topic affinity score between two papers.

    This computes the overlap in topic distributions, weighted by topic scores.
    Unlike simple Jaccard similarity on topic sets, this accounts for the
    strength of topic assignments (score from OpenAlex topic classification).

    Algorithm:
    1. Build topic score dictionaries
    2. Find shared topics
    3. For each shared topic, take min(score_a, score_b) as overlap contribution
    4. Normalize by average total topic weight

    Args:
        topics_a: List of (topic_id, score) tuples for first paper
        topics_b: List of (topic_id, score) tuples for second paper

    Returns:
        Topic affinity score in [0.0, 1.0] where:
        - 0.0 = no shared topics
        - 1.0 = identical topic distributions

    Examples:
        >>> topics_a = [("T1", 0.8), ("T2", 0.6)]
        >>> topics_b = [("T2", 0.5), ("T3", 0.7)]
        >>> topic_affinity_score(topics_a, topics_b)  # Shared: T2
        0.3571...

        >>> topics_a = [("T1", 1.0)]
        >>> topics_b = [("T1", 1.0)]
        >>> topic_affinity_score(topics_a, topics_b)
        1.0

        >>> topics_a = [("T1", 0.5)]
        >>> topics_b = [("T2", 0.5)]
        >>> topic_affinity_score(topics_a, topics_b)
        0.0
    """
    # Handle empty topic lists
    if not topics_a or not topics_b:
        return 0.0

    # Build topic score dictionaries
    scores_a = {topic_id: score for topic_id, score in topics_a}
    scores_b = {topic_id: score for topic_id, score in topics_b}

    # Find shared topics
    shared_topics = set(scores_a.keys()) & set(scores_b.keys())

    if not shared_topics:
        return 0.0

    # Compute weighted overlap
    # For each shared topic, take the minimum score as the overlap contribution
    overlap = sum(min(scores_a[topic], scores_b[topic]) for topic in shared_topics)

    # Compute normalization factor (average total topic weight)
    total_a = sum(scores_a.values())
    total_b = sum(scores_b.values())

    if total_a == 0.0 or total_b == 0.0:
        return 0.0

    normalization = (total_a + total_b) / 2.0

    # Normalized affinity score
    affinity = overlap / normalization

    # Clamp to [0.0, 1.0] (should already be in range)
    return max(0.0, min(1.0, affinity))


def citation_velocity_similarity(
    velocity_a: float,
    velocity_b: float,
    max_diff: float = 10.0,
) -> float:
    """Calculate similarity between two citation velocity values.

    Citation velocity = citations per year since publication.
    Papers with similar growth patterns are likely related (both emerging,
    both established, etc.).

    This uses an exponential decay function where papers with closer
    velocities get higher similarity scores.

    Formula:
    similarity = exp(-|velocity_a - velocity_b| / max_diff)

    Args:
        velocity_a: First paper's citation velocity (citations/year)
        velocity_b: Second paper's citation velocity (citations/year)
        max_diff: Maximum velocity difference to consider (default: 10.0)
                  Differences larger than this decay to near zero

    Returns:
        Velocity similarity in [0.0, 1.0] where:
        - 1.0 = identical velocities
        - 0.37 = velocities differ by max_diff
        - ~0.0 = velocities very different

    Examples:
        >>> citation_velocity_similarity(5.0, 5.0)
        1.0
        >>> citation_velocity_similarity(5.0, 15.0)  # Differ by max_diff=10
        0.367...
        >>> citation_velocity_similarity(0.0, 100.0)
        0.0
        >>> citation_velocity_similarity(10.5, 10.6, max_diff=1.0)
        0.904...
    """
    # Handle negative velocities (shouldn't happen, but be defensive)
    if velocity_a < 0.0 or velocity_b < 0.0:
        return 0.0

    # Compute absolute difference
    diff = abs(velocity_a - velocity_b)

    # Exponential decay similarity
    # e^0 = 1.0 (identical), e^-1 ≈ 0.37 (max_diff apart), e^-∞ → 0.0
    similarity = math.exp(-diff / max_diff)

    # Clamp to [0.0, 1.0] (should already be in range)
    return max(0.0, min(1.0, similarity))


def weighted_combination(
    scores: dict[str, float],
    weights: dict[str, float],
) -> float:
    """Combine multiple similarity scores using weighted average.

    This is used by the collaborative filtering engine to combine
    different similarity methods (citation-based, topic-based, etc.)
    into a final composite score.

    Args:
        scores: Dictionary mapping score name → score value (0-1)
        weights: Dictionary mapping score name → weight (must sum to 1.0)

    Returns:
        Weighted average in [0.0, 1.0]

    Raises:
        ValueError: If weights don't sum to approximately 1.0 (±0.01)
                    or if score keys don't match weight keys

    Examples:
        >>> scores = {"citation": 0.8, "topic": 0.6}
        >>> weights = {"citation": 0.5, "topic": 0.5}
        >>> weighted_combination(scores, weights)
        0.7

        >>> scores = {"a": 1.0, "b": 0.0, "c": 0.5}
        >>> weights = {"a": 0.5, "b": 0.3, "c": 0.2}
        >>> weighted_combination(scores, weights)
        0.6
    """
    # Validate keys match
    if set(scores.keys()) != set(weights.keys()):
        raise ValueError(
            f"Score keys {set(scores.keys())} must match weight keys {set(weights.keys())}"
        )

    # Validate weights sum to 1.0 (within tolerance)
    total_weight = sum(weights.values())
    if not (0.99 <= total_weight <= 1.01):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight:.4f}")

    # Compute weighted average
    weighted_sum = sum(scores[key] * weights[key] for key in scores)

    # Clamp to [0.0, 1.0] (should already be in range)
    return max(0.0, min(1.0, weighted_sum))
