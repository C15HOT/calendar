from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from models import Base
from sqlalchemy import text


if __name__=='__main__':


    CONNECTION = 'postgresql+psycopg2://calendar:calendar@localhost/calendar'
    engine = create_engine(CONNECTION)
    Base.metadata.create_all(engine)

    event_create = text("CREATE OR REPLACE FUNCTION event_create_notify()"
               "RETURNS trigger AS "
               "$BODY$ "
               "BEGIN "
               "PERFORM pg_notify('event_create', row_to_json(NEW)::text);"
               "RETURN NEW;"
               "END;"
               "$BODY$ "
               "LANGUAGE plpgsql VOLATILE "
               "COST 100;"
               "ALTER FUNCTION event_create_notify() "
               "OWNER TO calendar;"
               "CREATE TRIGGER event_create_trigger "
               "AFTER INSERT "
               "ON events "
               "FOR EACH ROW "
               "EXECUTE PROCEDURE event_create_notify();")

    event_update = text("CREATE OR REPLACE FUNCTION event_update_notify()"
               "RETURNS trigger AS "
               "$BODY$ "
               "BEGIN "
               "PERFORM pg_notify('event_update', row_to_json(NEW)::text);"
               "RETURN NEW;"
               "END;"
               "$BODY$ "
               "LANGUAGE plpgsql VOLATILE "
               "COST 100;"
               "ALTER FUNCTION event_update_notify() "
               "OWNER TO calendar;"
               "CREATE TRIGGER event_update_trigger "
               "AFTER UPDATE "
               "ON events "
               "FOR EACH ROW "
                        "WHEN (OLD.OWNER_ID = NEW.OWNER_ID) "
               "EXECUTE PROCEDURE event_update_notify();")

    event_delete = text("CREATE OR REPLACE FUNCTION event_delete_notify()"
                        "RETURNS trigger AS "
                        "$BODY$ "
                        "BEGIN "
                        "PERFORM pg_notify('event_delete', row_to_json(OLD)::text);"
                        "RETURN OLD;"
                        "END;"
                        "$BODY$ "
                        "LANGUAGE plpgsql VOLATILE "
                        "COST 100;"
                        "ALTER FUNCTION event_delete_notify() "
                        "OWNER TO calendar;"
                        "CREATE TRIGGER event_delete_trigger "
                        "AFTER DELETE "
                        "ON events "
                        "FOR EACH ROW "
                        "EXECUTE PROCEDURE event_delete_notify();")

    event_transfer = text("CREATE OR REPLACE FUNCTION event_transfer_notify()"
                        "RETURNS trigger AS "
                        "$BODY$ "
                        "BEGIN "
                        "PERFORM pg_notify('event_transfer', row_to_json(NEW)::text);"
                        "RETURN NEW;"
                        "END;"
                        "$BODY$ "
                        "LANGUAGE plpgsql VOLATILE "
                        "COST 100;"
                        "ALTER FUNCTION event_transfer_notify() "
                        "OWNER TO calendar;"
                        "CREATE TRIGGER event_transfer_trigger "
                        "AFTER UPDATE "
                        "ON events "
                        "FOR EACH ROW "
                          "WHEN (OLD.OWNER_ID IS DISTINCT FROM NEW.OWNER_ID) "
                        "EXECUTE PROCEDURE event_transfer_notify();")


    task_create = text("CREATE OR REPLACE FUNCTION task_create_notify()"
                        "RETURNS trigger AS "
                        "$BODY$ "
                        "BEGIN "
                        "PERFORM pg_notify('task_create', row_to_json(NEW)::text);"
                        "RETURN NEW;"
                        "END;"
                        "$BODY$ "
                        "LANGUAGE plpgsql VOLATILE "
                        "COST 100;"
                        "ALTER FUNCTION task_create_notify() "
                        "OWNER TO calendar;"
                        "CREATE TRIGGER task_create_trigger "
                        "AFTER INSERT "
                        "ON tasks "
                        "FOR EACH ROW "
                        "EXECUTE PROCEDURE task_create_notify();")

    task_update = text("CREATE OR REPLACE FUNCTION task_update_notify()"
                        "RETURNS trigger AS "
                        "$BODY$ "
                        "BEGIN "
                        "PERFORM pg_notify('task_update', row_to_json(NEW)::text);"
                        "RETURN NEW;"
                        "END;"
                        "$BODY$ "
                        "LANGUAGE plpgsql VOLATILE "
                        "COST 100;"
                        "ALTER FUNCTION task_update_notify() "
                        "OWNER TO calendar;"
                        "CREATE TRIGGER task_update_trigger "
                        "AFTER UPDATE "
                        "ON tasks "
                        "FOR EACH ROW "
                        "EXECUTE PROCEDURE task_update_notify();")

    task_delete = text("CREATE OR REPLACE FUNCTION task_delete_notify()"
                        "RETURNS trigger AS "
                        "$BODY$ "
                        "BEGIN "
                        "PERFORM pg_notify('task_delete', row_to_json(OLD)::text);"
                        "RETURN OLD;"
                        "END;"
                        "$BODY$ "
                        "LANGUAGE plpgsql VOLATILE "
                        "COST 100;"
                        "ALTER FUNCTION task_delete_notify() "
                        "OWNER TO calendar;"
                        "CREATE TRIGGER task_delete_trigger "
                        "AFTER DELETE "
                        "ON tasks "
                        "FOR EACH ROW "
                        "EXECUTE PROCEDURE task_delete_notify();")

    event_user_create = text("CREATE OR REPLACE FUNCTION  event_user_create_notify()"
                       "RETURNS trigger AS "
                       "$BODY$ "
                       "BEGIN "
                       "PERFORM pg_notify('event_user_create', row_to_json(NEW)::text);"
                       "RETURN NEW;"
                       "END;"
                       "$BODY$ "
                       "LANGUAGE plpgsql VOLATILE "
                       "COST 100;"
                       "ALTER FUNCTION  event_user_create_notify() "
                       "OWNER TO calendar;"
                       "CREATE TRIGGER  event_user_create_trigger "
                       "AFTER INSERT "
                       "ON event_user "
                       "FOR EACH ROW "
                       "EXECUTE PROCEDURE  event_user_create_notify();")

    event_user_join = text("CREATE OR REPLACE FUNCTION event_user_join_notify()"
                                   "RETURNS trigger AS "
                                   "$BODY$ "
                                   "BEGIN "
                                   "PERFORM pg_notify('event_user_join', row_to_json(NEW)::text);"
                                   "RETURN NEW;"
                                   "END;"
                                   "$BODY$ "
                                   "LANGUAGE plpgsql VOLATILE "
                                   "COST 100;"
                                   "ALTER FUNCTION event_user_join_notify() "
                                   "OWNER TO calendar;"
                                   "CREATE TRIGGER event_user_join_trigger "
                                   "AFTER INSERT "
                                   "ON event_user "
                                   "FOR EACH ROW "
                           "WHEN (NEW.IS_ACCEPTED = True)"
                                   "EXECUTE PROCEDURE event_user_join_notify();")

    event_user_join_if_exist = text("CREATE TRIGGER event_user_join_if_exist_trigger "
                           "AFTER UPDATE "
                           "ON event_user "
                           "FOR EACH ROW "
                           "WHEN (NEW.IS_ACCEPTED = True AND OLD.IS_ACCEPTED IS DISTINCT FROM True) "
                           "EXECUTE PROCEDURE event_user_join_notify();")


    event_user_invite = text("CREATE OR REPLACE FUNCTION event_user_invite_notify()"
                           "RETURNS trigger AS "
                           "$BODY$ "
                           "BEGIN "
                           "PERFORM pg_notify('event_user_invite', row_to_json(NEW)::text);"
                           "RETURN NEW;"
                           "END;"
                           "$BODY$ "
                           "LANGUAGE plpgsql VOLATILE "
                           "COST 100;"
                           "ALTER FUNCTION event_user_invite_notify() "
                           "OWNER TO calendar;"
                           "CREATE TRIGGER event_user_invite_trigger "
                           "AFTER INSERT "
                           "ON event_user "
                           "FOR EACH ROW "
                           "WHEN (NEW.IS_ACCEPTED IS DISTINCT FROM True AND NEW.IS_VIEWED = False) "
                           "EXECUTE PROCEDURE event_user_invite_notify();")

    event_user_invite_if_exist = text("CREATE TRIGGER event_user_invite_if_exist_trigger "
                                    "AFTER UPDATE "
                                    "ON event_user "
                                    "FOR EACH ROW "
                                    "WHEN (NEW.IS_ACCEPTED IS DISTINCT FROM True AND NEW.IS_VIEWED = False) "
                                    "EXECUTE PROCEDURE event_user_invite_notify();")


    event_user_delete = text("CREATE OR REPLACE FUNCTION event_user_delete_notify()"
                             "RETURNS trigger AS "
                             "$BODY$ "
                             "BEGIN "
                             "PERFORM pg_notify('event_user_delete', row_to_json(OLD)::text);"
                             "RETURN NEW;"
                             "END;"
                             "$BODY$ "
                             "LANGUAGE plpgsql VOLATILE "
                             "COST 100;"
                             "ALTER FUNCTION event_user_delete_notify() "
                             "OWNER TO calendar;"
                             "CREATE TRIGGER event_user_delete_trigger "
                             "AFTER DELETE "
                             "ON event_user "
                             "FOR EACH ROW "
                             "EXECUTE PROCEDURE event_user_delete_notify();")



    event_user_rejected = text("CREATE OR REPLACE FUNCTION event_user_rejected_notify()"
                               "RETURNS trigger AS "
                               "$BODY$ "
                               "BEGIN "
                               "PERFORM pg_notify('event_user_rejected', row_to_json(NEW)::text);"
                               "RETURN NEW;"
                               "END;"
                               "$BODY$ "
                               "LANGUAGE plpgsql VOLATILE "
                               "COST 100;"
                               "ALTER FUNCTION event_user_rejected_notify() "
                               "OWNER TO calendar;"
                               "CREATE TRIGGER event_user_rejected_trigger "
                               "AFTER UPDATE "
                               "ON event_user "
                               "FOR EACH ROW "
                               "WHEN (NEW.IS_ACCEPTED = False) "
                               "EXECUTE PROCEDURE event_user_rejected_notify();")

    event_user_like = text("CREATE OR REPLACE FUNCTION event_user_like_notify()"
                               "RETURNS trigger AS "
                               "$BODY$ "
                               "BEGIN "
                               "PERFORM pg_notify('event_user_like', row_to_json(NEW)::text);"
                               "RETURN NEW;"
                               "END;"
                               "$BODY$ "
                               "LANGUAGE plpgsql VOLATILE "
                               "COST 100;"
                               "ALTER FUNCTION event_user_like_notify() "
                               "OWNER TO calendar;"
                               "CREATE TRIGGER event_user_like_trigger "
                               "AFTER UPDATE "
                               "ON event_user "
                               "FOR EACH ROW "
                               "WHEN (NEW.IS_LIKED IS DISTINCT FROM OLD.IS_LIKED AND NEW.IS_LIKED = True) "
                               "EXECUTE PROCEDURE event_user_like_notify();")

    event_user_unlike = text("CREATE OR REPLACE FUNCTION event_user_unlike_notify()"
                           "RETURNS trigger AS "
                           "$BODY$ "
                           "BEGIN "
                           "PERFORM pg_notify('event_user_unlike', row_to_json(NEW)::text);"
                           "RETURN NEW;"
                           "END;"
                           "$BODY$ "
                           "LANGUAGE plpgsql VOLATILE "
                           "COST 100;"
                           "ALTER FUNCTION event_user_unlike_notify() "
                           "OWNER TO calendar;"
                           "CREATE TRIGGER event_user_unlike_trigger "
                           "AFTER UPDATE "
                           "ON event_user "
                           "FOR EACH ROW "
                           "WHEN (NEW.IS_LIKED IS DISTINCT FROM OLD.IS_LIKED AND NEW.IS_LIKED = False) "
                           "EXECUTE PROCEDURE event_user_unlike_notify();")

    event_user_remind = text("CREATE OR REPLACE FUNCTION event_user_remind_notify()"
                           "RETURNS trigger AS "
                           "$BODY$ "
                           "BEGIN "
                           "PERFORM pg_notify('event_user_remind', row_to_json(NEW)::text);"
                           "RETURN NEW;"
                           "END;"
                           "$BODY$ "
                           "LANGUAGE plpgsql VOLATILE "
                           "COST 100;"
                           "ALTER FUNCTION event_user_remind_notify() "
                           "OWNER TO calendar;"
                           "CREATE TRIGGER event_user_remind_trigger "
                           "AFTER UPDATE "
                           "ON event_user "
                           "FOR EACH ROW "
                           "WHEN (NEW.IS_REMINDER_ON IS DISTINCT FROM OLD.IS_REMINDER_ON AND NEW.IS_REMINDER_ON = True) "
                           "EXECUTE PROCEDURE event_user_remind_notify();")

    event_user_unremind = text("CREATE OR REPLACE FUNCTION event_user_unremind_notify()"
                             "RETURNS trigger AS "
                             "$BODY$ "
                             "BEGIN "
                             "PERFORM pg_notify('event_user_unremind', row_to_json(NEW)::text);"
                             "RETURN NEW;"
                             "END;"
                             "$BODY$ "
                             "LANGUAGE plpgsql VOLATILE "
                             "COST 100;"
                             "ALTER FUNCTION event_user_unremind_notify() "
                             "OWNER TO calendar;"
                             "CREATE TRIGGER event_user_unremind_trigger "
                             "AFTER UPDATE "
                             "ON event_user "
                             "FOR EACH ROW "
                             "WHEN (NEW.IS_REMINDER_ON IS DISTINCT FROM OLD.IS_REMINDER_ON AND NEW.IS_REMINDER_ON = False) "
                             "EXECUTE PROCEDURE event_user_unremind_notify();")

    event_user_hidden = text("CREATE OR REPLACE FUNCTION event_user_hidden_notify()"
                             "RETURNS trigger AS "
                             "$BODY$ "
                             "BEGIN "
                             "PERFORM pg_notify('event_user_hidden', row_to_json(NEW)::text);"
                             "RETURN NEW;"
                             "END;"
                             "$BODY$ "
                             "LANGUAGE plpgsql VOLATILE "
                             "COST 100;"
                             "ALTER FUNCTION event_user_hidden_notify() "
                             "OWNER TO calendar;"
                             "CREATE TRIGGER event_user_hidden_trigger "
                             "AFTER UPDATE "
                             "ON event_user "
                             "FOR EACH ROW "
                             "WHEN (NEW.IS_HIDDEN IS DISTINCT FROM OLD.IS_HIDDEN AND NEW.IS_HIDDEN = True) "
                             "EXECUTE PROCEDURE event_user_hidden_notify();")

    event_user_unhidden = text("CREATE OR REPLACE FUNCTION event_user_unhidden_notify()"
                               "RETURNS trigger AS "
                               "$BODY$ "
                               "BEGIN "
                               "PERFORM pg_notify('event_user_unhidden', row_to_json(NEW)::text);"
                               "RETURN NEW;"
                               "END;"
                               "$BODY$ "
                               "LANGUAGE plpgsql VOLATILE "
                               "COST 100;"
                               "ALTER FUNCTION event_user_unhidden_notify() "
                               "OWNER TO calendar;"
                               "CREATE TRIGGER event_user_unhidden_trigger "
                               "AFTER UPDATE "
                               "ON event_user "
                               "FOR EACH ROW "
                               "WHEN (NEW.IS_HIDDEN IS DISTINCT FROM OLD.IS_HIDDEN AND NEW.IS_HIDDEN = False) "
                               "EXECUTE PROCEDURE event_user_unhidden_notify();")

    task_user_like = text("CREATE OR REPLACE FUNCTION task_user_like_notify()"
                           "RETURNS trigger AS "
                           "$BODY$ "
                           "BEGIN "
                           "PERFORM pg_notify('task_user_like', row_to_json(NEW)::text);"
                           "RETURN NEW;"
                           "END;"
                           "$BODY$ "
                           "LANGUAGE plpgsql VOLATILE "
                           "COST 100;"
                           "ALTER FUNCTION task_user_like_notify() "
                           "OWNER TO calendar;"
                           "CREATE TRIGGER task_user_like_trigger "
                           "AFTER UPDATE "
                           "ON task_user "
                           "FOR EACH ROW "
                           "WHEN (NEW.IS_LIKED IS DISTINCT FROM OLD.IS_LIKED AND NEW.IS_LIKED = True) "
                           "EXECUTE PROCEDURE task_user_like_notify();")

    task_user_unlike = text("CREATE OR REPLACE FUNCTION task_user_unlike_notify()"
                             "RETURNS trigger AS "
                             "$BODY$ "
                             "BEGIN "
                             "PERFORM pg_notify('task_user_unlike', row_to_json(NEW)::text);"
                             "RETURN NEW;"
                             "END;"
                             "$BODY$ "
                             "LANGUAGE plpgsql VOLATILE "
                             "COST 100;"
                             "ALTER FUNCTION task_user_unlike_notify() "
                             "OWNER TO calendar;"
                             "CREATE TRIGGER task_user_unlike_trigger "
                             "AFTER UPDATE "
                             "ON task_user "
                             "FOR EACH ROW "
                             "WHEN (NEW.IS_LIKED IS DISTINCT FROM OLD.IS_LIKED AND NEW.IS_LIKED = False) "
                             "EXECUTE PROCEDURE task_user_unlike_notify();")

    task_user_done = text("CREATE OR REPLACE FUNCTION task_user_done_notify()"
                             "RETURNS trigger AS "
                             "$BODY$ "
                             "BEGIN "
                             "PERFORM pg_notify('task_user_done', row_to_json(NEW)::text);"
                             "RETURN NEW;"
                             "END;"
                             "$BODY$ "
                             "LANGUAGE plpgsql VOLATILE "
                             "COST 100;"
                             "ALTER FUNCTION task_user_done_notify() "
                             "OWNER TO calendar;"
                             "CREATE TRIGGER task_user_done_trigger "
                             "AFTER UPDATE "
                             "ON task_user "
                             "FOR EACH ROW "
                             "WHEN (NEW.IS_DONE IS DISTINCT FROM OLD.IS_DONE AND NEW.IS_DONE = True) "
                             "EXECUTE PROCEDURE task_user_done_notify();")

    task_user_undone = text("CREATE OR REPLACE FUNCTION task_user_undone_notify()"
                               "RETURNS trigger AS "
                               "$BODY$ "
                               "BEGIN "
                               "PERFORM pg_notify('task_user_undone', row_to_json(NEW)::text);"
                               "RETURN NEW;"
                               "END;"
                               "$BODY$ "
                               "LANGUAGE plpgsql VOLATILE "
                               "COST 100;"
                               "ALTER FUNCTION task_user_undone_notify() "
                               "OWNER TO calendar;"
                               "CREATE TRIGGER task_user_undone_trigger "
                               "AFTER UPDATE "
                               "ON task_user "
                               "FOR EACH ROW "
                               "WHEN (NEW.IS_DONE IS DISTINCT FROM OLD.IS_DONE AND NEW.IS_DONE = False) "
                               "EXECUTE PROCEDURE task_user_undone_notify();")

    session = Session(engine)
    # session.execute(event_create)
    # session.execute(event_update)
    # session.execute(event_delete)
    # session.execute(task_create)
    # session.execute(task_update)
    # session.execute(task_delete)
    # session.execute(event_user_create)
    # session.execute(event_user_join)
    # session.execute(event_user_invite)
    # session.execute(event_user_join_if_exist)
    # session.execute(event_user_invite_if_exist)
    # session.execute(event_user_delete)
    # session.execute(event_transfer)
    # session.execute(event_user_rejected)
    # session.execute(event_user_like)
    # session.execute(event_user_unlike)
    # session.execute(event_user_remind)
    # session.execute(event_user_unremind)
    # session.execute(event_user_hidden)
    # session.execute(event_user_unhidden)
    # session.execute(task_user_like)
    # session.execute(task_user_unlike)
    session.execute(task_user_done)
    session.execute(task_user_undone)
    session.commit()


