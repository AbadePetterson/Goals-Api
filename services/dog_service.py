from sqlalchemy import func
from sqlalchemy.orm import Session

from models.dogs import DogDB
from models.procedure import ProcedureDB


def get_dogs_summary(db: Session):
    results = (
        db.query(
            func.to_char(DogDB.date_of_visit, 'Month').label("month_name"),
            (func.date_part('year', func.age(DogDB.birth_date)) * 12 + func.date_part('month', func.age(DogDB.birth_date))).label("age_in_months"),
            DogDB.name.label("dog_name"),
            ProcedureDB.name.label("procedure")
        )
        .join(ProcedureDB, DogDB.procedure_id == ProcedureDB.id)
        .order_by("month_name", "age_in_months")
        .all()
    )

    monthly_summary = {}
    for result in results:
        month = result.month_name.strip()
        if month not in monthly_summary:
            monthly_summary[month] = []

        monthly_summary[month].append({
            "dog_name": result.dog_name,
            "age_in_months": int(result.age_in_months),
            "procedure": result.procedure
        })

    return monthly_summary

