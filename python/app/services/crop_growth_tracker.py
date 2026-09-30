"""
Crop growth tracking: splits a crop's planting -> harvest window into growth stages (crop_milestones rows),
tracks progress, and gives stage-specific advice.

Named crop_growth_tracker.py on purpose: `crop_milestone_service.py` is the generated CRUD service and
`php setup.php` overwrites it (which is how the original milestone logic was lost).
"""

import logging
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional

from app.core.db import DB
from app.core.ownership import owner_condition

logger = logging.getLogger(__name__)

# (stage, share of the season, advice). Shares add up to 1.0.
STAGES = [
    (
        "germination",
        0.10,
        "Keep soil moist but not waterlogged; check for uneven emergence and gap-fill early.",
    ),
    (
        "vegetative",
        0.30,
        "Apply the first nitrogen top dressing, weed at 20-30 days, and scout for leaf-eating pests.",
    ),
    (
        "flowering",
        0.20,
        "Avoid water stress; irrigate at critical flowering stage and watch for flower drop or blight.",
    ),
    (
        "grain_filling",
        0.25,
        "Maintain moisture, apply potash if deficient, and protect against pod/ear borers.",
    ),
    (
        "maturity",
        0.10,
        "Stop irrigation 10-15 days before harvest; watch for lodging and bird damage.",
    ),
    (
        "harvest",
        0.05,
        "Harvest at physiological maturity, dry to safe moisture, and store in clean, dry bags.",
    ),
]
ADVICE = {name: text for name, _, text in STAGES}


def _d(v) -> date:
    return v.date() if isinstance(v, datetime) else v


def _iso(v):
    return v.isoformat() if hasattr(v, "isoformat") else v


