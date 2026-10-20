"""Funded initiatives (e.g. NSD-funded NSIA / CBF investments) as an assignable entity type."""
from app.extensions import db
from app.utils.datetime_helpers import utcnow


class Initiative(db.Model):
    """A funded initiative that reports on its own schedule.

    It is an entity like a country or a branch: assignments hold one status row per initiative
    (AssignmentEntityStatus.entity_type = 'initiative'), each with its own due date and its own answers.
    Details that belong to a specific fund (budget, contacts, logframe) live in the form data, not here.
    """
    __tablename__ = 'initiative'

    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), nullable=False, unique=True, index=True)
    title = db.Column(db.String(500), nullable=False)
    fund_type = db.Column(db.String(20), nullable=True, index=True)

    national_society_id = db.Column(
        db.Integer,
        db.ForeignKey('national_societies.id', ondelete='SET NULL'),
        nullable=True,
        index=True,
    )

    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)

    is_active = db.Column(db.Boolean, nullable=False, default=True, server_default=db.true())
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    national_society = db.relationship('NationalSociety', lazy='joined')

    @property
    def name(self):
        return f"{self.reference} – {self.title}"

    @property
    def country(self):
        return self.national_society.country if self.national_society else None

    def __repr__(self):
        return f'<Initiative {self.reference}>'
