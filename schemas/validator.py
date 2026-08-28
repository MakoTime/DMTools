import json
import os
from jsonschema import RefResolver, Draft7Validator

class SchemaValidator:
    def __init__(self, schema_dir):
        self.schema_dir = schema_dir
        # Ensure we are pointing at the root 'schemas/' folder
        self.base_uri = f"file:///{os.path.abspath(schema_dir).replace(os.sep, '/')}/"

    def validate(self, data, schema_filename):
        schema_path = os.path.join(self.schema_dir, schema_filename)
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        # The base URI must point to the schemas root directory,
        # so that relative paths like "../values/..." work regardless of where
        # the entity schema is located.
        base_uri = f"file:///{os.path.abspath(self.schema_dir).replace(os.sep, '/')}/"

        # We need a store to cache all schemas so they can be resolved by their $id
        # or path.
        store = {}
        for root, _, files in os.walk(self.schema_dir):
            for file in files:
                if file.endswith('.json'):
                    path = os.path.join(root, file)
                    with open(path, 'r') as f:
                        try:
                            s = json.load(f)
                            # Create an absolute reference path for this file
                            rel_path = os.path.relpath(path, self.schema_dir).replace(os.sep, '/')
                            store[base_uri + rel_path] = s

                            # Also register by ID if present
                            if "$id" in s:
                                store[base_uri + s["$id"]] = s
                        except json.JSONDecodeError:
                            continue

        resolver = RefResolver(base_uri=base_uri, referrer=schema, store=store)
        
        validator = Draft7Validator(schema, resolver=resolver)
        errors = list(validator.iter_errors(data))
        return errors

def validate_entity(entity_data, schema_path):
    validator = SchemaValidator("schemas")
    return validator.validate(entity_data, schema_path)