class CropGrowthTracker:
    def _crop(self, crop_id: int, user=None) -> Optional[Dict[str, Any]]:
        sql, bind = "SELECT * FROM crops t WHERE t.id = ?", [crop_id]
        if user is not None and getattr(user, "user_type", None) != "admin":
            sql += f" AND {owner_condition('crops', user.id)}"
        rows = DB.raw(sql, bind).result
        return rows[0] if rows else None

    def _milestones(self, crop_id: int) -> List[Dict[str, Any]]:
        return DB.raw(
            "SELECT * FROM crop_milestones WHERE crop_id = ? ORDER BY expected_start_date",
            [crop_id],
        ).result

    @staticmethod
    def _status_for(start: date, end: date, today: date) -> str:
        if today > end:
            return "completed"
        if today >= start:
            return "in_progress"
        return "pending"

    async def create_milestones_for_crop(
        self, crop_id: int, crop_name: str, planting_date, expected_harvest_date, user=None
    ) -> List[Dict[str, Any]]:
        if not self._crop(crop_id, user):
            raise LookupError("Crop not found")
        existing = self._milestones(crop_id)
        if existing:
            return existing
        start, end = _d(planting_date), _d(expected_harvest_date)
        if end <= start:
            raise ValueError("Harvest date must be after planting date")
        total = (end - start).days
        today, cursor, created = date.today(), start, []
        for i, (stage, share, advice) in enumerate(STAGES):
            stage_end = (
                end
                if i == len(STAGES) - 1
                else cursor + timedelta(days=max(1, round(total * share)))
            )
            created.append(
                DB.raw(
                    """INSERT INTO crop_milestones (crop_id, stage, expected_start_date, expected_end_date, status,
                   progress_percentage, recommendations) VALUES (?, ?, ?, ?, ?, ?, ?) RETURNING *""",
                    [
                        crop_id,
                        stage,
                        cursor,
                        stage_end,
                        self._status_for(cursor, stage_end, today),
                        100 if today > stage_end else 0,
                        f"{crop_name}: {advice}",
                    ],
                ).result[0]
            )
            cursor = stage_end
        return created

    async def ensure_for_crop(self, crop_id: int, user=None) -> List[Dict[str, Any]]:
        crop = self._crop(crop_id, user)
        if not crop:
            raise LookupError("Crop not found")
        return self._milestones(crop_id) or await self.create_milestones_for_crop(
            crop_id, crop["crop_name"], crop["planting_date"], crop["expected_harvest_date"], user
        )

    async def update_milestone_progress(
        self,
        milestone_id: int,
        progress_percentage: int,
        actual_start_date=None,
        actual_end_date=None,
        notes: Optional[str] = None,
        user=None,
    ) -> Dict[str, Any]:
        rows = DB.raw("SELECT * FROM crop_milestones WHERE id = ?", [milestone_id]).result
        if not rows or not self._crop(rows[0]["crop_id"], user):
            raise LookupError("Milestone not found")
        m = rows[0]
        status = (
            "completed"
            if progress_percentage >= 100
            else ("in_progress" if progress_percentage > 0 else m["status"])
        )
        return DB.raw(
            """UPDATE crop_milestones SET progress_percentage = ?, status = ?,
               actual_start_date = COALESCE(?, actual_start_date, CASE WHEN ? > 0 THEN CURRENT_DATE END),
               actual_end_date = COALESCE(?, actual_end_date, CASE WHEN ? >= 100 THEN CURRENT_DATE END),
               notes = COALESCE(?, notes), "updated_at" = CURRENT_TIMESTAMP WHERE id = ? RETURNING *""",
            [
                progress_percentage,
                status,
                actual_start_date,
                progress_percentage,
                actual_end_date,
                progress_percentage,
                notes,
                milestone_id,
            ],
        ).result[0]

    async def get_current_stage(self, crop_id: int, user=None) -> Optional[Dict[str, Any]]:
        milestones = await self.ensure_for_crop(crop_id, user)
        today = date.today()
        for m in milestones:
            if (
                _d(m["expected_start_date"]) <= today <= _d(m["expected_end_date"])
                or m["status"] == "in_progress"
            ):
                span = max((_d(m["expected_end_date"]) - _d(m["expected_start_date"])).days, 1)
                elapsed = min(max((today - _d(m["expected_start_date"])).days, 0), span)
                progress = m["progress_percentage"] or round(100 * elapsed / span)
                return {
                    **m,
                    "progress_percentage": progress,
                    "days_remaining": max((_d(m["expected_end_date"]) - today).days, 0),
                }
        return None

    async def get_milestone_recommendations(
        self, crop_id: int, stage: Optional[str] = None, user=None
    ) -> Dict[str, Any]:
        try:
            current = await self.get_current_stage(crop_id, user)
        except LookupError:
            return {"error": "Crop not found"}
        stage = stage or (current or {}).get("stage")
        if not stage:
            return {"error": "No active growth stage"}
        if stage not in ADVICE:
            return {"error": f"Unknown stage '{stage}'"}
        return {
            "crop_id": crop_id,
            "stage": stage,
            "recommendations": ADVICE[stage],
            "is_current_stage": bool(current and current["stage"] == stage),
        }

    async def send_stage_transition_alert(
        self,
        crop_id: int,
        farmer_phone: str,
        farmer_email: Optional[str],
        farmer_name: str,
        crop_name: str,
        new_stage: str,
        recommendations: str,
    ) -> Dict[str, Any]:
        crop = DB.raw(
            """SELECT f.user_id FROM crops c JOIN farm_plots p ON p.id = c.farm_plot_id
                         JOIN farms f ON f.id = p.farm_id WHERE c.id = ?""",
            [crop_id],
        ).result
        pushed = None
        if crop:
            try:
                from app.services.notification_service import get_notification_service

                pushed = get_notification_service()._push_to_user(
                    crop[0]["user_id"],
                    f"{crop_name}: {new_stage.replace('_', ' ')} stage",
                    recommendations,
                    "harvest_reminder",
                )
            except Exception as e:
                logger.warning(f"Stage alert push failed for crop {crop_id}: {e}")
        DB.raw(
            "UPDATE crop_milestones SET alert_sent = 1 WHERE crop_id = ? AND stage = ?",
            [crop_id, new_stage],
        )
        return {"success": True, "crop_id": crop_id, "stage": new_stage, "web_push": pushed}

    async def get_progress_dashboard(self, crop_id: int, user=None) -> Dict[str, Any]:
        crop = self._crop(crop_id, user)
        if not crop:
            return {"error": "Crop not found"}
        milestones = await self.ensure_for_crop(crop_id, user)
        current = await self.get_current_stage(crop_id, user)
        start, end, today = (
            _d(crop["planting_date"]),
            _d(crop["expected_harvest_date"]),
            date.today(),
        )
        total = max((end - start).days, 1)
        summary: Dict[str, int] = {}
        for m in milestones:
            summary[m["status"]] = summary.get(m["status"], 0) + 1
        return {
            "crop_id": crop_id,
            "crop_name": crop["crop_name"],
            "crop_variety": crop.get("crop_variety"),
            "planting_date": _iso(start),
            "expected_harvest_date": _iso(end),
            "days_to_harvest": max((end - today).days, 0),
            "overall_progress": round(min(max((today - start).days / total, 0), 1) * 100, 1),
            "current_stage": current["stage"] if current else None,
            "milestones": [{k: _iso(v) for k, v in m.items()} for m in milestones],
            "status_summary": summary,
        }

    async def check_and_update_stages(self) -> Dict[str, Any]:
        """Daily job: move milestones to in_progress/completed by date."""
        today = date.today()
        started = DB.raw(
            """UPDATE crop_milestones SET status = 'in_progress', actual_start_date = COALESCE(actual_start_date, CURRENT_DATE)
                            WHERE status = 'pending' AND expected_start_date <= ? AND expected_end_date >= ? RETURNING id""",
            [today, today],
        ).result
        finished = DB.raw(
            """UPDATE crop_milestones SET status = 'completed', progress_percentage = 100,
                             actual_end_date = COALESCE(actual_end_date, expected_end_date)
                             WHERE status IN ('pending', 'in_progress') AND expected_end_date < ? RETURNING id""",
            [today],
        ).result
        return {"started": len(started), "completed": len(finished)}


crop_growth_tracker = CropGrowthTracker()


def get_crop_growth_tracker(db=None) -> CropGrowthTracker:
    return crop_growth_tracker
