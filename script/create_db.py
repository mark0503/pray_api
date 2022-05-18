from sqlalchemy import create_engine
from sqlalchemy.orm import Session

DATABASE_URL = f"postgresql://postgres:postgres@127.0.0.1:5432/praydb"

def main():
    engine = create_engine(DATABASE_URL)
    session = Session(bind=engine.connect())
    print(session)

    session.execute("""create table users (
    id SERIAL primary key,
    email varchar(256),
    username varchar(256),
    password varchar(256),
    first_name varchar(256),
    last_name varchar(256),
    created_at varchar(256)
    );""")

    session.execute("""create table auth_token (
    id SERIAL primary key,
    token varchar(256),
    user_id integer  references users,
    created_at varchar(256)
    );""")

    session.execute("""create table pray (
    id SERIAL primary key,
    user_id integer  references users,
    live_names text[],
    rip_names text[],
    type_pray varchar(256),
    created_at varchar(256),
    status_payment varchar(256) DEFAULT 'Не оплачено'
    );""")

    session.execute("""create table payments (
    id SERIAL primary key,
    ex_id varchar(256),
    url_pay varchar(256),
    user_id integer  references users,
    pray integer  references pray,
    status_payment varchar(256) DEFAULT 'Не оплачено'
    );""")

    session.commit()
    session.close()


if __name__ == '__main__':
    main()
