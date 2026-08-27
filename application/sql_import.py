import re


def mysql_dump_to_sqlite(script):
    """Convert the common phpMyAdmin MySQL dump syntax to SQLite SQL."""
    script = re.sub(r"/\*!.*?\*/", "", script, flags=re.DOTALL)
    script = re.sub(r"^\s*SET\s+.*?;", "", script, flags=re.IGNORECASE | re.MULTILINE)
    script = re.sub(
        r"^\s*CREATE\s+DATABASE\b.*?;",
        "",
        script,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    script = re.sub(
        r"^\s*USE\s+.*?;",
        "",
        script,
        flags=re.IGNORECASE | re.MULTILINE,
    )
    script = script.replace("`", '"')
    script = re.sub(r"\s+AUTO_INCREMENT\b", "", script, flags=re.IGNORECASE)
    script = re.sub(r"\s+UNSIGNED\b", "", script, flags=re.IGNORECASE)
    script = re.sub(
        r"\)\s+ENGINE\s*=\s*\w+"
        r"(?:\s+DEFAULT\s+CHARSET\s*=\s*[^\s;]+)?"
        r"(?:\s+AUTO_INCREMENT\s*=\s*\d+)?\s*;",
        ");",
        script,
        flags=re.IGNORECASE,
    )
    return script
