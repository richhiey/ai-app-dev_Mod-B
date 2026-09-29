"""INTENTIONALLY UNSAFE synthetic fixture: sends all runtime configuration."""
def build_prompt(question, context, runtime):
    return [{'role':'user','content':f'{question}\nContext: {context}\nRuntime: {runtime}'}]
