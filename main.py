import argparse
import datetime as dt
import glob
import logging
import os
import sys
import time
import traceback

import pandas as pd
from sqlsorcery import MSSQL
from tenacity import *

from api import API
from ftp import FTP
from mailer import Mailer

LOCALDIR = "files"
SOURCEDIR = "schoolmint"

logging.basicConfig(
    handlers=[
        logging.FileHandler(filename="app.log", mode="w+"),
        logging.StreamHandler(sys.stdout),
    ],
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %I:%M:%S%p %Z",
)

# Quiet the logging from pysftp
logging.getLogger("paramiko").setLevel(logging.ERROR)


def read_logs(filename):
    """ Read the given file """
    with open(filename) as f:
        return f.read()


def read_csv_to_df(csv):
    """ Read the csv into a dataframe in preparation for database load """
    if not os.path.isfile(csv):
        raise Exception(
            f"ERROR: '{csv}' file does not exist. Most likely problem downloading from sFTP."
        )
    df = pd.read_csv(csv, sep=",", quotechar='"', doublequote=True, dtype=str, header=0)
    count = len(df.index)
    if count == 0:
        raise Exception(f"ERROR: No data was loaded from CSV file '{csv}'.")
    else:
        logging.info(f"Read {count} rows from CSV file '{csv}'.")
    return df


def backup_and_truncate_table(conn, prep_sproc):
    """ Execute the prep sproc, which truncates the primary table. """
    result = conn.exec_sproc(prep_sproc)
    count = result.fetchone()[0]
    if count == 0:
        return True
    else:
        raise Exception(f"ERROR: Table {table} was not truncated.")


def get_records_count(conn, schema, table):
    """ Count the number of records in a given table. """
    result = conn.query(f"SELECT COUNT(1) records FROM {schema}.{table};")
    count = result["records"].values[0]
    return count


def load_from_backup_table(conn, schema, table):
    """
    Load data from backup table to primary table,
    only when there was an issue loading the csv into the primary table.
    """
    sql_insert = f"INSERT INTO {schema}.{table} SELECT * FROM {schema}.{table}_backup;"
    result = conn.query(sql_insert)
    count = get_records_count(conn, schema, table)
    raise Exception(
        f"ERROR: No rows loaded into {table}. {count} records reverted from backup table."
    )


def check_table_load(conn, schema, table):
    """ Ensure data was loaded successfully into the primary table. """
    count = get_records_count(conn, schema, table)
    if count == 0:
        load_from_backup_table(conn, schema, table)
    else:
        backup_count = get_records_count(conn, schema, f"{table}_backup")
        logging.info(f"Loaded {backup_count} rows into backup table '{table}_backup'.")
        logging.info(f"Loaded {count} rows into table '{table}''.")


def delete_data_files(directory):
    """ Delete data files (not everything) from the given directory """
    for file in os.listdir(directory):
        if "Data" in file:
            os.remove(os.path.join(directory, file))


def get_latest_file(filename):
    """ Get the file that matches the given name.
    Reverse sort by modification date in case there are multiple. """
    all_files = os.listdir(LOCALDIR)
    matched_files = [file for file in all_files if filename in file]
    files = sorted(
        matched_files,
        key=lambda file: os.path.getmtime(f"{LOCALDIR}/{file}"),
        reverse=True,
    )
    if files:
        file = files[0]
        logging.info(f"Downloaded '{file}'.")
        return file
    else:
        raise Exception(f"Error: '{filename}' was not downloaded.")


@retry(wait=wait_fixed(30), stop=stop_after_attempt(60))
def download_from_ftp(ftp):
    """
    Download data files from FTP.
    
    It can take some time for SchoolMint to upload the reports after the API request,
    so we use Tenacity retry to wait up to 30 min.
    """
    ftp.download_dir(SOURCEDIR, LOCALDIR)
    app_file = get_latest_file("Automated Application Data Raw")
    app_index_file = get_latest_file("Automated Application Data Index")
    return app_file, app_index_file


def process_application_data(conn, schema, file):
    """ Take application data from csv and insert into table """
    df = read_csv_to_df(f"{LOCALDIR}/{file}")
    if backup_and_truncate_table(conn, os.getenv("SPROC_RAW_PREP")):
        table = os.getenv("DB_RAW_TABLE")
        conn.insert_into(table, df)
        check_table_load(conn, schema, table)
        conn.exec_sproc(os.getenv("SPROC_RAW_POST"))


def process_application_data_index(conn, schema, file):
    """ Take application data index from csv and insert into table """
    df = read_csv_to_df(f"{LOCALDIR}/{file}")
    if backup_and_truncate_table(conn, os.getenv("SPROC_RAW_INDEX_PREP")):
        table = os.getenv("DB_RAW_INDEX_TABLE")
        conn.insert_into(table, df)
        check_table_load(conn, schema, table)
        conn.exec_sproc(os.getenv("SPROC_RAW_INDEX_POST"))


def process_change_tracking(conn):
    """ Execute sproc to generate change history """
    result = conn.exec_sproc(os.getenv("SPROC_CHANGE_TRACK"))
    count = result.fetchone()[0]
    logging.info(f"Loaded {count} rows into Change History table.")


def process_fact_daily_status(conn):
    """ Execute sproc to generate fact daily status table """
    result = conn.exec_sproc(os.getenv("SPROC_FACT_DAILY"))
    count = result.fetchone()[0]
    logging.info(f"Loaded {count} rows into Fact Daily Status table.")


def main():
    try:
        schema = os.getenv("DB_SCHEMA")
        conn = MSSQL()
        mailer = Mailer()
        ftp = FTP()

        ftp.archive_remote_files(SOURCEDIR)
        API().request_reports()
        if eval(os.getenv("DELETE_LOCAL_FILES", "True")):
            delete_data_files(LOCALDIR)
        app_file, app_index_file = download_from_ftp(ftp)

        process_application_data(conn, schema, app_file)
        process_application_data_index(conn, schema, app_index_file)

        process_change_tracking(conn)
        process_fact_daily_status(conn)

        success_message = read_logs("app.log")
        mailer.notify(results=success_message)
    except Exception as e:
        logging.exception(e)
        stack_trace = traceback.format_exc()
        mailer.notify(success=False, error_message=stack_trace)


if __name__ == "__main__":
    main()
