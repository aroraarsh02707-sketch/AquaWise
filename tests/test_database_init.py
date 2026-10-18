from sqlalchemy import inspect

from app import create_app
from backend.models import User, db


def test_init_db_creates_all_model_tables_and_preserves_existing_user():
    app = create_app("testing")

    with app.app_context():
        # Simulate a partially initialized database with an existing account.
        User.__table__.create(db.engine)
        existing_user = User(name="Existing household", email="existing@example.com")
        existing_user.set_password("household-password")
        db.session.add(existing_user)
        db.session.commit()
        existing_user_id = existing_user.id

    result = app.test_cli_runner().invoke(args=["init-db"])

    assert result.exit_code == 0, result.output

    with app.app_context():
        table_names = set(inspect(db.engine).get_table_names())
        assert set(db.metadata.tables).issubset(table_names)
        preserved_user = db.session.get(User, existing_user_id)
        assert preserved_user is not None
        assert preserved_user.email == "existing@example.com"
        assert preserved_user.check_password("household-password")
