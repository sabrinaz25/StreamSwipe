from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from scipy.sparse import csr_matrix

from app.storage.memory import MemoryStore, SessionState


# Item–item CF needs overlapping likes across sessions.
MIN_SESSIONS_WITH_LIKES = 2
MIN_DISTINCT_ITEMS = 3
MIN_INTERACTIONS = 8


@dataclass(slots=True)
class CFBundle:
    """Binary user×item matrix (rows = sessions with ≥1 like) and id orderings."""

    R: csr_matrix
    user_ids: list[str]
    item_ids: list[str]
    item_pos: dict[str, int]


def _build_csr_from_sessions(sessions: dict[str, SessionState]) -> tuple[csr_matrix, list[str], list[str], dict[str, int]] | None:
    user_source: list[tuple[str, str]] = []
    for sid, s in sessions.items():
        for iid in s.right_item_ids:
            user_source.append((sid, iid))

    if len(user_source) < MIN_INTERACTIONS:
        return None

    users = sorted({sid for sid, _ in user_source})
    items = sorted({iid for _, iid in user_source})
    if len(users) < MIN_SESSIONS_WITH_LIKES or len(items) < MIN_DISTINCT_ITEMS:
        return None

    u_pos = {u: i for i, u in enumerate(users)}
    i_pos = {it: j for j, it in enumerate(items)}

    rows = [u_pos[sid] for sid, _ in user_source]
    cols = [i_pos[iid] for _, iid in user_source]
    data = [1.0] * len(rows)

    mat = csr_matrix((data, (rows, cols)), shape=(len(users), len(items)), dtype=np.float64)
    item_pos = {it: j for j, it in enumerate(items)}
    return mat, users, items, item_pos


def refit_cf_if_needed(store: MemoryStore) -> None:
    """Rebuild sparse co-occurrence structure when swipe data changed."""
    if not store.cf_dirty and store.cf_bundle is not None:
        return

    built = _build_csr_from_sessions(store.sessions)
    if built is None:
        store.cf_bundle = None
        store.cf_dirty = False
        return

    mat, user_ids, item_ids, item_pos = built
    store.cf_bundle = CFBundle(R=mat, user_ids=user_ids, item_ids=item_ids, item_pos=item_pos)
    store.cf_dirty = False


def cf_dot_scores_for_session(store: MemoryStore, session_id: str, candidate_ids: set[str]) -> dict[str, float]:
    """
    Item–item scores: for each candidate column c, sum of cosines(c, l) over liked columns l
    in the training matrix (sessions that liked both items co-occur in dot(c,l)).
    """
    bundle = store.cf_bundle
    if bundle is None or not candidate_ids:
        return {}

    s = store.sessions.get(session_id)
    if not s or not s.right_item_ids:
        return {}

    like_cols = [bundle.item_pos[i] for i in s.right_item_ids if i in bundle.item_pos]
    if not like_cols:
        return {}

    R = bundle.R
    scores: dict[str, float] = {}
    eps = 1e-9

    for cid in candidate_ids:
        jc = bundle.item_pos.get(cid)
        if jc is None:
            continue
        col_c = R.getcol(jc)
        nc = float(np.sqrt(col_c.nnz)) + eps
        total = 0.0
        for jl in like_cols:
            if jl == jc:
                continue
            col_l = R.getcol(jl)
            nl = float(np.sqrt(col_l.nnz)) + eps
            co = float(col_c.T.dot(col_l)[0, 0])
            total += co / (nc * nl)
        scores[cid] = total
    return scores
